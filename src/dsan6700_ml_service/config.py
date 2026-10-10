"""Application configuration."""

import math
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DSAN 6700 ML Service"
    app_env: Literal["development", "testing", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_path: str = "artifacts/iris.joblib"
    inference_delay_seconds: float = 0.0

    @field_validator("app_name")
    @classmethod
    def validate_app_name(cls, value: str) -> str:
        """Reject an empty application name."""
        if not value.strip():
            raise ValueError("APP_NAME must not be empty")
        return value

    @field_validator("model_path")
    @classmethod
    def validate_model_path(cls, value: str) -> str:
        """Reject an empty or whitespace-only model path."""
        if not value.strip():
            raise ValueError("MODEL_PATH must not be empty")
        return value

    @field_validator("inference_delay_seconds")
    @classmethod
    def validate_inference_delay(cls, value: float) -> float:
        """Require a finite, non-negative inference delay."""
        if not math.isfinite(value):
            raise ValueError("INFERENCE_DELAY_SECONDS must be finite")
        if value < 0:
            raise ValueError("INFERENCE_DELAY_SECONDS must be non-negative")
        return value
