#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="${SERVICE_NAME:-auditly-backend}"
REGION="${REGION:-us-central1}"
RUNTIME_SERVICE_ACCOUNT="${RUNTIME_SERVICE_ACCOUNT:-}"
ROOT_AGENT_URL="${ROOT_AGENT_URL:-}"
ALLOW_UNAUTHENTICATED="${ALLOW_UNAUTHENTICATED:-false}"
FRONTEND_ORIGINS="${FRONTEND_ORIGINS:-http://localhost:3000,http://127.0.0.1:3000}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI is required. Install it and authenticate first." >&2
  exit 2
fi

ACTIVE_PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
if [[ "$ACTIVE_PROJECT" == "(unset)" ]]; then
  ACTIVE_PROJECT=""
fi
PROJECT_ID="${PROJECT_ID:-$ACTIVE_PROJECT}"

required_vars=(PROJECT_ID RUNTIME_SERVICE_ACCOUNT ROOT_AGENT_URL)
for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required environment variable: ${var_name}" >&2
    exit 2
  fi
done

case "$ALLOW_UNAUTHENTICATED" in
  true) invoker_flag="--allow-unauthenticated" ;;
  false) invoker_flag="--no-allow-unauthenticated" ;;
  *) echo "ALLOW_UNAUTHENTICATED must be true or false" >&2; exit 2 ;;
esac

env_vars="^~^GOOGLE_CLOUD_PROJECT=${PROJECT_ID}~FIRESTORE_DATABASE_ID=${FIRESTORE_DATABASE_ID:-auditly-db}~INVOICE_DOCUMENTAI_LOCATION=${INVOICE_DOCUMENTAI_LOCATION:-us}~INVOICE_DOCUMENTAI_PROCESSOR_ID=${INVOICE_DOCUMENTAI_PROCESSOR_ID:-ea53a2713455dd38}~INVOICE_DOCUMENTAI_FIELD_MASK=${INVOICE_DOCUMENTAI_FIELD_MASK:-entities}~PO_DOCUMENTAI_LOCATION=${PO_DOCUMENTAI_LOCATION:-us}~PO_DOCUMENTAI_PROCESSOR_ID=${PO_DOCUMENTAI_PROCESSOR_ID:-48ec6e25c970f7f9}~PO_DOCUMENTAI_FIELD_MASK=${PO_DOCUMENTAI_FIELD_MASK:-entities}~ROOT_AGENT_URL=${ROOT_AGENT_URL}~MAX_UPLOAD_SIZE_BYTES=${MAX_UPLOAD_SIZE_BYTES:-20971520}~FRONTEND_ORIGINS=${FRONTEND_ORIGINS}"

gcloud run deploy "$SERVICE_NAME" \
  --source "$SCRIPT_DIR" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --service-account "$RUNTIME_SERVICE_ACCOUNT" \
  --port 8080 \
  --timeout 900 \
  --memory 1Gi \
  "$invoker_flag" \
  --set-env-vars "$env_vars"

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --project "$PROJECT_ID" \
  --format='value(status.url)')"
printf '\nDeployed %s\nService URL: %s\n' "$SERVICE_NAME" "$SERVICE_URL"
printf 'Invoice endpoint: %s/api/v1/documents/invoice/process\n' "$SERVICE_URL"
printf 'Purchase order endpoint: %s/api/v1/documents/purchase-order/process\n' "$SERVICE_URL"
printf 'Compare endpoint: %s/api/v1/documents/compare\n' "$SERVICE_URL"
printf 'Inference endpoint: %s/api/v1/inference\n' "$SERVICE_URL"
