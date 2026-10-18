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


@router.post(
    "/process",
    summary="Process an uploaded PDF",
    description=(
        "Uploads a PDF to the configured Google Cloud Document AI processor and "
        "returns its Document resource as JSON. Google Cloud ADC must be set up."
    ),
)
async def process_document(file: UploadFile = File(...)) -> dict:
    settings = get_settings()
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a PDF file (application/pdf).",
        )

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

    try:
        return await run_in_threadpool(process_pdf, content, settings)
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
