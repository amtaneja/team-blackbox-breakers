"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.endpoints.documents import router as documents_router

app = FastAPI(
    title="Document AI API",
    description="Upload a PDF and receive Google Cloud Document AI's JSON result.",
    version="1.0.0",
)
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Basic liveness endpoint; does not call Google Cloud."""
    return {"status": "ok"}
