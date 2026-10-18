"""Save a purchase-order extraction to Firestore."""

import argparse
import json
from pathlib import Path
from typing import Any

from google.cloud import firestore


def save_purchase_order(po_id: str, po_details: dict[str, Any]) -> str:
    """Upsert a PO using its identifier as the Firestore document ID."""
    normalized_po_id = po_id.strip()
    if not normalized_po_id:
        raise ValueError("po_id must not be empty")
    if not isinstance(po_details, dict):
        raise ValueError("po_details must be a JSON object")

    db = firestore.Client(database="auditly-db")
    db.collection("purchase_orders").document(normalized_po_id).set(
        {"po_id": normalized_po_id, "po_details": po_details}
    )
    return normalized_po_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write a purchase order JSON object to Firestore."
    )
    parser.add_argument("--po-id", required=True, help="Purchase order identifier")
    parser.add_argument(
        "--details-file",
        required=True,
        type=Path,
        help="Path to a JSON file containing the full purchase-order response",
    )
    args = parser.parse_args()

    details = json.loads(args.details_file.read_text(encoding="utf-8"))
    if not isinstance(details, dict):
        parser.error("details file must contain a JSON object")

    saved_id = save_purchase_order(args.po_id, details)
    print(
        f"Saved purchase order {saved_id!r} to "
        "auditly-db / purchase_orders with fields po_id and po_details."
    )


if __name__ == "__main__":
    main()
