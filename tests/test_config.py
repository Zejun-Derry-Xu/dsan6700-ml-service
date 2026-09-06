"""Tests for application configuration."""

import pytest
from pydantic import ValidationError

from dsan6700_ml_service.config import Settings


def test_invalid_app_env_is_rejected() -> None:
    """An invalid application environment should fail validation."""
    with pytest.raises(ValidationError):
        Settings(app_env="banana")
