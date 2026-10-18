# Backend Specification

> **Status:** Initial, implementation-based spec  
> **Scope:** Backend behavior currently present in `backend/`. Update this document as the API and processing flow grow.

## 1. Purpose

The backend exposes an HTTP API for extracting structured data from invoice and purchase order PDF files. It uses Google Cloud Document AI processors and returns a compact JSON result without raw OCR text or page layout metadata.

## 2. Current architecture

```text
HTTP client
    │ multipart/form-data PDF
    ▼
FastAPI (`app/main.py`)
    ├── GET /health
    └── /api/v1/documents/* (`app/api/v1/endpoints/documents.py`)
            │ validate type, size, PDF header
            ▼
       thread pool (`run_in_threadpool`)
            ▼
       Document AI service (`document_ai/service.py`)
            ├── invoice processor
            └── purchase order processor
            ▼
       compact extraction JSON
```

The HTTP layer is asynchronous. The Google client call and response conversion are synchronous and are run in FastAPI's thread pool so they do not block the event loop. Settings are environment-backed and cached for the process lifetime.

## 3. HTTP API

### `GET /health`

Returns `200 OK` with `{"status":"ok"}`. This is a liveness check only; it does not verify Google Cloud credentials or processor availability.

### `POST /api/v1/documents/invoice/process`

Accepts one required multipart field named `file` containing an invoice PDF. Processes it with the configured invoice processor and returns the compact invoice object described below.

### `POST /api/v1/documents/purchase-order/process`

Accepts one required multipart field named `file` containing a purchase order PDF. Processes it with the configured purchase order processor and returns the compact purchase order object described below.

### `POST /api/v1/documents/compare`

Accepts the compact results from the invoice and purchase order processing routes
as JSON:

```json
{
  "invoice": { "...": "invoice extraction response" },
  "purchase_order": { "...": "purchase order extraction response" }
}
```

The backend sends both objects in an A2A `message/send` request to
`ROOT_AGENT_URL` and returns `{"analysis":"..."}` containing the agent's text
response. The agent is prompted to identify mismatched fields and values, explain
their significance, distinguish missing data from a mismatch, and avoid inventing
values. Returns 503 if `ROOT_AGENT_URL` is unset and 502 if the agent call fails
or returns no text.

### Upload validation and errors

The two document routes use the same validation and processing path:

| Condition | HTTP status | Current detail |
| --- | ---: | --- |
| Content type is not `application/pdf` or `application/octet-stream` | 415 | `Upload a PDF file (application/pdf).` |
| Content exceeds `MAX_UPLOAD_SIZE_BYTES` | 413 | Reports the configured byte limit |
| Content does not begin with `%PDF-` | 400 | `The uploaded file does not have a valid PDF header.` |
| Required Google Cloud project or selected processor settings are missing | 503 | Names missing settings |
| Google API request raises a Google API error | 502 | `Google Document AI could not process this PDF.` |

The upload is read up to one byte beyond the configured limit to detect oversize files. The upload handle is closed after processing or validation failure. The current header check is a lightweight format check, not full PDF parsing or safety validation.

## 4. Response shapes

### Invoice

The response is a JSON object with this shape; extracted values may be `null`, and `line_items` is an array:

```json
{
  "invoice_number": "string|null",
  "invoice_date": "string|null",
  "supplier": {
    "name": "string|null",
    "tax_id": "string|null",
    "address": "string|null"
  },
  "customer": {
    "name": "string|null",
    "tax_id": "string|null",
    "address": "string|null"
  },
  "purchase_order": "string|null",
  "currency": "string|null",
  "net_amount": "string|null",
  "tax_amount": "string|null",
  "total_amount": "string|null",
  "line_items": [
    {
      "description": "string|null",
      "product_code": "string|null",
      "quantity": "string|null",
      "unit_price": "string|null",
      "amount": "string|null"
    }
  ]
}
```

Values are read from Document AI entity `mentionText`, falling back to normalized text. Currency is retained only when it is a three-letter alphabetic value. Line-item entities are mapped to the listed fields.

### Purchase order

The response contains processor entity names in a `fields` map and extracted line items in a `line_items` array. Each line-item object contains whichever named properties the processor returned; property values may be `null`.

```json
{
  "fields": {
    "processor_entity_name": "string|null"
  },
  "line_items": [
    {
      "processor_line_item_property": "string|null"
    }
  ]
}
```

The purchase order field names are processor-defined and are not normalized to a fixed application schema yet.

### Data omitted from responses

The service compacts the Document AI response and does not return raw OCR text, entity confidence, text anchors, bounding geometry, or page layout metadata.

## 5. Processing flow

1. FastAPI routes the request to the invoice or purchase order handler.
2. The handler checks the content type, reads at most the configured limit plus one byte, enforces the size limit, and checks the `%PDF-` header.
3. It selects the document-type-specific processor settings.
4. It checks that the Google Cloud project, processor location, and processor ID are configured.
5. It creates a regional Document AI client and targets either the configured processor version or the processor default.
6. It submits the bytes as `application/pdf`, optionally applying the configured field mask.
7. It converts the protobuf response to a dictionary and compacts entities to the route's response shape.
8. The route returns the resulting JSON. Configuration errors map to 503 and Google API errors map to 502.

## 6. Configuration and runtime

Settings are loaded from environment variables and `backend/document_ai/.env` (when present). Unknown environment entries are ignored. Defaults and current names:

| Setting | Purpose |
| --- | --- |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project used to address processors |
| `INVOICE_DOCUMENTAI_LOCATION` | Invoice processor region |
| `INVOICE_DOCUMENTAI_PROCESSOR_ID` | Invoice processor ID |
| `INVOICE_DOCUMENTAI_PROCESSOR_VERSION_ID` | Optional invoice processor version; empty uses processor default |
| `INVOICE_DOCUMENTAI_FIELD_MASK` | Optional invoice response field mask |
| `PO_DOCUMENTAI_LOCATION` | Purchase order processor region |
| `PO_DOCUMENTAI_PROCESSOR_ID` | Purchase order processor ID |
| `PO_DOCUMENTAI_PROCESSOR_VERSION_ID` | Optional purchase order processor version; empty uses processor default |
| `PO_DOCUMENTAI_FIELD_MASK` | Optional purchase order response field mask |
| `ROOT_AGENT_URL` | Root agent A2A JSON-RPC endpoint, e.g. `http://127.0.0.1:8001/a2a/app` |
| `MAX_UPLOAD_SIZE_BYTES` | Maximum PDF upload size; defaults to 20 MiB |

Google authentication uses Application Default Credentials (ADC). The identity must be allowed to invoke the configured processors. The backend package targets Python 3.11 through 3.13 and uses FastAPI, Pydantic Settings, `python-multipart`, `google-cloud-documentai`, and Uvicorn.

## 7. Code map

| Path | Responsibility |
| --- | --- |
| `backend/app/main.py` | FastAPI app metadata, router registration, health endpoint |
| `backend/app/api/v1/endpoints/documents.py` | Upload endpoints, validation, error-to-HTTP mapping |
| `backend/app/api/v1/endpoints/comparison.py` | Comparison request schema and root agent error mapping |
| `backend/document_ai/config.py` | Environment-backed settings |
| `backend/document_ai/service.py` | Processor configuration, Document AI call, response compaction |
| `backend/document_ai/root_agent.py` | A2A request to the root agent and analysis extraction |
| `backend/document_ai/process_document.py` | Command-line entry point for the included sample invoice |

## 8. Current boundaries and open specification areas

These areas are not defined by the current implementation. Add requirements here as they are decided:

- Authentication, authorization, and tenant isolation: **Not implemented / unspecified**
- Persistence, document IDs, retrieval, and deletion: **Not implemented / unspecified**
- Background jobs, retries, idempotency, and processing status: **Not implemented / unspecified**
- API request/response schema versioning beyond the `/api/v1` URL prefix: **Unspecified**
- Normalized purchase order field schema: **Unspecified**
- Structured validation of extracted amounts, dates, and confidence thresholds: **Not implemented / unspecified**
- Rate limits, quotas, and concurrency limits: **Unspecified**
- Logging, metrics, tracing, and retention: **Unspecified**
- CORS and deployment/runtime topology: **Unspecified**
- Error response envelope and stable machine-readable error codes: **Unspecified**

## 9. Change log

| Date | Change |
| --- | --- |
| 2026-10-18 | Added root-agent comparison endpoint for processed invoice and purchase order data. |
| 2026-10-18 | Initial spec written from the current backend implementation. |
