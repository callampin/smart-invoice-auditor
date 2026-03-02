import base64
import json
from io import BytesIO
from pathlib import Path

from openai import OpenAI
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


class OpenAIProvider(BaseAIProvider):
    def __init__(self, config: Config):
        self.config = config
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)

    def get_provider_name(self) -> str:
        return "openai"

    def _pdf_to_images_base64(self, pdf_path: Path) -> list[dict]:
        images = convert_from_path(str(pdf_path), dpi=150, first_page=1, last_page=2)
        content = []

        for img in images:
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            img_bytes = buffer.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_b64}"
                }
            })

        return content

    def extract_invoice_data(self, pdf_path: Path) -> InvoiceData:
        images_content = self._pdf_to_images_base64(pdf_path)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        *images_content,
                        {"type": "text", "text": "Extrae los datos de esta factura."}
                    ]
                }
            ],
            response_format=InvoiceData,
            temperature=0,
        )

        return response.choices[0].message.parsed
