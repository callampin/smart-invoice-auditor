import re
from datetime import date
from typing import List
from pydantic import BaseModel, field_validator


class InvoiceData(BaseModel):
    rut_emisor: str
    monto_total: int
    fecha_vencimiento: date
    lista_productos: List[str]

    @field_validator("rut_emisor")
    @classmethod
    def validate_rut(cls, v: str) -> str:
        cleaned = re.sub(r"[^0-9kK.-]", "", v).upper()
        if not re.match(r"^\d{1,2}\.\d{3}\.\d{3}-[0-9K]$", cleaned):
            raise ValueError("RUT chileno inválido. Formato esperado: XX.XXX.XXX-X")
        return cleaned

    @field_validator("monto_total", mode="before")
    @classmethod
    def clean_monto(cls, v) -> int:
        if isinstance(v, str):
            return int(re.sub(r"[^0-9]", "", v))
        return int(v)


class BudgetCheck(BaseModel):
    rut_emisor: str
    monto_total: int
    presupuesto_disponible: int
    excede_presupuesto: bool
    productos: List[str]
    fecha_vencimiento: date
