# Gmail document processor

This HTTP Cloud Run function consumes Gmail Pub/Sub notifications and handles
two user labels:

- `Purchase Order`: uploads PDF attachments to the FastAPI purchase order
  endpoint and stores `po_id` and `po_details` in the Firestore collection
  `purchase_orders`. It saves the source PDF under
  `gs://aman-enterprises-invoices/purchase_order_uploaded/` and records the
  object URI in `po_file_link`. The document ID is the extracted PO ID.
- `Invoice`: uploads PDF attachments to the FastAPI invoice endpoint, extracts
  `invoice_number` and `purchase_order` from its JSON response, looks up that
  `po_id` in `purchase_orders`, then stores `invoice_id`, `po_id`, the full
  response as `invoice_details`, the matched `po_details`, and the source PDF
  URI as `invoice_file_link` in `invoices`. It saves source PDFs under
  `gs://aman-enterprises-invoices/invoices_uploaded/`.
  When a PO is available, it calls the FastAPI compare endpoint and stores its
  `analysis` as `summary` in the `inference` collection, alongside `invoice_id`,
  `po_id`, and a server-generated `timestamp`. It also copies `email_from` and
  `email_subject` from the invoice record, plus `invoice_file_link` and
  `po_file_link` from the invoice and purchase order records. Existing inference
  records are moved to use `invoice_id` as their Firestore document ID and get
  these metadata fields filled on the next Gmail scan.

For each invoice, `po_available` is `true` with `message: "po is available"`
when its PO is found. If the PO is not found yet, the invoice is still saved
with `po_available: false`, `message: "po is missing"`, and an empty
`po_details` object. Attachment processing is idempotent across Pub/Sub
redelivery. The handler scans Purchase Order messages before Invoice messages
so a PO already carrying its label is stored before its related invoice is
processed.

## Required setup

1. Enable Gmail API, Cloud Run, Cloud Build, Pub/Sub, Firestore, and Secret
   Manager APIs in the Google Cloud project. Create a Firestore database.
2. Create a Pub/Sub topic, for example `gmail-document-notifications`. Grant
   `gmail-api-push@system.gserviceaccount.com` the Pub/Sub Publisher role on
   this topic.
3. In Gmail, create the labels `Purchase Order` and `Invoice`, and apply the
   right label to each incoming email (a Gmail filter can do this). Gmail API
   `users.watch` requires user OAuth; a service account cannot read a personal
   Gmail mailbox. Create an OAuth client and authorize
   `amanenterprises3105@gmail.com` with
   `https://www.googleapis.com/auth/gmail.readonly`. Store the authorized-user
   JSON as a Secret Manager secret and retain its refresh token. If the OAuth
   consent app is in Testing, refresh tokens expire after seven days; move it
   to Production (and complete any required verification) for ongoing use.
4. Deploy the FastAPI app as a private Cloud Run service. Set
   `INVOICE_API_URL` to
   `https://<backend-host>/api/v1/documents/invoice/process` and
   `PURCHASE_ORDER_API_URL` to
   `https://<backend-host>/api/v1/documents/purchase-order/process`. The
   function obtains a Cloud Run ID token using its runtime service account. If
   you use a custom domain, set `BACKEND_AUDIENCE` to the backend Cloud Run
   service URL. Set
   `COMPARISON_API_URL` to
   `https://<backend-host>/api/v1/documents/compare`. The backend must have
   `ROOT_AGENT_URL` configured and its root agent reachable. The function's
   runtime service account needs `roles/run.invoker` on the backend service;
   `deploy.sh` grants this using `BACKEND_SERVICE_NAME` (default
   `auditly-backend`).
5. Set the Cloud Run runtime service account as an object creator on the
   `aman-enterprises-invoices` bucket (`roles/storage.objectCreator`). The two
   listed “folders” are object name prefixes in this same bucket; Cloud Storage
   creates them as objects are uploaded. Set `GCS_BUCKET` if you use a
   different bucket name.

## Run locally

This runs the function against the real Gmail mailbox and local FastAPI API,
but writes Firestore data to the local emulator. Use a Gmail OAuth authorized
user JSON with read-only Gmail scope in `gmail-oauth.json` in this directory;
the file is gitignored. The simulated notification below tells the function
to scan both configured Gmail labels, so no Pub/Sub subscription is needed.

1. Start the Firestore emulator (requires Node.js):

   ```sh
   cd integrations/gmail_invoice_function
   npx firebase-tools emulators:start --only firestore --project local-invoice-test
   ```

2. In a second terminal, start the backend with its Document AI settings and
   Google ADC configured. From `backend`, create `document_ai/.env` from
   `.env.example` if needed, then run:

   ```sh
   uv sync
   uv run uvicorn app.main:app --reload
   ```

3. In a third terminal, install and run this function. From
   `integrations/gmail_invoice_function`:

   ```sh
   uv venv
   uv pip install --python .venv/bin/python -r requirements.txt
   export GOOGLE_CLOUD_PROJECT=local-invoice-test
   export FIRESTORE_EMULATOR_HOST=127.0.0.1:8085
   export GMAIL_USER=amanenterprises3105@gmail.com
   export GMAIL_OAUTH_CREDENTIALS="$(cat gmail-oauth.json)"
   export INVOICE_API_URL=http://127.0.0.1:8000/api/v1/documents/invoice/process
   export PURCHASE_ORDER_API_URL=http://127.0.0.1:8000/api/v1/documents/purchase-order/process
   export COMPARISON_API_URL=http://127.0.0.1:8000/api/v1/documents/compare
   export GCS_BUCKET=aman-enterprises-invoices
export FIRESTORE_DATABASE_ID=auditly-db
   uv run --with functions-framework functions-framework --target=gmail_invoice_webhook --port=8082
   ```

4. Trigger a local scan with a simulated Pub/Sub push. It reads messages from
   the real Gmail labels and processes any not already marked in the emulator:

   ```sh
   python -c 'import base64,json; n={"emailAddress":"amanenterprises3105@gmail.com","historyId":"1"}; print(json.dumps({"message":{"data":base64.b64encode(json.dumps(n).encode()).decode()}}))' \
     | curl -sS -X POST http://127.0.0.1:8082 -H 'Content-Type: application/json' --data-binary @-
   ```

Inspect `purchase_orders`, `invoices`, `inference`, and `_gmail_invoice_processed` in the
Firestore emulator UI at `http://127.0.0.1:4000` (start the UI by removing
`"enabled": false` from `firebase.json`), or query the emulator with the
Firestore SDK. The test still calls Google Gmail and Document AI APIs, so
valid Gmail OAuth credentials and backend ADC are required. The Firestore
emulator keeps the writes local; don’t unset `FIRESTORE_EMULATOR_HOST` unless
you intend to write to the configured cloud project. The PDF upload step uses
the real Cloud Storage bucket even during a local run, so the local ADC identity
must have `roles/storage.objectCreator` on that bucket.

## Deploy

The deployment script uses the active `gcloud` project unless `PROJECT_ID` is
set. Set the backend URLs and the Cloud Run runtime service account, then run it
from this directory:

```sh
export PROJECT_ID=project-c7b154e5-95da-4f50-a5b
export REGION=us-central1
export RUNTIME_SERVICE_ACCOUNT=YOUR_RUNTIME_SERVICE_ACCOUNT
export INVOICE_API_URL=https://YOUR_BACKEND/api/v1/documents/invoice/process
export PURCHASE_ORDER_API_URL=https://YOUR_BACKEND/api/v1/documents/purchase-order/process
export COMPARISON_API_URL=https://YOUR_BACKEND/api/v1/documents/compare
export FIRESTORE_DATABASE_ID=auditly-db
# Optional for custom domains; defaults to the service origin in the URLs above
# export BACKEND_AUDIENCE=https://YOUR_BACKEND.run.app
# Optional if the backend Cloud Run service has a different name
# export BACKEND_SERVICE_NAME=auditly-backend
# Optional: defaults to gmail-oauth-authorized-user
export GMAIL_OAUTH_SECRET=gmail-oauth-authorized-user

./deploy.sh
```

Before deployment, grant the runtime service account `roles/datastore.user` on
the project, `roles/secretmanager.secretAccessor` on the OAuth secret, and
`roles/storage.objectCreator` on the bucket. The deploy script also grants this
identity `roles/run.invoker` on the backend. The function deploys without public
invocation. The `gs://` file links are private object URIs; grant read access
to any users or services that need to open them.

After deployment, grant the Pub/Sub push service account
`roles/run.invoker` on the Cloud Run service, then create an authenticated push
subscription using OIDC:

```sh
gcloud pubsub topics create gmail-document-notifications
gcloud pubsub subscriptions create gmail-document-push \
  --topic=gmail-document-notifications \
  --push-endpoint="$(gcloud run services describe gmail-document-webhook --region us-central1 --format='value(status.url)')" \
  --push-auth-service-account=PUBSUB_PUSH_SERVICE_ACCOUNT
```

Grant the Gmail publisher identity `roles/pubsub.publisher` on the topic.
Grant the `PUBSUB_PUSH_SERVICE_ACCOUNT` identity `roles/run.invoker` on the
Cloud Run service.

## Start and renew Gmail watch

Gmail watches expire after at most seven days. Call `users.watch` once after
deployment and renew it daily (for example, with Cloud Scheduler). Use the
same OAuth authorized-user credentials as the function:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

credentials = Credentials.from_authorized_user_file("gmail-oauth.json", [
    "https://www.googleapis.com/auth/gmail.readonly"
])
gmail = build("gmail", "v1", credentials=credentials)
print(gmail.users().watch(userId="me", body={
    "topicName": "projects/YOUR_PROJECT_ID/topics/gmail-document-notifications",
    "labelIds": ["INBOX"],
    "labelFilterBehavior": "INCLUDE",
}).execute())
```

The watch listens for inbox changes; the handler checks both configured user
labels and only processes messages carrying the matching label. It scans all
pages of each label's PDF message results. Firestore stores processed
attachment markers in the internal `_gmail_invoice_processed` collection to
avoid duplicate Document AI requests on Pub/Sub redelivery.
