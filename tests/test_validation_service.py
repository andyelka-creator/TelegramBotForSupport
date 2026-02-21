import pytest

from app.services.validation_service import ValidationError, normalize_phone

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ('raw', 'expected'),
    [
        ('8 (900) 123-45-67', '+79001234567'),
        ('+7 900 123 45 67', '+79001234567'),
        ('7-900-123-45-67', '+79001234567'),
        ('9001234567', '+79001234567'),
    ],
)
def test_phone_normalization_ok(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize('raw', ['123', '', '+1 555 111 2233'])
def test_phone_normalization_invalid(raw):
    with pytest.raises(ValidationError):
        normalize_phone(raw)
