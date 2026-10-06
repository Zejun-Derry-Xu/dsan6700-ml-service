"""HTTP endpoints, application startup, and synchronous prediction."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import sleep
from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from dsan6700_ml_service.config import Settings
from dsan6700_ml_service.model_client import IrisModelClient, ModelClient
from dsan6700_ml_service.schemas import PredictRequest, PredictResponse


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: Literal["healthy"]


def create_app(model_client: ModelClient | None = None) -> FastAPI:
    """Create an application with a real or injected model client."""
    active_client: ModelClient | None = None
    active_delay = 0.0

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        nonlocal active_client, active_delay
        settings = Settings()
        active_delay = settings.inference_delay_seconds
        application.title = settings.app_name
        active_client = (
            model_client
            if model_client is not None
            else IrisModelClient(settings.model_path)
        )
        try:
            yield
        finally:
            active_client = None

    application = FastAPI(
        title="DSAN 6700 ML Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    def get_model_client() -> ModelClient:
        if active_client is None:
            raise RuntimeError("Model client is not initialized")
        return active_client

    @application.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="healthy")

    @application.post("/predict", response_model=PredictResponse)
    def predict(
        payload: PredictRequest,
        client: Annotated[ModelClient, Depends(get_model_client)],
    ) -> PredictResponse:
        # Run synchronous inference in FastAPI's worker thread pool.
        sleep(active_delay)
        return client.predict(payload)

    return application


app = create_app()
