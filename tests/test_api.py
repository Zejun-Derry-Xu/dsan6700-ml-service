"""API tests using an injected fake model client."""

import pytest
from fastapi.testclient import TestClient

from dsan6700_ml_service.api import create_app
from dsan6700_ml_service.schemas import PredictRequest, PredictResponse


class FakeModelClient:
    """Return a fixed result and record the input."""

    def __init__(self) -> None:
        self.requests: list[PredictRequest] = []

    def predict(self, request: PredictRequest) -> PredictResponse:
        self.requests.append(request)
        return PredictResponse(class_id=2, class_name="virginica")


def test_health_endpoint() -> None:
    application = create_app(model_client=FakeModelClient())
    with TestClient(application) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_predict_uses_fake_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MODEL_PATH", "missing-model-for-test.joblib")
    fake = FakeModelClient()
    application = create_app(model_client=fake)

    with TestClient(application) as client:
        response = client.post(
            "/predict",
            json={
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            },
        )

    assert response.status_code == 200
    assert response.json() == {"class_id": 2, "class_name": "virginica"}
    assert len(fake.requests) == 1
    assert fake.requests[0].to_features() == [5.1, 3.5, 1.4, 0.2]
