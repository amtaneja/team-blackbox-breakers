"""Gmail Pub/Sub push handler for invoice and purchase order PDFs."""

import base64
import json
import logging
import os
import hashlib
from pathlib import PurePosixPath
from urllib.parse import quote, urlsplit

import functions_framework
import requests
from flask import Request
from google.api_core.exceptions import PreconditionFailed
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.cloud import firestore
from google.cloud import storage
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
INVOICE_COLLECTION = os.getenv("INVOICE_FIRESTORE_COLLECTION", "invoices")
PO_COLLECTION = os.getenv("PO_FIRESTORE_COLLECTION", "purchase_orders")
INFERENCE_COLLECTION = os.getenv("INFERENCE_FIRESTORE_COLLECTION", "inference")
INVOICE_LABEL = os.getenv("INVOICE_GMAIL_LABEL", "Invoice")
PO_LABEL = os.getenv("PO_GMAIL_LABEL", "Purchase Order")
MAX_ATTACHMENT_BYTES = int(os.getenv("MAX_ATTACHMENT_BYTES", str(20 * 1024 * 1024)))
GCS_BUCKET = os.getenv("GCS_BUCKET", "aman-enterprises-invoices")


def _backend_auth_headers(api_url: str) -> dict[str, str]:
    """Return a Cloud Run ID token header for private backend requests.

    Local HTTP URLs are left unauthenticated so the documented emulator/local
    workflow continues to work. For Cloud Run URLs, the audience is the service
    origin (scheme + host), unless BACKEND_AUDIENCE is explicitly configured.
    """
    parsed = urlsplit(api_url)
    if parsed.scheme != "https" or not parsed.netloc:
        return {}

    audience = os.getenv("BACKEND_AUDIENCE") or f"{parsed.scheme}://{parsed.netloc}"
    token = id_token.fetch_id_token(GoogleAuthRequest(), audience)
    return {"Authorization": f"Bearer {token}"}


def _gmail_service():
    credentials = Credentials.from_authorized_user_info(
        json.loads(os.environ["GMAIL_OAUTH_CREDENTIALS"]), scopes=[GMAIL_SCOPE]
    )
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def _decode_attachment(service, message_id: str, part: dict) -> bytes:
    body = part.get("body", {})
    data = body.get("data")
    if not data and body.get("attachmentId"):
        attachment = service.users().messages().attachments().get(
            userId="me", messageId=message_id, id=body["attachmentId"]
        ).execute()
        data = attachment["data"]
    return base64.urlsafe_b64decode(data or "")


def _pdf_attachments(service, message: dict):
    message_id = message["id"]
    parts = []
    payload = message.get("payload", {})
    stack = [payload]
    while stack:
        part = stack.pop()
        stack.extend(part.get("parts", []))
        filename = part.get("filename", "")
        mime_type = part.get("mimeType", "")
        if filename.lower().endswith(".pdf") or mime_type == "application/pdf":
            content = _decode_attachment(service, message_id, part)
            if content.startswith(b"%PDF-"):
                if len(content) > MAX_ATTACHMENT_BYTES:
                    raise ValueError(f"Attachment {filename!r} exceeds size limit")
                parts.append((filename or "invoice.pdf", content))
    return parts


def _header(message: dict, name: str) -> str:
    for item in message.get("payload", {}).get("headers", []):
        if item.get("name", "").lower() == name.lower():
            return item.get("value", "")
    return ""


def _po_id(details: dict) -> str | None:
    fields = details.get("fields", {})
    for key in (
        "purchase_order_id", "po_id", "purchase_order", "purchase_order_number", "po_number"
    ):
        value = fields.get(key)
        if value:
            return str(value).strip()
    return None


def _find_purchase_order(db, po_id: str) -> tuple[dict, bool, str]:
    """Return saved PO details, existence, and its source PDF URI."""
    snapshot = db.collection(PO_COLLECTION).document(po_id).get()
    if snapshot.exists:
        record = snapshot.to_dict()
        return record.get("po_details", {}), True, record.get("po_file_link", "")

    matches = list(
        db.collection(PO_COLLECTION).where("po_id", "==", po_id).limit(1).stream()
    )
    if matches:
        record = matches[0].to_dict()
        return record.get("po_details", {}), True, record.get("po_file_link", "")
    return {}, False, ""


def _inference_document_id(invoice_id: str) -> str:
    """Return a readable Firestore document ID derived from the invoice ID."""
    invoice_id = str(invoice_id).strip()
    if not invoice_id:
        raise ValueError("Invoice ID is required for an inference document")
    return quote(invoice_id, safe="-_.~")


def _backfill_inference_metadata(db, message_id: str, attachment_key: str) -> None:
    """Move legacy inference data to an invoice ID and fill its metadata."""
    invoice = db.collection(INVOICE_COLLECTION).document(
        f"{message_id}_{attachment_key}"
    ).get()
    if not invoice.exists:
        return
    invoice_record = invoice.to_dict()
    legacy_ref = db.collection(INFERENCE_COLLECTION).document(
        f"{message_id}_{attachment_key}"
    )
    legacy_snapshot = legacy_ref.get()
    invoice_id = invoice_record.get("invoice_id") or invoice_record.get(
        "invoice_details", {}
    ).get("invoice_number")
    if not invoice_id:
        return
    inference_ref = db.collection(INFERENCE_COLLECTION).document(
        _inference_document_id(invoice_id)
    )
    existing_snapshot = inference_ref.get()
    if not legacy_snapshot.exists and not existing_snapshot.exists:
        return
    if legacy_snapshot.exists and legacy_ref.id != inference_ref.id:
        inference_ref.set(legacy_snapshot.to_dict(), merge=True)
    _, _, po_file_link = _find_purchase_order(db, invoice_record.get("po_id", ""))
    inference_ref.set(
        {
            "invoice_id": invoice_id,
            "email_from": invoice_record.get("email_from", ""),
            "email_subject": invoice_record.get("email_subject", ""),
            "po_file_link": po_file_link,
            "invoice_file_link": invoice_record.get("invoice_file_link", ""),
        },
        merge=True,
    )
    if legacy_snapshot.exists and legacy_ref.id != inference_ref.id:
        legacy_ref.delete()


def _upload_pdf(
    storage_client,
    document_type: str,
    message_id: str,
    attachment_key: str,
    filename: str,
    content: bytes,
) -> str:
    """Upload one PDF and return its private Cloud Storage URI."""
    folder = (
        "purchase_order_uploaded"
        if document_type == "purchase_order"
        else "invoices_uploaded"
    )
    safe_filename = PurePosixPath(filename.replace("\\", "/")).name or "document.pdf"
    object_name = f"{folder}/{message_id}/{attachment_key}_{safe_filename}"
    blob = storage_client.bucket(GCS_BUCKET).blob(object_name)
    try:
        blob.upload_from_string(
            content,
            content_type="application/pdf",
            if_generation_match=0,
        )
    except PreconditionFailed:
        # A previous delivery may have uploaded this same deterministic object.
        pass
    return f"gs://{GCS_BUCKET}/{object_name}"


def _process_message(
    service, db, message_id: str, document_type: str, api_url: str
):
    api_headers = _backend_auth_headers(api_url)
    message = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()
    attachments = _pdf_attachments(service, message)
    storage_client = storage.Client() if attachments else None
    for index, (filename, content) in enumerate(attachments):
        attachment_key = hashlib.sha256(f"{index}:{filename}".encode()).hexdigest()[:16]
        marker = db.collection("_gmail_invoice_processed").document(
            f"{message_id}_{attachment_key}"
        )
        if marker.get().exists:
            if document_type == "invoice":
                _backfill_inference_metadata(db, message_id, attachment_key)
            continue
        file_link = _upload_pdf(
            storage_client,
            document_type,
            message_id,
            attachment_key,
            filename,
            content,
        )
        if document_type == "purchase_order":
            response = requests.post(
                api_url,
                files={"file": (filename, content, "application/pdf")},
                headers=api_headers,
                timeout=180,
            )
            response.raise_for_status()
            details = response.json()
            po_id = _po_id(details)
            if not po_id:
                raise ValueError(
                    "Purchase order API response has no recognized PO ID in fields"
                )
            po_ref = db.collection(PO_COLLECTION).document(po_id)
            po_ref.set(
                {"po_id": po_id, "po_details": details, "po_file_link": file_link}
            )
            marker.set({"type": document_type, "processed_at": firestore.SERVER_TIMESTAMP})
        else:
            ref = db.collection(INVOICE_COLLECTION).document(
                f"{message_id}_{attachment_key}"
            )
            saved_invoice = ref.get()
            if saved_invoice.exists:
                invoice_record = saved_invoice.to_dict()
                if invoice_record.get("comparison_status") == "completed":
                    _backfill_inference_metadata(db, message_id, attachment_key)
                    marker.set(
                        {"type": document_type, "processed_at": firestore.SERVER_TIMESTAMP}
                    )
                    continue
                details = invoice_record["invoice_details"]
                po_id = invoice_record["po_id"]
                po_details = invoice_record.get("po_details", {})
                po_available = invoice_record.get("po_available", False)
                ref.update({"invoice_file_link": file_link})
                found_po_details, found_po, po_file_link = _find_purchase_order(db, po_id)
                if found_po:
                    po_details, po_available = found_po_details, True
                    ref.update(
                        {
                            "po_details": po_details,
                            "po_available": True,
                            "message": "po is available",
                            "comparison_status": "pending",
                        }
                    )
            else:
                response = requests.post(
                    api_url,
                    files={"file": (filename, content, "application/pdf")},
                    headers=api_headers,
                    timeout=180,
                )
                response.raise_for_status()
                details = response.json()
                invoice_id = details.get("invoice_number")
                po_id = details.get("purchase_order")
                if not po_id:
                    raise ValueError("Invoice API response does not contain purchase_order")
                po_id = str(po_id).strip()
                po_details, po_available, po_file_link = _find_purchase_order(db, po_id)
                invoice_record = {
                        "invoice_id": invoice_id,
                        "po_id": po_id,
                        "invoice_details": details,
                        "po_details": po_details,
                        "invoice_file_link": file_link,
                        "po_available": po_available,
                        "message": "po is available" if po_available else "po is missing",
                        "comparison_status": (
                            "pending" if po_available else "skipped_po_missing"
                        ),
                        "gmail_message_id": message_id,
                        "attachment_name": filename,
                        "email_from": _header(message, "From"),
                        "email_subject": _header(message, "Subject"),
                        "processed_at": firestore.SERVER_TIMESTAMP,
                    }
                ref.set(invoice_record)

            if po_available:
                compare_response = requests.post(
                    os.environ["COMPARISON_API_URL"],
                    json={"invoice": details, "purchase_order": po_details},
                    headers=_backend_auth_headers(os.environ["COMPARISON_API_URL"]),
                    timeout=180,
                )
                compare_response.raise_for_status()
                comparison = compare_response.json()
                analysis = comparison.get("analysis")
                if not isinstance(analysis, str) or not analysis.strip():
                    raise ValueError("Compare API response does not contain analysis text")
                invoice_id = invoice_record.get("invoice_id") or details.get("invoice_number")
                if not invoice_id:
                    raise ValueError("Invoice API response does not contain invoice_number")
                db.collection(INFERENCE_COLLECTION).document(
                    _inference_document_id(invoice_id)
                ).set(
                    {
                        "invoice_id": invoice_id,
                        "po_id": po_id,
                        "summary": analysis,
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "email_from": invoice_record.get("email_from", ""),
                        "email_subject": invoice_record.get("email_subject", ""),
                        "po_file_link": po_file_link if po_available else "",
                        "invoice_file_link": file_link,
                    }
                )
                ref.update(
                    {
                        "comparison_status": "completed",
                    }
                )
            if po_available:
                marker.set({"type": document_type, "processed_at": firestore.SERVER_TIMESTAMP})


@functions_framework.http
def gmail_invoice_webhook(request: Request):
    """Handle Gmail's Pub/Sub push notification (push subscription target)."""
    if request.method != "POST":
        return ("Method not allowed", 405)
    envelope = request.get_json(silent=True) or {}
    if "message" not in envelope or "data" not in envelope["message"]:
        return ("Bad Pub/Sub envelope", 400)
    try:
        notification = json.loads(
            base64.b64decode(envelope["message"]["data"]).decode("utf-8")
        )
        email_address = notification.get("emailAddress", "").lower()
        expected = os.environ["GMAIL_USER"].lower()
        if email_address != expected:
            logging.info("Ignoring notification for %s", email_address)
            return ("", 204)

        service = _gmail_service()
        db = firestore.Client(
            database=os.getenv("FIRESTORE_DATABASE_ID", "auditly-db")
        )
        routes = (
            (PO_LABEL, "purchase_order", os.environ["PURCHASE_ORDER_API_URL"]),
            (INVOICE_LABEL, "invoice", os.environ["INVOICE_API_URL"]),
        )
        label_ids = _label_ids(service)
        for label_name, document_type, api_url in routes:
            label_id = label_ids.get(label_name)
            if not label_id:
                logging.warning(
                    "Configured Gmail label %r was not found; skipping this document type",
                    label_name,
                )
                continue
            # Search current label; Firestore makes Pub/Sub redelivery safe.
            page_token = None
            while True:
                result = service.users().messages().list(
                    userId="me",
                    labelIds=[label_id],
                    q="has:attachment filename:pdf",
                    maxResults=100,
                    pageToken=page_token,
                ).execute()
                for item in result.get("messages", []):
                    _process_message(
                        service, db, item["id"], document_type, api_url
                    )
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
        return ("", 204)
    except Exception:
        logging.exception("Gmail invoice processing failed")
        return ("Processing failed; Pub/Sub may retry", 500)


def _label_ids(service) -> dict[str, str]:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    return {label["name"]: label["id"] for label in labels}
