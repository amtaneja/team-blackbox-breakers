"""Google Cloud Document AI integration."""

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPIError
from google.cloud import documentai
from google.protobuf.json_format import MessageToDict

from document_ai.config import Settings


class DocumentAIConfigurationError(Exception):
    """Raised when the Document AI processor is not configured."""


def _entity_value(entity: dict | None) -> str | None:
    """Get an entity's readable value without returning layout metadata."""
    if not entity:
        return None
    value = entity.get("mentionText")
    if value:
        return value
    normalized = entity.get("normalizedValue", {})
    return normalized.get("text") or None


def _compact_invoice(document: dict) -> dict:
    """Keep invoice fields while dropping OCR text, anchors, and geometry."""
    entities = document.get("entities", [])
    fields = {
        entity.get("type"): entity
        for entity in entities
        if entity.get("type") != "line_item"
    }

    def value(entity_type: str) -> str | None:
        return _entity_value(fields.get(entity_type))

    line_items = []
    for entity in entities:
        if entity.get("type") != "line_item":
            continue
        properties = {
            prop.get("type", "").removeprefix("line_item/"): prop
            for prop in entity.get("properties", [])
        }
        line_items.append(
            {
                "description": _entity_value(properties.get("description")),
                "product_code": _entity_value(properties.get("product_code")),
                "quantity": _entity_value(properties.get("quantity")),
                "unit_price": _entity_value(properties.get("unit_price")),
                "amount": _entity_value(properties.get("amount")),
            }
        )

    currency = value("currency")
    if currency and not (len(currency) == 3 and currency.isalpha()):
        currency = None

    return {
        "invoice_number": value("invoice_id"),
        "invoice_date": value("invoice_date"),
        "supplier": {
            "name": value("supplier_name"),
            "tax_id": value("supplier_tax_id"),
            "address": value("supplier_address"),
        },
        "customer": {
            "name": value("receiver_name"),
            "tax_id": value("receiver_tax_id"),
            "address": value("receiver_address"),
        },
        "purchase_order": value("purchase_order"),
        "currency": currency,
        "net_amount": value("net_amount"),
        "tax_amount": value("total_tax_amount"),
        "total_amount": value("total_amount"),
        "line_items": line_items,
    }


def process_pdf(content: bytes, settings: Settings) -> dict:
    """Process PDF bytes and return a compact invoice JSON summary."""
    missing = [
        name
        for name, value in (
            ("GOOGLE_CLOUD_PROJECT", settings.google_cloud_project),
            ("DOCUMENTAI_LOCATION", settings.documentai_location),
            ("DOCUMENTAI_PROCESSOR_ID", settings.documentai_processor_id),
        )
        if not value.strip()
    ]
    if missing:
        raise DocumentAIConfigurationError(
            "Missing configuration: " + ", ".join(missing)
        )

    client = documentai.DocumentProcessorServiceClient(
        client_options=ClientOptions(
            api_endpoint=(
                f"{settings.documentai_location}-documentai.googleapis.com"
            )
        )
    )
    if settings.documentai_processor_version_id:
        processor_name = client.processor_version_path(
            settings.google_cloud_project,
            settings.documentai_location,
            settings.documentai_processor_id,
            settings.documentai_processor_version_id,
        )
    else:
        processor_name = client.processor_path(
            settings.google_cloud_project,
            settings.documentai_location,
            settings.documentai_processor_id,
        )

    request = documentai.ProcessRequest(
        name=processor_name,
        raw_document=documentai.RawDocument(
            content=content,
            mime_type="application/pdf",
        ),
        field_mask=settings.documentai_field_mask or None,
    )
    result = client.process_document(request=request)
    document = MessageToDict(
        result.document._pb,
        preserving_proto_field_name=False,
    )
    return _compact_invoice(document)


def is_document_ai_error(error: Exception) -> bool:
    """Return whether an exception came from a Google API request."""
    return isinstance(error, GoogleAPIError)
