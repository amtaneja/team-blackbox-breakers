"""Document upload and processing endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from document_ai.config import get_settings
from document_ai.service import (
    DocumentAIConfigurationError,
    is_document_ai_error,
    process_pdf,
)

router = APIRouter(prefix="/documents", tags=["documents"])


async def _process_upload(file: UploadFile, document_type: str) -> dict:
    settings = get_settings()
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a PDF file (application/pdf).",
        )

    try:
        content = await file.read(settings.max_upload_size_bytes + 1)
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    "PDF exceeds the upload limit of "
                    f"{settings.max_upload_size_bytes} bytes."
                ),
            )
        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded file does not have a valid PDF header.",
            )

        return await run_in_threadpool(process_pdf, content, settings, document_type)
    except DocumentAIConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except Exception as error:
        if is_document_ai_error(error):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google Document AI could not process this PDF.",
            ) from error
        raise
    finally:
        await file.close()


@router.post(
    "/invoice/process",
    summary="Process an uploaded invoice PDF",
    description=(
        "Uploads an invoice PDF to the configured Google Cloud Document AI "
        "invoice processor. Google Cloud ADC must be set up."
    ),
)
async def process_invoice(file: UploadFile = File(...)) -> dict:
    return await _process_upload(file, "invoice")


@router.post(
    "/purchase-order/process",
    summary="Process an uploaded purchase order PDF",
    description=(
        "Uploads a purchase order PDF to the configured Google Cloud Document "
        "AI purchase order processor. Google Cloud ADC must be set up."
    ),
)
async def process_purchase_order(file: UploadFile = File(...)) -> dict:
    return await _process_upload(file, "purchase_order")
