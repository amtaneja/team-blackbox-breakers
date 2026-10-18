#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="${SERVICE_NAME:-auditly-frontend}"
REGION="${REGION:-us-central1}"
API_BASE_URL="${API_BASE_URL:-https://auditly-backend-xr2oaad7sa-uc.a.run.app/api/v1}"
SESSION_SECRET_SECRET="${SESSION_SECRET_SECRET:-auditly-session-secret}"
RUNTIME_SERVICE_ACCOUNT="${RUNTIME_SERVICE_ACCOUNT:-}"

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud CLI is required. Install it and authenticate first." >&2
  exit 2
fi

ACTIVE_PROJECT="$(gcloud config get-value project 2>/dev/null || true)"
if [[ "$ACTIVE_PROJECT" == "(unset)" ]]; then
  ACTIVE_PROJECT=""
fi
PROJECT_ID="${PROJECT_ID:-$ACTIVE_PROJECT}"
if [[ -z "$PROJECT_ID" ]]; then
  echo "Set PROJECT_ID or configure an active gcloud project." >&2
  exit 2
fi

deploy_args=()
if [[ -n "$RUNTIME_SERVICE_ACCOUNT" ]]; then
  deploy_args+=(--service-account "$RUNTIME_SERVICE_ACCOUNT")
fi

gcloud run deploy "$SERVICE_NAME" \
  --source "$SCRIPT_DIR" \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --allow-unauthenticated \
  --port 8080 \
  --timeout 900 \
  --memory 1Gi \
  --set-env-vars "BACKEND_URL=${API_BASE_URL}" \
  --set-secrets "AUDITLY_SESSION_SECRET=${SESSION_SECRET_SECRET}:latest" \
  ${deploy_args[@]+"${deploy_args[@]}"}

SERVICE_URL="$(gcloud run services describe "$SERVICE_NAME" \
  --region "$REGION" --project "$PROJECT_ID" \
  --format='value(status.url)')"
printf '\nDeployed %s\nService URL: %s\n' "$SERVICE_NAME" "$SERVICE_URL"
