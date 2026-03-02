import logging
from datetime import date
from typing import Optional

import requests

from src.config import Config

logger = logging.getLogger(__name__)


class SlackService:
    def __init__(self, config: Config):
        self.config = config
        self.webhook_url = config.SLACK_WEBHOOK_URL

    def enviar_alerta_presupuesto_excedido(
        self,
        rut_emisor: str,
        monto_total: int,
        presupuesto: int,
        fecha_vencimiento: date,
        productos: list[str]
    ) -> bool:
        excedido = monto_total - presupuesto

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Alerta: Presupuesto Excedido",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*RUT Emisor:*\n{rut_emisor}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Monto Factura:*\n${monto_total:,}"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Presupuesto:*\n${presupuesto:,}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Excedente:*\n${excedido:,}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Fecha Vencimiento:*\n{fecha_vencimiento}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Productos:*\n{', '.join(productos[:5])}{'...' if len(productos) > 5 else ''}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📩 Canal: {self.config.SLACK_CHANNEL}"
                    }
                ]
            }
        ]

        return self._send(blocks)

    def enviar_notificacion_aprobacion(
        self,
        rut_emisor: str,
        monto_total: int,
        fecha_vencimiento: date
    ) -> bool:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Factura Aprobada",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*RUT Emisor:*\n{rut_emisor}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Monto:*\n${monto_total:,}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Fecha Vencimiento:*\n{fecha_vencimiento}"
                }
            }
        ]

        return self._send(blocks)

    def _send(self, blocks: list[dict]) -> bool:
        try:
            response = requests.post(
                self.webhook_url,
                json={"blocks": blocks},
                timeout=30
            )
            response.raise_for_status()
            logger.info("Mensaje enviado a Slack exitosamente")
            return True
        except requests.RequestException as e:
            logger.error(f"Error al enviar a Slack: {e}")
            return False
