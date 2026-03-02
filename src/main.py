import logging
import time
from datetime import datetime
from pathlib import Path

from src.ai_providers import get_ai_provider
from src.config import Config
from src.models.invoice import InvoiceData
from src.services.email_service import EmailService
from src.services.sheets_service import SheetsService
from src.services.slack_service import SlackService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def job():
    logger.info("=== Iniciando ciclo de procesamiento ===")
    start_time = time.time()

    try:
        config = Config()
        email_service = EmailService(config)
        sheets_service = SheetsService(config)
        slack_service = SlackService(config)
        ai_provider = get_ai_provider(config)

        logger.info(f"Proveedor de IA: {ai_provider.get_provider_name()}")

        attachments = email_service.search_unseen_invoices()
        logger.info(f"Correos encontrados: {len(attachments)}")

        if not attachments:
            logger.info("No hay facturas nuevas. Ciclo terminado.")
            return

        downloaded = email_service.download_attachments(attachments)
        logger.info(f"PDFs descargados: {len(downloaded)}")

        current_month = datetime.now().strftime("%m")
        current_year = datetime.now().year

        presupuesto = sheets_service.get_presupuesto(current_month, current_year)
        logger.info(f"Presupuesto disponible: ${presupuesto.disponible:,}")

        for att, pdf_path in downloaded:
            try:
                logger.info(f"Procesando: {att.filename} (ID: {att.message_id})")

                invoice_data: InvoiceData = ai_provider.extract_invoice_data(pdf_path)
                logger.info(f"RUT: {invoice_data.rut_emisor}, Monto: {invoice_data.monto_total}")

                excede = invoice_data.monto_total > presupuesto.disponible

                if excede:
                    logger.warning(f"Presupuesto excedido: {invoice_data.monto_total} > {presupuesto.disponible}")
                    slack_service.enviar_alerta_presupuesto_excedido(
                        rut_emisor=invoice_data.rut_emisor,
                        monto_total=invoice_data.monto_total,
                        presupuesto=presupuesto.disponible,
                        fecha_vencimiento=invoice_data.fecha_vencimiento,
                        productos=invoice_data.lista_productos
                    )
                    logger.info(f"Alerta enviada a Slack. Correo NO marcado como seen.")
                else:
                    sheets_service.registrar_factura_aprobada(
                        rut_emisor=invoice_data.rut_emisor,
                        monto_total=invoice_data.monto_total,
                        fecha_vencimiento=invoice_data.fecha_vencimiento,
                        productos=invoice_data.lista_productos
                    )
                    slack_service.enviar_notificacion_aprobacion(
                        rut_emisor=invoice_data.rut_emisor,
                        monto_total=invoice_data.monto_total,
                        fecha_vencimiento=invoice_data.fecha_vencimiento
                    )

                    email_service.mark_as_seen(att.message_id)
                    logger.info(f"Factura aprobada y registrada. Correo marcado como SEEN.")

            except Exception as e:
                logger.error(f"Error procesando {att.filename}: {e}")
                logger.info("El correo permanece como UNSEEN para reintento en próximo ciclo.")
                continue

            finally:
                email_service.cleanup_temp_files(pdf_path)

    except Exception as e:
        logger.error(f"Error crítico en el ciclo: {e}")

    elapsed = time.time() - start_time
    logger.info(f"=== Ciclo completado en {elapsed:.2f}s ===")


def main():
    logger.info("Smart Invoice Auditor iniciado")
    logger.info("Ejecutando job inicial...")
    job()

    while True:
        time.sleep(900)
        logger.info("Ejecutando job programado (cada 15 min)...")
        job()


if __name__ == "__main__":
    main()
