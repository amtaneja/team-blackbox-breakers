"""Read saved invoice and purchase order inference summaries."""

from typing import Any
import os

from fastapi import APIRouter, HTTPException, status
from google.api_core.exceptions import GoogleAPIError
from google.cloud import firestore

router = APIRouter(prefix="/inference", tags=["inference"])
FIRESTORE_DATABASE_ID = os.getenv("FIRESTORE_DATABASE_ID", "auditly-db")


@router.get("", summary="List invoice comparison summaries")
def list_inference_summaries() -> dict[str, Any]:
    """Return inference summaries ordered newest first."""
    try:
        db = firestore.Client(database=FIRESTORE_DATABASE_ID)
        snapshots = (
            db.collection("inference")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .stream()
        )
        items = []
        for snapshot in snapshots:
            data = snapshot.to_dict() or {}
            timestamp = data.get("timestamp")
            items.append(
                {
                    "id": snapshot.id,
                    "invoice_id": data.get("invoice_id"),
                    "po_id": data.get("po_id"),
                    "summary": data.get("summary", ""),
                    "email_from": data.get("email_from", ""),
                    "email_subject": data.get("email_subject", ""),
                    "invoice_file_link": data.get("invoice_file_link", ""),
                    "po_file_link": data.get("po_file_link", ""),
                    "timestamp": timestamp.isoformat() if timestamp else None,
                }
            )
        return {"items": items, "count": len(items)}
    except GoogleAPIError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Inference records are temporarily unavailable.",
        ) from error
