import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from src.config import Config

logger = logging.getLogger(__name__)


@dataclass
class BudgetInfo:
    disponible: int
    mes: str
    año: int


class SheetsService:
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    def __init__(self, config: Config):
        self.config = config
        self.client = self._authenticate()

    def _authenticate(self) -> gspread.GSpreads:
        import json
        service_account_info = json.loads(self.config.GOOGLE_SERVICE_ACCOUNT_JSON)
        
        credentials = Credentials.from_service_account_info(
            service_account_info,
            scopes=self.SCOPES
        )
        return gspread.authorize(credentials)

    def get_presupuesto(self, mes: str, año: int) -> BudgetInfo:
        try:
            sheet = self.client.open(self.config.GOOGLE_SHEET_NAME)
            config_ws = sheet.worksheet("Config")

            cell = config_ws.find(f"{mes}-{año}")
            if cell:
                presupuesto = int(config_ws.cell(cell.row, cell.col + 1).value)
                return BudgetInfo(disponible=presupuesto, mes=mes, año=año)

            logger.warning(f"No se encontró presupuesto para {mes}-{año}, usando 0")
            return BudgetInfo(disponible=0, mes=mes, año=año)

        except gspread.exceptions.SpreadsheetNotFound:
            raise RuntimeError(f"Spreadsheet no encontrado: {self.config.GOOGLE_SHEET_NAME}")
        except Exception as e:
            raise RuntimeError(f"Error al leer presupuesto: {e}")

    def registrar_factura_aprobada(
        self,
        rut_emisor: str,
        monto_total: int,
        fecha_vencimiento: date,
        productos: list[str]
    ) -> bool:
        try:
            sheet = self.client.open(self.config.GOOGLE_SHEET_NAME)
            aprobadas_ws = sheet.worksheet("Aprobadas")

            productos_str = ", ".join(productos)
            nueva_fila = [
                rut_emisor,
                monto_total,
                fecha_vencimiento.isoformat(),
                productos_str,
                "Listo para pago"
            ]

            aprobadas_ws.append_row(nueva_fila)
            logger.info(f"Factura {rut_emisor} registrada en hoja Aprobadas")
            return True

        except gspread.exceptions.WorksheetNotFound:
            raise RuntimeError("Hoja 'Aprobadas' no encontrada")
        except Exception as e:
            raise RuntimeError(f"Error al registrar factura: {e}")
