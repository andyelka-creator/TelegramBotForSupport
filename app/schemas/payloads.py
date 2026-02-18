from pydantic import BaseModel, EmailStr, Field, field_validator


class IssueNewForm(BaseModel):
    card_no: str
    last_name: str
    first_name: str
    middle_name: str | None = None
    phone: str
    email: EmailStr | None = None


class ReplaceDamagedForm(BaseModel):
    old_card_no: str
    new_card_no: str
    damaged_card_photo: str
    last_name: str | None = None
    first_name: str | None = None
    middle_name: str | None = None


class TopupForm(BaseModel):
    card_no: str
    amount_rub: int = Field(gt=0)
    payment_id: str
    payer_name: str

    @field_validator('card_no', mode='before')
    @classmethod
    def card_is_string(cls, value: object) -> str:
        return str(value)
