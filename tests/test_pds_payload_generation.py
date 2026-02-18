import json
import uuid
from datetime import datetime, timezone

from app.schemas.common import TaskType
from app.services.pds_payload_service import PDSPayloadService


def test_pds_issue_payload_generation():
    service = PDSPayloadService()
    payload = service.build_payload(
        task_id=uuid.uuid4(),
        task_type=TaskType.ISSUE_NEW,
        created_at=datetime.now(timezone.utc),
        data={
            'card_no': 1,
            'last_name': 'Ivanov',
            'first_name': 'Ivan',
            'middle_name': None,
            'phone': '8 (900) 123-45-67',
            'email': '  IVANOV@EXAMPLE.COM ',
        },
    )

    dumped = json.dumps(payload, sort_keys=True)
    assert payload['schema'] == 'pds-assist-v1'
    assert payload['card_no'] == '1'
    assert payload['guest']['phone'] == '+79001234567'
    assert payload['guest']['email'] == 'ivanov@example.com'
    assert payload['operator_confirm_required'] is True
    assert payload['helper_target'] == 'ahk-v1'
    assert payload['ui_hints'] == {}
    assert 'middle_name' not in payload['guest']
    assert 'null' not in dumped


def test_replace_payload_keeps_damaged_photo_file_ids():
    service = PDSPayloadService()
    payload = service.build_payload(
        task_id=uuid.uuid4(),
        task_type=TaskType.REPLACE_DAMAGED,
        created_at=datetime.now(timezone.utc),
        data={
            'old_card_no': '001',
            'new_card_no': '045',
            'damaged_photos': ['AgACAgIAAxkBAAIBQmY_file_1', 'AgACAgIAAxkBAAIBQmY_file_2'],
        },
    )

    assert payload['attachments']['damaged_photos'] == ['AgACAgIAAxkBAAIBQmY_file_1', 'AgACAgIAAxkBAAIBQmY_file_2']
