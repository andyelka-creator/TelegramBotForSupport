import pytest

from app.bots.handlers.common import resolve_actor_by_telegram_id
from app.config import settings
from app.repositories.users import UserRepository
from app.schemas.common import Role

pytestmark = pytest.mark.integration


async def test_owner_auto_bootstrap_to_admin(session, monkeypatch):
    monkeypatch.setattr(settings, 'owner_telegram_id', 999999)

    actor = await resolve_actor_by_telegram_id(session, 999999)
    assert actor is not None
    assert actor.role == Role.ADMIN

    saved = await UserRepository(session).get_by_telegram_id(999999)
    assert saved is not None
    assert saved.role == Role.ADMIN


async def test_non_owner_without_record_is_denied(session, monkeypatch):
    monkeypatch.setattr(settings, 'owner_telegram_id', 999999)
    actor = await resolve_actor_by_telegram_id(session, 777777)
    assert actor is None


async def test_revoke_via_repository_delete(session):
    repo = UserRepository(session)
    created = await repo.create(telegram_id=333333, role=Role.SYSADMIN)
    await session.commit()
    assert created.id is not None

    deleted = await repo.delete_by_telegram_id(333333)
    await session.commit()
    assert deleted is True
    assert await repo.get_by_telegram_id(333333) is None
