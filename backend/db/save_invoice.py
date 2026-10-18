"""Save an invoice extraction and its matching PO details to Firestore."""

import argparse
import json
import re
from pathlib import Path
from typing import Any

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter


def save_invoice(invoice_details: dict[str, Any]) -> dict[str, Any]:
    """Query the PO by the invoice's purchase_order field and save the invoice."""
    invoice_id = invoice_details.get("invoice_number")
    po_id = invoice_details.get("purchase_order")
    if not invoice_id:
        raise ValueError("invoice_details must contain invoice_number")
    if not po_id:
        raise ValueError("invoice_details must contain purchase_order")

    invoice_id = str(invoice_id).strip()
    po_id = str(po_id).strip()
    if not invoice_id or not po_id:
        raise ValueError("invoice_number and purchase_order must not be empty")

    db = firestore.Client(database="auditly-db")
    po_matches = list(
        db.collection("purchase_orders")
        .where(filter=FieldFilter("po_id", "==", po_id))
        .limit(1)
        .stream()
    )
    po_available = bool(po_matches)
    po_details = (
        po_matches[0].to_dict().get("po_details", {}) if po_available else {}
    )

    # Firestore document IDs cannot contain '/'; preserve the original invoice_id
    # as a field while deriving a path-safe ID for the document.
    document_id = re.sub(r"[/\\]", "_", invoice_id)
    db.collection("invoices").document(document_id).set(
        {
            "invoice_id": invoice_id,
            "po_id": po_id,
            "invoice_details": invoice_details,
            "po_available": po_available,
            "message": "po is available" if po_available else "po is missing",
            "po_details": po_details,
        }
    )
    return {
        "invoice_id": invoice_id,
        "po_id": po_id,
        "po_available": po_available,
        "po_details": po_details,
        "document_id": document_id,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Save an invoice and its matching PO data to Firestore."
    )
    parser.add_argument(
        "--details-file",
        required=True,
        type=Path,
        help="Path to a JSON file containing the full invoice API response",
    )
    args = parser.parse_args()
    details = json.loads(args.details_file.read_text(encoding="utf-8"))
    if not isinstance(details, dict):
        parser.error("details file must contain a JSON object")

    result = save_invoice(details)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
