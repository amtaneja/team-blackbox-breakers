# PDF Document AI API

FastAPI accepts invoice and purchase order PDF uploads, sends each to its configured Google Cloud Document AI processor, and returns a compact extraction. OCR text, confidence scores, anchors, and page geometry are omitted.

## Layout

- `app/` contains the FastAPI application and versioned HTTP endpoints.
- `document_ai/` contains Document AI settings, the Google Cloud service integration, and a sample PDF for local testing.

## Setup

From the `backend` directory (install uv first):

```bash
uv sync
cp document_ai/.env.example document_ai/.env
```

The example environment includes both processor IDs. Check the `GOOGLE_CLOUD_PROJECT`, `INVOICE_DOCUMENTAI_*`, and `PO_DOCUMENTAI_*` values in `document_ai/.env`. Configure Google Application Default Credentials with an identity that can use both processors, for example:

```bash
gcloud auth application-default login
```

## Run the API

From `backend`:

```bash
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. Liveness is available at `GET /health`.

## Upload a PDF

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/invoice/process \
  -F 'file=@document_ai/sample_data/inv_28_rajputana.pdf;type=application/pdf'
```

Purchase order uploads use a separate URL:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/purchase-order/process \
  -F 'file=@document_ai/sample_data/purchase_order.pdf;type=application/pdf'
```

To compare the two extraction results, run the root agent's A2A-enabled server
from `agents/root-agent`:

```sh
uv run uvicorn app.fast_api_app:app --host 127.0.0.1 --port 8081
```

Then set `ROOT_AGENT_URL=http://127.0.0.1:8081/a2a/app` in
`backend/document_ai/.env` and restart the backend. The ADK Web UI on port 8080
does not expose the A2A endpoint used by this integration. Send both processed
JSON objects to the backend:

```sh
curl -X POST http://127.0.0.1:8000/api/v1/documents/compare \
  -H 'Content-Type: application/json' \
  -d '{"invoice": {"total_amount": "125.00"}, "purchase_order": {"fields": {"total_amount": "120.00"}, "line_items": []}}'
```

The response contains the agent's discrepancy analysis in the `analysis` field.

Invoice responses contain normalized invoice fields. Purchase order responses contain a `fields` map using the processor's entity names plus `line_items`. Both omit raw OCR text, entity metadata, and page layout. The default maximum upload size is 20 MiB. Adjust `MAX_UPLOAD_SIZE_BYTES` in `document_ai/.env` to change it. The `*_DOCUMENTAI_PROCESSOR_VERSION_ID` settings are optional. Each `*_DOCUMENTAI_FIELD_MASK=entities` setting limits the processor response before the API builds its compact summary.

## Run the included PDF directly

From `backend`:

```bash
uv run python -m document_ai.process_document
```
