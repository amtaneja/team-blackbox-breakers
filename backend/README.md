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

## Deploy the FastAPI service to Cloud Run

`deploy.sh` builds the backend from `Dockerfile` and deploys it as a Cloud Run
service. From the `backend` directory, set the project, runtime service
account, and the deployed root-agent A2A URL before running it:

```sh
export PROJECT_ID=project-c7b154e5-95da-4f50-a5b
export REGION=us-central1
export RUNTIME_SERVICE_ACCOUNT=YOUR_BACKEND_RUNTIME_SERVICE_ACCOUNT
export ROOT_AGENT_URL=https://YOUR_ROOT_AGENT_HOST/a2a/app
./deploy.sh
```

The runtime service account needs `roles/documentai.apiUser` on the project.
The dashboard overview reads `GET /api/v1/inference` from the `inference`
collection in Firestore database `auditly-db`. The runtime service account also
needs `roles/datastore.user`; set `FIRESTORE_DATABASE_ID` to override the
database name. Set the frontend's `NEXT_PUBLIC_API_BASE_URL` to the backend API
base URL ending in `/api/v1`.
The script defaults to a private Cloud Run service. To allow unauthenticated
requests, set `ALLOW_UNAUTHENTICATED=true` before deploying. The current FastAPI
app has no request authentication, so public access also makes its PDF
processing endpoints available to anyone who can reach the service. The
dashboard's browser-side fetch works only when the backend is browser-reachable
and its `FRONTEND_ORIGINS` includes the frontend origin. For a private service,
serve the request through a frontend server-side proxy that adds a Cloud Run
ID token; do not expose the private service URL directly to the browser.

After deployment, the script prints the service URL and its invoice,
purchase-order, and comparison endpoint URLs. Set those URLs in
`integrations/gmail_invoice_function/deploy.sh` before deploying the email
function.

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
