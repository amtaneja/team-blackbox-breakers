# Firestore connection check

This script uses Google Application Default Credentials (ADC) and writes a
small verification record to `users/test-user` in the `auditly-db` database.

## Run locally

From the repository root:

```sh
gcloud auth application-default login
gcloud config set project project-c7b154e5-95da-4f50-a5b
uv run --with-requirements backend/db/requirements.txt python backend/db/firestore_connection.py
```

The project must contain the `auditly-db` Firestore database, and the signed-in
user needs permission to write documents (for example, `roles/datastore.user`).
The script reports success only after Firestore accepts the write. The created
record can be removed from Firebase Console under the `users` collection.

## Save a purchase order

`save_purchase_order.py` writes the required fields `po_id` and `po_details`
to `purchase_orders` in `auditly-db`. `po_details` must be a JSON object,
typically the full response from the purchase-order API. The document ID is
the PO ID, so saving the same PO ID updates that PO record.

```sh
uv run --with-requirements backend/db/requirements.txt \
  python backend/db/save_purchase_order.py \
  --po-id PO-12345 --details-file /path/to/purchase-order-response.json
```

## Save an invoice and attach its purchase order

`save_invoice.py` reads `invoice_number` and `purchase_order` from an invoice
response JSON, queries `purchase_orders` for the matching `po_id`, and writes
the invoice to `invoices`. The record includes `invoice_id`, `po_id`, the full
`invoice_details`, `po_available`, `message`, and `po_details` (or `{}` when
the PO query finds no match). The invoice ID is sanitized for the Firestore
document path while the original ID is kept in the `invoice_id` field.

```sh
uv run --with-requirements backend/db/requirements.txt \
  python backend/db/save_invoice.py \
  --details-file /path/to/invoice-response.json
```
