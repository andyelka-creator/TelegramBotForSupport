import os
import re
import time

import pytest


def _env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing env: {name}")
    return value


async def _wait_for_message(client, entity, pattern: str, after_id: int, timeout_sec: int = 60):
    deadline = time.time() + timeout_sec
    rx = re.compile(pattern, re.IGNORECASE | re.DOTALL)
    while time.time() < deadline:
        async for message in client.iter_messages(entity, limit=30):
            if message.id <= after_id:
                break
            text = message.message or ""
            match = rx.search(text)
            if match:
                return message, match
        await client.send_read_acknowledge(entity)
        await __import__("asyncio").sleep(1)
    raise AssertionError(f"Timeout waiting for pattern: {pattern}")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_telegram_issue_new_flow_e2e():
    if os.getenv("E2E_ENABLE", "0") != "1":
        pytest.skip("Set E2E_ENABLE=1 to run Telegram e2e tests")

    telethon = pytest.importorskip("telethon")
    StringSession = telethon.sessions.StringSession
    TelegramClient = telethon.TelegramClient

    api_id = int(_env("TELEGRAM_API_ID"))
    api_hash = _env("TELEGRAM_API_HASH")
    session_string = _env("E2E_TELEGRAM_SESSION")
    control_bot = _env("E2E_CONTROL_BOT_USERNAME").lstrip("@")
    intake_bot = _env("E2E_INTAKE_BOT_USERNAME").lstrip("@")

    async with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        control = await client.get_entity(control_bot)
        intake = await client.get_entity(intake_bot)

        unique_card_no = f"79{int(time.time())}"
        sent = await client.send_message(control, f"/vypusk {unique_card_no}")

        _, match = await _wait_for_message(
            client,
            control,
            r"https://t\.me/[a-zA-Z0-9_]+\?start=([0-9a-fA-F-]{36})",
            after_id=sent.id,
            timeout_sec=90,
        )
        token = match.group(1)

        start_msg = await client.send_message(intake, f"/start {token}")
        await _wait_for_message(client, intake, r"Введите фамилию", after_id=start_msg.id, timeout_sec=60)

        answers = [
            "Иванов",
            "Иван",
            "Иванович",
            "+79031234567",
            "-",
        ]
        for answer in answers:
            await client.send_message(intake, answer)

        await _wait_for_message(client, intake, r"Спасибо\. Анкета отправлена\.", after_id=start_msg.id, timeout_sec=90)
