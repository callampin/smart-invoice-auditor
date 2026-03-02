import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    IMAP_HOST = os.getenv("IMAP_HOST")
    IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
    IMAP_USER = os.getenv("IMAP_USER")
    IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
    EMAIL_SUBJECT_FILTER = os.getenv("EMAIL_SUBJECT_FILTER", "Factura")

    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
    MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")

    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Presupuesto Facturas")

    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#facturas")

    TEMP_DIR = Path("/tmp/smart-invoice-auditor")
    TEMP_DIR.mkdir(exist_ok=True)
