import json
from pathlib import Path

import google.genai as genai
from google.genai import types

from src.ai_providers.base import BaseAIProvider
from src.config import Config
from src.models.invoice import InvoiceData

SYSTEM_PROMPT = """Eres un asistente especializado en extraer datos de facturas chilenas.

INSTRUCCIONES ESTRICTAS:
1. Extrae los datos de la factura adjunta.
2. El identificador del emisor es un RUT chileno (formato XX.XXX.XXX-X, ejemplo: 12.345.678-9).
3. El monto total debe ser un número ENTERO LIMPIO sin puntos, comas ni símbolos de moneda ($). Ejemplo: si el monto es "$150.990", debes extraer "150990".
4. La fecha de vencimiento debe estar en formato YYYY-MM-DD.
5. Lista todos los productos/servicios de la factura como strings.
6. Si no puedes extraer algún campo,返回一个 error claro."""


class GeminiProvider(BaseAIProvider):
    def __init__(self, config: Config):
        self.config = config
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.client = genai.Client()

    def get_provider_name(self) -> str:
        return "gemini"

    def extract_invoice_data(self, pdf_path: Path) -> InvoiceData:
        uploaded_file = self.client.files.upload(file=pdf_path)

        while uploaded_file.state.name == "PROCESSING":
            uploaded_file = self.client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name != "ACTIVE":
            raise RuntimeError(f"File {pdf_path.name} no está activo: {uploaded_file.state.name}")

        schema = InvoiceData.model_json_schema()

        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_uri(
                            file_uri=uploaded_file.uri,
                            mime_type=uploaded_file.mime_type
                        ),
                        types.Part(text=SYSTEM_PROMPT),
                    ],
                ),
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        data = json.loads(raw_text)
        return InvoiceData(**data)
