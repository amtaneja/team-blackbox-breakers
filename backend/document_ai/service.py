"""Google Cloud Document AI integration."""

from dataclasses import dataclass

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPIError
from google.cloud import documentai
from google.protobuf.json_format import MessageToDict

from document_ai.config import Settings


class DocumentAIConfigurationError(Exception):
    """Raised when the Document AI processor is not configured."""


@dataclass(frozen=True)
class ProcessorConfig:
    """Configuration for one Document AI processor."""

    location: str
    processor_id: str
    processor_version_id: str | None
    field_mask: str | None


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


def _compact_purchase_order(document: dict) -> dict:
    """Return readable purchase order entities without OCR/layout metadata."""
    fields: dict[str, str | None] = {}
    line_items: list[dict] = []
    for entity in document.get("entities", []):
        entity_type = entity.get("type", "")
        if entity_type == "line_item":
            item = {}
            for prop in entity.get("properties", []):
                name = prop.get("type", "").removeprefix("line_item/")
                if name:
                    item[name] = _entity_value(prop)
            line_items.append(item)
        elif entity_type:
            fields[entity_type] = _entity_value(entity)
    return {"fields": fields, "line_items": line_items}


def _processor_config(settings: Settings, document_type: str) -> ProcessorConfig:
    if document_type == "invoice":
        return ProcessorConfig(
            settings.invoice_documentai_location,
            settings.invoice_documentai_processor_id,
            settings.invoice_documentai_processor_version_id,
            settings.invoice_documentai_field_mask,
        )
    if document_type == "purchase_order":
        return ProcessorConfig(
            settings.po_documentai_location,
            settings.po_documentai_processor_id,
            settings.po_documentai_processor_version_id,
            settings.po_documentai_field_mask,
        )
    raise ValueError(f"Unsupported document type: {document_type}")


class DocumentAIProcessor:
    """Shared client and request handling for configured Document AI processors."""

    def __init__(self, settings: Settings, document_type: str):
        self.settings = settings
        self.document_type = document_type
        self.config = _processor_config(settings, document_type)

    def process(self, content: bytes) -> dict:
        """Process PDF bytes and return a compact result for this document type."""
        config = self.config
        missing = []
        env_prefix = "INVOICE" if self.document_type == "invoice" else "PO"
        if not self.settings.google_cloud_project.strip():
            missing.append("GOOGLE_CLOUD_PROJECT")
        if not config.location.strip():
            missing.append(f"{env_prefix}_DOCUMENTAI_LOCATION")
        if not config.processor_id.strip():
            missing.append(f"{env_prefix}_DOCUMENTAI_PROCESSOR_ID")
        if missing:
            raise DocumentAIConfigurationError(
                "Missing configuration: " + ", ".join(missing)
            )

        client = documentai.DocumentProcessorServiceClient(
            client_options=ClientOptions(
                api_endpoint=f"{config.location}-documentai.googleapis.com"
            )
        )
        if config.processor_version_id:
            processor_name = client.processor_version_path(
                self.settings.google_cloud_project,
                config.location,
                config.processor_id,
                config.processor_version_id,
            )
        else:
            processor_name = client.processor_path(
                self.settings.google_cloud_project,
                config.location,
                config.processor_id,
            )

        request = documentai.ProcessRequest(
            name=processor_name,
            raw_document=documentai.RawDocument(
                content=content,
                mime_type="application/pdf",
            ),
            field_mask=config.field_mask or None,
        )
        result = client.process_document(request=request)
        document = MessageToDict(
            result.document._pb,
            preserving_proto_field_name=False,
        )
        if self.document_type == "invoice":
            return _compact_invoice(document)
        return _compact_purchase_order(document)


def process_pdf(
    content: bytes,
    settings: Settings,
    document_type: str = "invoice",
) -> dict:
    """Process PDF bytes using the selected configured processor."""
    return DocumentAIProcessor(settings, document_type).process(content)


def is_document_ai_error(error: Exception) -> bool:
    """Return whether an exception came from a Google API request."""
    return isinstance(error, GoogleAPIError)
