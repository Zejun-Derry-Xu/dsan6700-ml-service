from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from dsan6700_ml_service.config import Settings


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: Literal["healthy"]


settings = Settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return the current health status of the service."""
    return HealthResponse(status="healthy")
