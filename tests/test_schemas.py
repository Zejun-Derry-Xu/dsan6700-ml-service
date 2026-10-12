"""Validation tests for prediction request schemas."""

import math
from typing import Any

import pytest
from pydantic import ValidationError

from dsan6700_ml_service.schemas import PredictRequest

FIELDS = ["sepal_length", "sepal_width", "petal_length", "petal_width"]

VALID_PAYLOAD: dict[str, Any] = {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2,
}


def assert_single_error(
    exc_info: pytest.ExceptionInfo[ValidationError],
    loc: tuple[str, ...],
    error_type: str,
) -> None:
    """Check that validation failed only for the expected field and reason."""
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["loc"] == loc
    assert errors[0]["type"] == error_type


def test_valid_floats_create_request() -> None:
    """Valid floating-point measurements should be accepted."""
    request = PredictRequest(**VALID_PAYLOAD)

    assert request.sepal_length == 5.1
    assert request.sepal_width == 3.5
    assert request.petal_length == 1.4
    assert request.petal_width == 0.2


def test_valid_integers_create_request() -> None:
    """Valid integer measurements should still be accepted."""
    request = PredictRequest(
        sepal_length=6,
        sepal_width=3,
        petal_length=5,
        petal_width=2,
    )

    assert request.to_features() == [6.0, 3.0, 5.0, 2.0]


@pytest.mark.parametrize("value", [1e-9, 0.1, 100.0, 1e6])
def test_small_and_large_positive_values_are_accepted(value: float) -> None:
    """Any finite positive value should be accepted, with no upper limit."""
    request = PredictRequest(**dict.fromkeys(FIELDS, value))

    assert request.to_features() == [value] * 4


def test_to_features_preserves_training_order() -> None:
    """Features should follow the order used to train the model."""
    request = PredictRequest(
        sepal_length=1.0,
        sepal_width=2.0,
        petal_length=3.0,
        petal_width=4.0,
    )

    assert request.to_features() == [1.0, 2.0, 3.0, 4.0]


def test_fields_describe_units() -> None:
    """Each measurement should document its unit in centimeters."""
    for field in FIELDS:
        description = PredictRequest.model_fields[field].description
        assert description is not None
        assert "centimeters" in description


@pytest.mark.parametrize("field", FIELDS)
def test_missing_measurement_is_rejected(field: str) -> None:
    """Every measurement is required."""
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != field}

    with pytest.raises(ValidationError) as exc_info:
        PredictRequest.model_validate(payload)

    assert_single_error(exc_info, (field,), "missing")


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [0, 0.0, -0.0])
def test_zero_measurement_is_rejected(field: str, value: float) -> None:
    """Measurements must be greater than zero."""
    with pytest.raises(ValidationError) as exc_info:
        PredictRequest.model_validate({**VALID_PAYLOAD, field: value})

    assert_single_error(exc_info, (field,), "greater_than")


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [-1, -0.1, -1e6])
def test_negative_measurement_is_rejected(field: str, value: float) -> None:
    """Negative measurements must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        PredictRequest.model_validate({**VALID_PAYLOAD, field: value})

    assert_single_error(exc_info, (field,), "greater_than")


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", ["abc", "", "five"])
def test_nonnumeric_string_is_rejected(field: str, value: str) -> None:
    """Strings that are not numbers must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        PredictRequest.model_validate({**VALID_PAYLOAD, field: value})

    assert_single_error(exc_info, (field,), "float_parsing")


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_measurement_is_rejected(field: str, value: float) -> None:
    """NaN and positive or negative infinity must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        PredictRequest.model_validate({**VALID_PAYLOAD, field: value})

    assert_single_error(exc_info, (field,), "finite_number")


@pytest.mark.parametrize("extra_field", ["species", "petal_colour", "debug"])
def test_unexpected_field_is_rejected(extra_field: str) -> None:
    """Fields outside the schema must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        PredictRequest.model_validate({**VALID_PAYLOAD, extra_field: 1.0})

    assert_single_error(exc_info, (extra_field,), "extra_forbidden")


@pytest.mark.parametrize(
    ("field", "misspelling"),
    [
        ("sepal_length", "sepal_lenght"),
        ("sepal_width", "sepalWidth"),
        ("petal_length", "petal-length"),
        ("petal_width", "Petal_Width"),
    ],
)
def test_misspelled_field_is_rejected(field: str, misspelling: str) -> None:
    """A misspelled field is rejected as unexpected and the real one as missing."""
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != field}
    payload[misspelling] = VALID_PAYLOAD[field]

    with pytest.raises(ValidationError) as exc_info:
        PredictRequest.model_validate(payload)

    errors = {(error["loc"], error["type"]) for error in exc_info.value.errors()}
    assert errors == {((field,), "missing"), ((misspelling,), "extra_forbidden")}
