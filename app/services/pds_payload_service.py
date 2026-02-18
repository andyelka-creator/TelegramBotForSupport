import uuid
from datetime import datetime

from app.schemas.common import TaskType
from app.services.validation_service import (
    normalize_amount_rub,
    normalize_card_no,
    normalize_email,
    normalize_payer_name,
    normalize_payment_id,
    normalize_phone,
)


class PayloadError(ValueError):
    pass


def _clean(value):
    if isinstance(value, dict):
        out = {}
        for key in sorted(value.keys()):
            item = _clean(value[key])
            if item is not None:
                out[key] = item
        return out
    if isinstance(value, list):
        cleaned = []
        for v in value:
            item = _clean(v)
            if item is not None:
                cleaned.append(item)
        return cleaned
    if value is None:
        return None
    return value


class PDSPayloadService:
    schema = 'pds-assist-v1'

    def build_payload(self, *, task_id: uuid.UUID, task_type: TaskType, created_at: datetime, data: dict) -> dict:
        base = {
            'schema': self.schema,
            'task_id': str(task_id),
            'operation': task_type.value,
            'created_at': created_at.isoformat(),
            'operator_notes': [],
            'ui_hints': {},
            'operator_confirm_required': True,
            'helper_target': 'ahk-v1',
        }

        if task_type == TaskType.ISSUE_NEW:
            payload = {
                **base,
                'card_no': normalize_card_no(data['card_no']),
                'guest': {
                    'last_name': data['last_name'],
                    'first_name': data['first_name'],
                    'middle_name': data.get('middle_name'),
                    'phone': normalize_phone(data['phone']),
                    'email': normalize_email(data.get('email')),
                },
            }
        elif task_type == TaskType.REPLACE_DAMAGED:
            payload = {
                **base,
                'old_card_no': normalize_card_no(data['old_card_no']),
                'new_card_no': normalize_card_no(data['new_card_no']),
                'attachments': {'damaged_photos': [str(x) for x in data.get('damaged_photos', [])]},
            }
        elif task_type == TaskType.TOPUP:
            payload = {
                **base,
                'card_no': normalize_card_no(data['card_no']),
                'amount_rub': normalize_amount_rub(data['amount_rub']),
                'payment_id': normalize_payment_id(data['payment_id']),
                'payer_name': normalize_payer_name(data['payer_name']),
            }
        else:
            raise PayloadError(f'Unsupported task type: {task_type}')

        return _clean(payload)

    def build_steps(self, task_type: TaskType, data: dict) -> str:
        if task_type == TaskType.ISSUE_NEW:
            steps = [
                '1) Open UCS PDS',
                '2) Navigate to Cards module',
                '3) Click Create',
                f"4) Enter Last Name: {data.get('last_name', '')}",
                f"5) Enter First Name: {data.get('first_name', '')}",
                '6) Switch to Card tab',
                f"7) Enter Card No: {data.get('card_no', '')}",
                '8) Verify fields manually',
                '9) Click Save',
            ]
        elif task_type == TaskType.REPLACE_DAMAGED:
            steps = [
                '1) Open UCS PDS',
                '2) Navigate to Cards module',
                '3) Open Replace / Reissue card workflow',
                f"4) Enter Old Card No: {data.get('old_card_no', '')}",
                f"5) Enter New Card No: {data.get('new_card_no', '')}",
                '6) Attach damaged card evidence (if required)',
                '7) Verify fields manually',
                '8) Click Save',
            ]
        elif task_type == TaskType.TOPUP:
            steps = [
                '1) Open UCS PDS',
                '2) Navigate to Balance / Top-up module',
                f"3) Enter Card No: {data.get('card_no', '')}",
                f"4) Enter Amount RUB: {data.get('amount_rub', '')}",
                f"5) Enter Payment ID: {data.get('payment_id', '')}",
                f"6) Enter Payer Name: {data.get('payer_name', '')}",
                '7) Verify fields manually',
                '8) Click Save',
            ]
        else:
            raise PayloadError(f'Unsupported task type: {task_type}')

        return '\n'.join(steps)
