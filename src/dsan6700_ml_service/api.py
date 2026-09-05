from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: Literal["healthy"]


app = FastAPI(
    title="DSAN 6700 ML Service",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return the current health status of the service."""
    return HealthResponse(status="healthy")
