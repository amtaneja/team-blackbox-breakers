"""FastAPI application entry point."""
# required imports 
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# importing router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.comparison import router as comparison_router
from app.api.v1.endpoints.inference import router as inference_router
# Creating the app for our application
app = FastAPI(
    title="Auditly",
    description="Fastapi application for auditly your smart auditing agent.",
    version="1.0.0",
)
allowed_origins = os.getenv(
    "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins.split(",") if origin.strip()],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
# Register document management endpoints under the v1 API prefix
app.include_router(documents_router, prefix="/api/v1")
app.include_router(comparison_router, prefix="/api/v1")
app.include_router(inference_router, prefix="/api/v1")

# health check endpoint
@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Basic liveness endpoint; does not call Google Cloud."""
    return {"status": "ok"}
