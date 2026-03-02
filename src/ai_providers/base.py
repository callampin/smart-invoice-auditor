from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.models.invoice import InvoiceData


class BaseAIProvider(ABC):
    """Interfaz abstracta para proveedores de IA."""

    @abstractmethod
    def extract_invoice_data(self, pdf_path: Path) -> InvoiceData:
        """
        Extrae datos estructurados de una factura PDF.

        Args:
            pdf_path: Ruta al archivo PDF de la factura.

        Returns:
            InvoiceData con rut_emisor, monto_total, fecha_vencimiento, lista_productos.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Retorna el nombre del proveedor para logs."""
        pass
