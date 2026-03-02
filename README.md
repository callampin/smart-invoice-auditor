# Smart Invoice Auditor

<p align="center">
  <a href="./README-ESP.md">
    <img src="https://img.shields.io/badge/Read%20in-Spanish-blue?style=for-the-badge" alt="Read in Spanish" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/License-MIT-olive?style=for-the-badge" alt="License MIT" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker" alt="Docker Ready" />
</p>

> "AI-powered B2B invoice data extraction with automatic budget validation and Slack routing."

---

## The Problem

Manual invoice processing is a time-consuming bottleneck for businesses. Finance teams waste hours every week:

- Opening emails and downloading PDF attachments
- Manually typing invoice data into spreadsheets
- Cross-referencing against approved budgets
- Routing approved vs. exceeded invoices to different channels

**Smart Invoice Auditor eliminates this entire workflow.** This autonomous worker monitors your inbox, extracts structured data from PDF invoices using multi-provider AI, validates against your Google Sheets budget, and routes the results — automatically.

### How It Works (4 Steps)

1. **Monitor IMAP** — Polls `UNSEEN` emails with "Factura" or "Invoice" in the subject line
2. **AI Extraction** — Sends PDF to Gemini, OpenAI, or MiniMax; receives structured JSON (RUT, amount, date, products)
3. **Budget Validation** — Compares extracted amount against Google Sheets budget for the current month
4. **Routing** — If exceeded: Slack alert (🚨). If approved: register in Sheets + notify Slack (✅)

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Email     │     │     AI      │     │   Budget    │     │   Output    │
│   (IMAP)    │────▶│  Provider   │────▶│   Check     │────▶│  Routing    │
│             │     │ (Agnostic)  │     │   Logic     │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                                        │
                           │                                        ▼
                    ┌──────┴──────┐                         ┌─────────────┐
                    │  Gemini     │                         │   Slack     │
                    │  OpenAI     │                         │   (Alert)   │
                    │  MiniMax    │                         └─────────────┘
                    └─────────────┘                                  │
                                                                     ▼
                                                             ┌─────────────┐
                                                             │   Sheets    │
                                                             │ (Approved)  │
                                                             └─────────────┘
```

### Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Core runtime with async-ready syntax |
| **IMAP (imaplib)** | Native email polling and attachment download |
| **Pydantic v2** | Strict structured output validation |
| **Gemini / OpenAI / MiniMax** | Multi-LLM agnostic design via Strategy Pattern |
| **Google Sheets API** | Budget lookup and invoice registration |
| **Docker** | VPS-ready container orchestration |

### Key Features

- **Multi-LLM Agnostic** — Switch providers via `AI_PROVIDER` env var; swap models without code changes
- **Strict Idempotency** — Marks email as `SEEN` only after full success; retries automatically on failure
- **Structured Outputs** — All AI responses validated through Pydantic models (RUT Chilean format, cleaned integers)
- **Docker-Ready** — Single `Dockerfile` with `poppler-utils` for PDF-to-image conversion

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/smart-invoice-auditor.git
cd smart-invoice-auditor

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Add your credentials
# - Google Service Account JSON in GOOGLE_SERVICE_ACCOUNT_JSON
# - API keys for your chosen AI provider
# - IMAP credentials for your email host
# - Slack webhook URL
```

**Note:** You need a `credentials.json` file (or inline JSON in `GOOGLE_SERVICE_ACCOUNT_JSON`) for Google Sheets API access.

---

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `AI_PROVIDER` | AI backend: `gemini`, `openai`, or `minimax` | Yes |
| `IMAP_HOST` | Email server (e.g., `imap.gmail.com`) | Yes |
| `IMAP_USER` | Email address | Yes |
| `IMAP_PASSWORD` | App password or IMAP password | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | If `AI_PROVIDER=gemini` |
| `OPENAI_API_KEY` | OpenAI API key | If `AI_PROVIDER=openai` |
| `MINIMAX_API_KEY` | MiniMax API key | If `AI_PROVIDER=minimax` |
| `SLACK_WEBHOOK_URL` | Incoming webhook for alerts | Yes |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account credentials (JSON string) | Yes |
| `GOOGLE_SHEET_NAME` | Spreadsheet name with "Config" and "Aprobadas" sheets | Yes |

---

## Metrics & Success Criteria

### Validation Pipeline

| Stage | Status | Description |
|-------|--------|-------------|
| **Raw Email** | 📥 Incoming | Unseen email with PDF attachment |
| **AI Extracted** | 🤖 Processed | JSON with RUT, amount, date, products |
| **Budget Checked** | ✅ Approved / 🚨 Exceeded | Comparison against Sheets budget |
| **Alerted** | 📤 Routed | Slack notification sent |
| **Registered** | 📝 Stored | Row added to "Aprobadas" sheet |

### Sample Output

```json
{
  "rut_emisor": "12.345.678-9",
  "monto_total": 150990,
  "fecha_vencimiento": "2026-03-15",
  "lista_productos": ["Servicios Cloud", "Licencia Enterprise"]
}
```

**Decision Logic:**

```
IF monto_total > presupuesto_disponible:
    → Send Slack Alert (🚨)
    → DO NOT mark email as SEEN
ELSE:
    → Register in Google Sheets ("Aprobadas")
    → Send Slack Confirmation (✅)
    → Mark email as SEEN
```

---

## Docker Deployment

### Dockerfile (includes poppler-utils)

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    poppler-utils \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.main"]
```

### Build & Run

```bash
# Build the image
docker build -t smart-invoice-auditor .

# Run with environment file
docker run --env-file .env -v ./credentials.json:/app/credentials.json:ro smart-invoice-auditor
```

Or use `docker-compose`:

```bash
docker-compose up --build -d
```

---

## Project Structure

```
smart-invoice-auditor/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── main.py                 # Orchestrator with 15-min scheduler
│   ├── config.py               # Environment variable loader
│   ├── models/
│   │   ├── __init__.py
│   │   └── invoice.py          # Pydantic: InvoiceData, BudgetCheck
│   ├── ai_providers/
│   │   ├── __init__.py         # Factory: get_ai_provider()
│   │   ├── base.py             # BaseAIProvider (ABC)
│   │   ├── gemini.py           # GeminiProvider (File API)
│   │   ├── openai.py           # OpenAIProvider (Vision)
│   │   └── minimax.py          # MiniMaxProvider (Vision)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py    # IMAP: search, download, mark SEEN
│   │   ├── sheets_service.py   # gspread: budget lookup, row insert
│   │   └── slack_service.py    # Webhooks: Block Kit alerts
│   └── utils/
│       └── logger.py
└── tests/
    ├── __init__.py
    └── test_ai_providers.py
```

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_ai_providers.py -v
```

---

## License & Disclaimer

**MIT License** — See `LICENSE` file for details.

> **Disclaimer:** This project is for educational and portfolio purposes only. It processes sensitive financial data — ensure proper security measures (encrypted credentials, access controls) before production use. The author is not responsible for any data loss or unauthorized access.
