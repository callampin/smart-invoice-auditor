# Smart Invoice Auditor

<p align="center">
  <a href="./README.md">
    <img src="https://img.shields.io/badge/Read%20in-English-blue?style=for-the-badge" alt="Read in English" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/License-MIT-olive?style=for-the-badge" alt="License MIT" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker" alt="Docker Ready" />
</p>

> "Extracción de datos de facturas B2B con IA y validación automática de presupuestos con enrutamiento a Slack."

---

## El Problema

El procesamiento manual de facturas es un cuello de botella que consume mucho tiempo en las empresas. Los equipos de finanzas pierden horas cada semana:

- Abriendo correos y descargando archivos PDF adjuntos
- Digitando manualmente los datos de las facturas en hojas de cálculo
- Comparando contra los presupuestos aprobados
- Enviando las facturas aprobadas o excedidas a diferentes canales

**Smart Invoice Auditor elimina este flujo de trabajo completo.** Este worker autónomo monitorea tu bandeja de entrada, extrae datos estructurados de facturas PDF usando IA multi-proveedor, valida contra tu presupuesto en Google Sheets y enruta los resultados — automáticamente.

### Cómo Funciona (4 Pasos)

1. **Monitorear IMAP** — Consulta correos `UNSEEN` con "Factura" o "Invoice" en el asunto
2. **Extracción con IA** — Envía el PDF a Gemini, OpenAI o MiniMax; recibe JSON estructurado (RUT, monto, fecha, productos)
3. **Validación de Presupuesto** — Compara el monto extraído contra el presupuesto de Google Sheets del mes actual
4. **Enrutamiento** — Si excede: alerta de Slack (🚨). Si aprueba: registrar en Sheets + notificar Slack (✅)

---

## Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Email     │     │     IA      │     │  Presupuesto│     │   Salida    │
│   (IMAP)    │────▶│  Proveedor  │────▶│   Validación│────▶│ Enrutamiento│
│             │     │ (Agnóstico) │     │   Lógica    │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                                        │
                           │                                        ▼
                    ┌──────┴──────┐                         ┌─────────────┐
                    │  Gemini     │                         │   Slack     │
                    │  OpenAI     │                         │  (Alerta)   │
                    │  MiniMax    │                         └─────────────┘
                    └─────────────┘                                  │
                                                                     ▼
                                                             ┌─────────────┐
                                                             │   Sheets    │
                                                             │ (Aprobadas) │
                                                             └─────────────┘
```

### Stack Tecnológico

| Tecnología | Propósito |
|------------|-----------|
| **Python 3.11+** | Runtime principal con sintaxis lista para async |
| **IMAP (imaplib)** | Consulta nativa de correos y descarga de adjuntos |
| **Pydantic v2** | Validación estricta de salida estructurada |
| **Gemini / OpenAI / MiniMax** | Diseño agnóstico multi-LLM usando Patrón Estrategia |
| **Google Sheets API** | Consulta de presupuesto y registro de facturas |
| **Docker** | Orquestación de contenedores lista para VPS |

### Características Clave

- **Agnóstico Multi-LLM** — Cambia proveedores vía variable de entorno `AI_PROVIDER`; cambia modelos sin modificar código
- **Idempotencia Estricta** — Marca el correo como `SEEN` solo después del éxito completo; reintenta automáticamente en caso de fallo
- **Salidas Estructuradas** — Todas las respuestas de IA validadas a través de modelos Pydantic (formato RUT chileno, enteros limpiados)
- **Listo para Docker** — `Dockerfile` único con `poppler-utils` para conversión de PDF a imagen

---

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/smart-invoice-auditor.git
cd smart-invoice-auditor

# Instalar dependencias
pip install -r requirements.txt

# Copiar plantilla de entorno
cp .env.example .env

# Agregar tus credenciales
# - JSON de Service Account de Google en GOOGLE_SERVICE_ACCOUNT_JSON
# - Claves API para tu proveedor de IA elegido
# - Credenciales IMAP para tu servidor de correo
# - URL del webhook de Slack
```

**Nota:** Necesitas un archivo `credentials.json` (o JSON en línea en `GOOGLE_SERVICE_ACCOUNT_JSON`) para el acceso a la API de Google Sheets.

---

## Configuración

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `AI_PROVIDER` | Backend de IA: `gemini`, `openai` o `minimax` | Sí |
| `IMAP_HOST` | Servidor de correo (ej. `imap.gmail.com`) | Sí |
| `IMAP_USER` | Dirección de correo electrónico | Sí |
| `IMAP_PASSWORD` | Contraseña de aplicación o contraseña IMAP | Sí |
| `GEMINI_API_KEY` | Clave API de Google Gemini | Si `AI_PROVIDER=gemini` |
| `OPENAI_API_KEY` | Clave API de OpenAI | Si `AI_PROVIDER=openai` |
| `MINIMAX_API_KEY` | Clave API de MiniMax | Si `AI_PROVIDER=minimax` |
| `SLACK_WEBHOOK_URL` | Webhook entrante para alertas | Sí |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Credenciales de Service Account (string JSON) | Sí |
| `GOOGLE_SHEET_NAME` | Nombre de la hoja de cálculo con hojas "Config" y "Aprobadas" | Sí |

---

## Métricas y Criterios de Éxito

### Pipeline de Validación

| Etapa | Estado | Descripción |
|-------|--------|-------------|
| **Correo Sin Leer** | 📥 Entrante | Correo sin ver con adjunto PDF |
| **Extraído por IA** | 🤖 Procesado | JSON con RUT, monto, fecha, productos |
| **Presupuesto Verificado** | ✅ Aprobado / 🚨 Excedido | Comparación contra presupuesto de Sheets |
| **Alertado** | 📤 Enrutado | Notificación de Slack enviada |
| **Registrado** | 📝 Almacenado | Fila agregada a hoja "Aprobadas" |

### Salida de Ejemplo

```json
{
  "rut_emisor": "12.345.678-9",
  "monto_total": 150990,
  "fecha_vencimiento": "2026-03-15",
  "lista_productos": ["Servicios Cloud", "Licencia Enterprise"]
}
```

**Lógica de Decisión:**

```
SI monto_total > presupuesto_disponible:
    → Enviar Alerta de Slack (🚨)
    → NO marcar correo como SEEN
DE LO CONTRARIO:
    → Registrar en Google Sheets ("Aprobadas")
    → Enviar Confirmación de Slack (✅)
    → Marcar correo como SEEN
```

---

## Despliegue con Docker

### Dockerfile (incluye poppler-utils)

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

### Construir y Ejecutar

```bash
# Construir la imagen
docker build -t smart-invoice-auditor .

# Ejecutar con archivo de entorno
docker run --env-file .env -v ./credentials.json:/app/credentials.json:ro smart-invoice-auditor
```

O usa `docker-compose`:

```bash
docker-compose up --build -d
```

---

## Estructura del Proyecto

```
smart-invoice-auditor/
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── README-ESP.md
├── src/
│   ├── __init__.py
│   ├── main.py                 # Orquestador con programador de 15 min
│   ├── config.py               # Cargador de variables de entorno
│   ├── models/
│   │   ├── __init__.py
│   │   └── invoice.py          # Pydantic: InvoiceData, BudgetCheck
│   ├── ai_providers/
│   │   ├── __init__.py         # Fábrica: get_ai_provider()
│   │   ├── base.py             # BaseAIProvider (ABC)
│   │   ├── gemini.py           # GeminiProvider (API de Archivos)
│   │   ├── openai.py           # OpenAIProvider (Visión)
│   │   └── minimax.py          # MiniMaxProvider (Visión)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py    # IMAP: buscar, descargar, marcar SEEN
│   │   ├── sheets_service.py   # gspread: consulta de presupuesto, inserción de fila
│   │   └── slack_service.py    # Webhooks: alertas con Block Kit
│   └── utils/
│       └── logger.py
└── tests/
    ├── __init__.py
    └── test_ai_providers.py
```

---

## Pruebas

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar con salida detallada
pytest -v

# Ejecutar archivo de prueba específico
pytest tests/test_ai_providers.py -v
```

---

## Licencia y Aviso Legal

**Licencia MIT** — Consulta el archivo `LICENSE` para más detalles.

> **Aviso Legal:** Este proyecto es solo para fines educativos y de portafolio. Procesa datos financieros sensibles — asegúrate de tener medidas de seguridad adecuadas (credenciales encriptadas, controles de acceso) antes de usarlo en producción. El autor no es responsable por pérdida de datos o acceso no autorizado.
