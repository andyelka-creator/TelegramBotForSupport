from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.invite_tokens import InviteTokenRepository
from app.repositories.tasks import TaskRepository
from app.schemas.common import TaskType
from app.services.invite_service import InviteError, InviteService
from app.services.task_service import TaskService

pytestmark = pytest.mark.integration


async def test_invite_token_created_for_issue_new(session):
    service = TaskService(session)
    result = await service.create_task_with_invite(TaskType.ISSUE_NEW, actor_id=1, initial_data={'card_no': '001'})

    assert result.invite_token is not None
    invite = await InviteTokenRepository(session).get_by_token(result.invite_token)
    assert invite is not None
    assert invite.used_at is None


async def test_token_not_created_for_topup(session):
    service = TaskService(session)
    result = await service.create_task_with_invite(TaskType.TOPUP, actor_id=1, initial_data={'card_no': '001'})

    assert result.invite_token is None
    latest = await InviteTokenRepository(session).get_latest_by_task_id(result.task_id)
    assert latest is None


async def test_token_validation_expired(session):
    task = await TaskRepository(session).create_task(TaskType.ISSUE_NEW, created_by=1)
    repo = InviteTokenRepository(session)
    invite = await repo.create(task.id, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    await session.commit()

    with pytest.raises(InviteError):
        await InviteService(repo).validate_token(str(invite.token))


async def test_token_one_time_usage(session):
    task = await TaskRepository(session).create_task(TaskType.ISSUE_NEW, created_by=1)
    service = InviteService(InviteTokenRepository(session))
    invite = await service.create_token(task.id, expires_hours=1)
    await session.commit()

    used = await service.use_token(str(invite.token))
    assert used.used_at is not None
    await session.commit()

    with pytest.raises(InviteError):
        await service.validate_token(str(invite.token))


async def test_regenerate_token_invalidates_previous(session):
    task_service = TaskService(session)
    created = await task_service.create_task_with_invite(TaskType.ISSUE_NEW, actor_id=1, initial_data={'card_no': '001'})
    old_token = created.invite_token
    assert old_token is not None

    new_token = await task_service.regenerate_invite(created.task_id, actor_id=1, expires_hours=24)
    assert new_token != old_token

    invite_service = InviteService(InviteTokenRepository(session))
    with pytest.raises(InviteError):
        await invite_service.validate_token(str(old_token))

    latest = await invite_service.validate_token(str(new_token))
    assert latest.used_at is None
