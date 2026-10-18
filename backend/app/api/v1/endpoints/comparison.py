"""Invoice and purchase order comparison endpoint."""

from typing import Any

import asyncio
import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict

from document_ai.config import get_settings
from document_ai.root_agent import RootAgentError, compare_documents

router = APIRouter(prefix="/documents", tags=["documents"])


class CompareDocumentsRequest(BaseModel):
    """Compact extraction results returned by the document processing routes."""

    model_config = ConfigDict(extra="forbid")

    invoice: dict[str, Any]
    purchase_order: dict[str, Any]


@router.post(
    "/compare",
    summary="Compare processed invoice and purchase order data",
    description=(
        "Sends the compact invoice and purchase order JSON objects to the configured "
        "root agent and returns its discrepancy analysis."
    ),
)
async def compare_invoice_and_purchase_order(
    request: CompareDocumentsRequest,
) -> dict[str, str]:
    settings = get_settings()
    if not settings.root_agent_url.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ROOT_AGENT_URL is not configured.",
        )

    try:
        return await compare_documents(
            settings.root_agent_url,
            request.invoice,
            request.purchase_order,
        )
    except RootAgentError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The root agent could not compare these documents.",
        ) from error


@router.post(
    "/compare/stream",
    summary="Stream an invoice and purchase order comparison",
)
async def stream_invoice_and_purchase_order_comparison(
    request: CompareDocumentsRequest,
) -> StreamingResponse:
    """Return the agent analysis as server-sent events once it is available."""
    settings = get_settings()
    if not settings.root_agent_url.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ROOT_AGENT_URL is not configured.",
        )

    async def events():
        try:
            result = await compare_documents(
                settings.root_agent_url, request.invoice, request.purchase_order
            )
            analysis = result["analysis"]
            # Keep SSE frame boundaries separate from the readable text chunks.
            for start in range(0, len(analysis), 48):
                chunk = analysis[start : start + 48]
                yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)
            yield "event: done\ndata: {}\n\n"
        except RootAgentError:
            yield f"event: error\ndata: {json.dumps({'detail': 'The root agent could not compare these documents.'})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
