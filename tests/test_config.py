"""Tests for application configuration."""

import math

import pytest
from pydantic import ValidationError

from dsan6700_ml_service.config import Settings


def test_default_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default settings should be valid."""
    monkeypatch.chdir("/")
    settings = Settings(_env_file=None)

    assert settings.model_path == "artifacts/iris.joblib"
    assert settings.inference_delay_seconds == 0.0


def test_valid_configuration() -> None:
    """Valid model paths and delays should be accepted."""
    settings = Settings(
        model_path="models/custom.joblib",
        inference_delay_seconds=2.0,
    )

    assert settings.model_path == "models/custom.joblib"
    assert settings.inference_delay_seconds == 2.0


@pytest.mark.parametrize("path", ["", " ", "   ", "\t\n"])
def test_invalid_model_path(path: str) -> None:
    """Empty or whitespace-only model paths must be rejected."""
    with pytest.raises(ValidationError):
        Settings(model_path=path)


@pytest.mark.parametrize(
    "delay",
    [-1.0, -0.5, math.nan, math.inf, -math.inf],
)
def test_invalid_inference_delay(delay: float) -> None:
    """Negative and non-finite inference delays must be rejected."""
    with pytest.raises(ValidationError):
        Settings(inference_delay_seconds=delay)


@pytest.mark.parametrize("delay", [0.0, 0.5, 2.0])
def test_valid_inference_delay(delay: float) -> None:
    """Finite, non-negative delays should be accepted."""
    settings = Settings(inference_delay_seconds=delay)
    assert settings.inference_delay_seconds == delay


def test_invalid_app_env_is_rejected() -> None:
    """An invalid application environment should fail validation."""
    with pytest.raises(ValidationError):
        Settings(app_env="banana")


def test_invalid_log_level_is_rejected() -> None:
    """An invalid log level should fail validation."""
    with pytest.raises(ValidationError):
        Settings(log_level="VERBOSE")


@pytest.mark.parametrize("name", ["", "   "])
def test_invalid_app_name(name: str) -> None:
    """Empty application names must be rejected."""
    with pytest.raises(ValidationError):
        Settings(app_name=name)


def test_env_file_loading(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load configuration from a .env file."""
    monkeypatch.delenv("MODEL_PATH", raising=False)
    monkeypatch.delenv("INFERENCE_DELAY_SECONDS", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "MODEL_PATH=models/from-env.joblib\nINFERENCE_DELAY_SECONDS=1.5\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.model_path == "models/from-env.joblib"
    assert settings.inference_delay_seconds == 1.5


def test_environment_overrides_env_file(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Environment variables should override values in .env."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "MODEL_PATH=models/from-file.joblib\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("MODEL_PATH", "models/from-environment.joblib")

    settings = Settings(_env_file=env_file)

    assert settings.model_path == "models/from-environment.joblib"
