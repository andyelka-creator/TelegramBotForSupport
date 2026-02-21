import re

PHONE_RE = re.compile(r"\D+")


class ValidationError(ValueError):
    pass


def normalize_phone(raw: str) -> str:
    digits = PHONE_RE.sub("", (raw or "").strip())
    if len(digits) == 11 and digits[0] in {"7", "8"}:
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    raise ValidationError("Invalid phone format")


def normalize_email(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = raw.strip().lower()
    return cleaned or None


def normalize_card_no(raw: object) -> str:
    card_no = str(raw).strip()
    if not card_no:
        raise ValidationError("card_no is required")
    return card_no


def normalize_amount_rub(raw: object) -> int:
    if isinstance(raw, bool):
        raise ValidationError("amount_rub must be integer")
    if not isinstance(raw, (int, str)):
        raise ValidationError("amount_rub must be integer")
    try:
        amount = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError("amount_rub must be integer") from exc
    if amount <= 0:
        raise ValidationError("amount_rub must be > 0")
    return amount


def normalize_payment_id(raw: str) -> str:
    cleaned = (raw or "").strip()
    if not cleaned or len(cleaned) > 64:
        raise ValidationError("payment_id length must be 1..64")
    return cleaned


def normalize_payer_name(raw: str) -> str:
    cleaned = (raw or "").strip()
    if not cleaned or len(cleaned) > 128:
        raise ValidationError("payer_name length must be 1..128")
    return cleaned
