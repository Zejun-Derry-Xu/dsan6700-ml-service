"""Request and response schemas for model predictions."""

from pydantic import BaseModel


class PredictRequest(BaseModel):
    """Measurements supplied for Iris classification."""

    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

    def to_features(self) -> list[float]:
        """Return measurements in the model's training order."""
        return [
            self.sepal_length,
            self.sepal_width,
            self.petal_length,
            self.petal_width,
        ]


class PredictResponse(BaseModel):
    """Classification returned by the model."""

    class_id: int
    class_name: str
