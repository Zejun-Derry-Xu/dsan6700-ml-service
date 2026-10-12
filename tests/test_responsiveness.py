"""Check that slow inference does not block the health endpoint."""

import asyncio
from threading import Event

import httpx
import pytest

from dsan6700_ml_service.api import create_app
from dsan6700_ml_service.schemas import PredictRequest, PredictResponse


class ControlledSlowModel:
    """Hold inference until the test explicitly releases it."""

    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()

    def predict(self, request: PredictRequest) -> PredictResponse:
        self.started.set()
        if not self.release.wait(timeout=5.0):
            raise TimeoutError("The test did not release inference")
        return PredictResponse(class_id=0, class_name="setosa")


def test_health_responds_during_slow_prediction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INFERENCE_DELAY_SECONDS", "0")
    fake = ControlledSlowModel()
    application = create_app(model_client=fake)

    async def exercise() -> None:
        async with application.router.lifespan_context(application):
            transport = httpx.ASGITransport(app=application)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:
                prediction = asyncio.create_task(
                    client.post(
                        "/predict",
                        json={
                            "sepal_length": 5.1,
                            "sepal_width": 3.5,
                            "petal_length": 1.4,
                            "petal_width": 0.2,
                        },
                    )
                )
                try:
                    started = await asyncio.to_thread(fake.started.wait, 1.0)
                    assert started, "Prediction never started"
                    assert not prediction.done()

                    health = await asyncio.wait_for(client.get("/health"), timeout=1.0)
                    assert health.status_code == 200
                    assert health.json() == {"status": "healthy"}
                    assert not prediction.done()
                finally:
                    fake.release.set()
                    result = await asyncio.wait_for(prediction, timeout=2.0)

                assert result.status_code == 200
                assert result.json() == {
                    "class_id": 0,
                    "class_name": "setosa",
                }

    asyncio.run(exercise())
