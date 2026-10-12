"""Request and response schemas for model predictions."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# A finite measurement strictly greater than zero, with no upper limit.
Measurement = Annotated[float, Field(gt=0, allow_inf_nan=False)]


class PredictRequest(BaseModel):
    """Measurements supplied for Iris classification."""

    model_config = ConfigDict(extra="forbid")

    sepal_length: Measurement = Field(description="Sepal length in centimeters.")
    sepal_width: Measurement = Field(description="Sepal width in centimeters.")
    petal_length: Measurement = Field(description="Petal length in centimeters.")
    petal_width: Measurement = Field(description="Petal width in centimeters.")

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
