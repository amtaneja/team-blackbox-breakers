# PDF Document AI API

FastAPI accepts a PDF upload, sends it to Google Cloud Document AI, and returns a compact invoice summary with extracted header fields and line items. OCR text, confidence scores, anchors, and page geometry are omitted.

## Layout

- `app/` contains the FastAPI application and versioned HTTP endpoints.
- `document_ai/` contains Document AI settings, the Google Cloud service integration, and a sample PDF for local testing.

## Setup

From the `backend` directory (install uv first):

```bash
uv sync
cp document_ai/.env.example document_ai/.env
```

Fill in `GOOGLE_CLOUD_PROJECT`, `DOCUMENTAI_LOCATION`, and `DOCUMENTAI_PROCESSOR_ID` in `document_ai/.env`. Configure Google Application Default Credentials with an identity that can use the processor, for example:

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
curl -X POST http://127.0.0.1:8000/api/v1/documents/process \
  -F 'file=@document_ai/sample_data/inv_28_rajputana.pdf;type=application/pdf'
```

The response body contains only the compact invoice summary; the raw OCR text, entity metadata, and page layout are omitted. The default maximum upload size is 20 MiB. Adjust `MAX_UPLOAD_SIZE_BYTES` in `document_ai/.env` to change it. `DOCUMENTAI_PROCESSOR_VERSION_ID` is optional. `DOCUMENTAI_FIELD_MASK=entities` limits the processor response before the API builds its compact summary.

## Run the included PDF directly

From `backend`:

```bash
uv run python -m document_ai.process_document
```
