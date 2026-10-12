"""Tests for configuration validation during application startup."""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from dsan6700_ml_service.api import create_app
from dsan6700_ml_service.schemas import PredictRequest, PredictResponse


class FakeModelClient:
    """A fake model client that avoids loading a real model."""

    def predict(self, payload: PredictRequest) -> PredictResponse:
        """Return a fixed prediction for testing."""
        return PredictResponse(class_id=0, class_name="setosa")


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("MODEL_PATH", ""),
        ("MODEL_PATH", "   "),
        ("INFERENCE_DELAY_SECONDS", "-1"),
        ("INFERENCE_DELAY_SECONDS", "nan"),
        ("INFERENCE_DELAY_SECONDS", "inf"),
        ("INFERENCE_DELAY_SECONDS", "-inf"),
        ("APP_ENV", "banana"),
        ("LOG_LEVEL", "VERBOSE"),
        ("APP_NAME", "   "),
    ],
)
def test_invalid_settings_prevent_startup(
    monkeypatch: pytest.MonkeyPatch,
    variable: str,
    value: str,
) -> None:
    """Invalid environment settings must prevent app startup."""
    monkeypatch.setenv(variable, value)

    app = create_app(model_client=FakeModelClient())

    with pytest.raises(ValidationError):
        with TestClient(app):
            pytest.fail("Application unexpectedly started")


def test_valid_settings_allow_startup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid settings should allow startup with a fake model."""
    monkeypatch.setenv("MODEL_PATH", "models/example.joblib")
    monkeypatch.setenv("INFERENCE_DELAY_SECONDS", "0")
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("APP_NAME", "Iris Test Service")

    app = create_app(model_client=FakeModelClient())

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

        assert app.title == "Iris Test Service"
