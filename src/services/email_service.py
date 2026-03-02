import email
import imaplib
import logging
import re
from dataclasses import dataclass
from email.message import Message
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

from src.config import Config

logger = logging.getLogger(__name__)


@dataclass
class EmailAttachment:
    filename: str
    content: bytes
    message_id: str


class EmailService:
    def __init__(self, config: Config):
        self.config = config
        self.temp_dir = config.TEMP_DIR

    def _connect(self) -> imaplib.IMAP4_SSL:
        mail = imaplib.IMAP4_SSL(host=self.config.IMAP_HOST, port=self.config.IMAP_PORT)
        mail.login(self.config.IMAP_USER, self.config.IMAP_PASSWORD)
        return mail

    def search_unseen_invoices(self) -> list[EmailAttachment]:
        attachments = []
        mail = self._connect()

        try:
            mail.select("INBOX")
            status, messages = mail.search(
                None,
                f'(UNSEEN SUBJECT "{self.config.EMAIL_SUBJECT_FILTER}" OR SUBJECT "Invoice")'
            )

            if status != "OK":
                logger.warning("No se pudieron buscar correos")
                return []

            email_ids = messages[0].split()
            logger.info(f"Correos no leídos encontrados: {len(email_ids)}")

            for eid in email_ids:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                message_id = msg.get("Message-ID", str(eid))

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "application/pdf":
                            filename = part.get_filename()
                            if filename:
                                filename = unquote(filename)
                                content = part.get_payload(decode=True)
                                if content:
                                    attachments.append(EmailAttachment(
                                        filename=filename,
                                        content=content,
                                        message_id=message_id
                                    ))
                                    logger.info(f"PDF adjunto encontrado: {filename}")
                else:
                    if msg.get_content_type() == "application/pdf":
                        filename = msg.get_filename()
                        if filename:
                            filename = unquote(filename)
                            content = msg.get_payload(decode=True)
                            if content:
                                attachments.append(EmailAttachment(
                                    filename=filename,
                                    content=content,
                                    message_id=message_id
                                ))

        finally:
            mail.logout()

        return attachments

    def download_attachments(self, attachments: list[EmailAttachment]) -> list[tuple[EmailAttachment, Path]]:
        downloaded = []
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        for att in attachments:
            safe_name = re.sub(r"[^\w\-.]", "_", att.filename)
            filepath = self.temp_dir / safe_name
            filepath.write_bytes(att.content)
            downloaded.append((att, filepath))
            logger.info(f"Descargado: {filepath}")

        return downloaded

    def mark_as_seen(self, message_id: str) -> bool:
        mail = self._connect()
        try:
            mail.select("INBOX")
            status, messages = mail.search(None, f'HEADER Message-ID "{message_id}"')

            if status != "OK" or not messages[0]:
                logger.warning(f"No se encontró correo con Message-ID: {message_id}")
                return False

            email_id = messages[0].split()[0]
            mail.store(email_id, "+FLAGS", "\\Seen")
            logger.info(f"Correo marcado como SEEN: {message_id}")
            return True

        finally:
            mail.logout()

    def cleanup_temp_files(self, filepath: Path) -> None:
        if filepath.exists():
            filepath.unlink()
            logger.info(f"Archivo temporal eliminado: {filepath}")
