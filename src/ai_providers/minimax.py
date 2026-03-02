import base64
import json
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests
from pdf2image import convert_from_path

from src.ai_providers.base import BaseAIProvider
from src.config import Config
from src.models.invoice import InvoiceData

SYSTEM_PROMPT = """Eres un asistente especializado en extraer datos de facturas chilenas.

INSTRUCCIONES ESTRICTAS:
1. Extrae los datos de la factura en la imagen adjunta.
2. El identificador del emisor es un RUT chileno (formato XX.XXX.XXX-X, ejemplo: 12.345.678-9).
3. El monto total debe ser un número ENTERO LIMPIO sin puntos, comas ni símbolos de moneda ($). Ejemplo: si el monto es "$150.990", debes extraer "150990".
4. La fecha de vencimiento debe estar en formato YYYY-MM-DD.
5. Lista todos los productos/servicios de la factura como strings.
6. Si no puedes extraer algún campo,返回一个 error claro."""


class MiniMaxProvider(BaseAIProvider):
    BASE_URL = "https://api.minimax.chat/v1"

    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.MINIMAX_API_KEY
        self.group_id = config.MINIMAX_GROUP_ID

    def get_provider_name(self) -> str:
        return "minimax"

    def _pdf_to_images_base64(self, pdf_path: Path) -> list[str]:
        images = convert_from_path(str(pdf_path), dpi=150, first_page=1, last_page=2)
        b64_images = []

        for img in images:
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            img_bytes = buffer.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            b64_images.append(img_b64)

        return b64_images

    def _make_request(self, messages: list[dict]) -> dict:
        url = f"{self.BASE_URL}/text/chatcompletion_v2"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "MiniMax-Text-01",
            "messages": messages,
            "temperature": 0.0
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def extract_invoice_data(self, pdf_path: Path) -> InvoiceData:
        b64_images = self._pdf_to_images_base64(pdf_path)

        user_content = [
            {"type": "text", "text": SYSTEM_PROMPT + "\n\nExtrae los datos de esta factura y responde en formato JSON con los campos: rut_emisor, monto_total (int), fecha_vencimiento (YYYY-MM-DD), lista_productos (array de strings)."}
        ]

        for img_b64 in b64_images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}"
                }
            })

        messages = [
            {"role": "system", "content": "Eres un asistente que responde siempre en JSON válido."},
            {"role": "user", "content": user_content}
        ]

        result = self._make_request(messages)

        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = content[0].get("text", "")

        try:
            data = json.loads(content)
            return InvoiceData(**data)
        except json.JSONDecodeError:
            raise ValueError(f"MiniMax no devolvió JSON válido: {content[:200]}")
