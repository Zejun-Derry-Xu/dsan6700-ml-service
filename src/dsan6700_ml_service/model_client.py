"""Load the saved model and expose a prediction interface."""

from pathlib import Path
from typing import Any, Protocol

import joblib  # type: ignore[import-untyped]

from dsan6700_ml_service.schemas import PredictRequest, PredictResponse

EXPECTED_FEATURES = [
    "sepal_length",
    "sepal_width",
    "petal_length",
    "petal_width",
]


class ModelClient(Protocol):
    """Interface shared by real and fake model clients."""

    def predict(self, request: PredictRequest) -> PredictResponse: ...


class IrisModelClient:
    """Reuse a model loaded from a local artifact."""

    def __init__(self, model_path: str) -> None:
        path = Path(model_path)
        if not path.is_file():
            raise FileNotFoundError(f"Model file not found: {path}")

        artifact: dict[str, Any] = joblib.load(path)
        if artifact.get("format_version") != 1:
            raise ValueError("Unsupported model artifact format")
        if artifact.get("feature_names") != EXPECTED_FEATURES:
            raise ValueError("Model feature order does not match the API")

        self._model = artifact["model"]
        self._class_names: list[str] = artifact["class_names"]

    def predict(self, request: PredictRequest) -> PredictResponse:
        """Predict without loading or training the model again."""
        features = request.to_features()
        class_id = int(self._model.predict([features])[0])
        return PredictResponse(
            class_id=class_id,
            class_name=self._class_names[class_id],
        )
