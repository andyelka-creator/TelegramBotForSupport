import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.tasks import TaskRepository
from app.schemas.common import TaskType
from app.services.invite_service import InviteError, InviteService


async def test_invite_token_single_use(session):
    task = await TaskRepository(session).create_task(TaskType.ISSUE_NEW, created_by=1)
    await session.commit()

    service = InviteService(InviteTokenRepository(session))
    token = await service.create_token(task.id, expires_hours=1)
    await session.commit()

    invite = await service.use_token(str(token))
    assert invite.used_at is not None
    await session.commit()

    with pytest.raises(InviteError):
        await service.validate_token(str(token))


async def test_invite_token_expired(session):
    task = await TaskRepository(session).create_task(TaskType.ISSUE_NEW, created_by=1)
    invite_repo = InviteTokenRepository(session)
    invite = await invite_repo.create(task.id, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    await session.commit()

    service = InviteService(invite_repo)
    with pytest.raises(InviteError):
        await service.validate_token(str(uuid.UUID(str(invite.token))))
