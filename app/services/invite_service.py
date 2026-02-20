import uuid
from datetime import datetime, timedelta, timezone

from app.db.models.invite_token import InviteToken
from app.repositories.invite_tokens import InviteTokenRepository


class InviteError(ValueError):
    pass


class InviteService:
    def __init__(self, repo: InviteTokenRepository):
        self.repo = repo

    async def create_token(self, task_id: uuid.UUID, expires_hours: int = 24) -> InviteToken:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        return await self.repo.create(task_id=task_id, expires_at=expires_at)

    async def validate_token(self, token: str) -> InviteToken:
        try:
            token_uuid = uuid.UUID(token)
        except ValueError as exc:
            raise InviteError('Invalid token format') from exc

        invite = await self.repo.get_by_token(token_uuid)
        if invite is None:
            raise InviteError('Token not found')

        now = datetime.now(timezone.utc)
        expires_at = invite.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now:
            raise InviteError('Token expired')
        if invite.used_at is not None:
            raise InviteError('Token already used')
        return invite

    async def use_token(self, token: str) -> InviteToken:
        invite = await self.validate_token(token)
        invite.used_at = datetime.now(timezone.utc)
        return invite

    async def get_latest_active_token(self, task_id: uuid.UUID) -> InviteToken | None:
        now = datetime.now(timezone.utc)
        return await self.repo.get_latest_active_by_task_id(task_id, now)

    async def regenerate_token(self, task_id: uuid.UUID, expires_hours: int = 24) -> InviteToken:
        now = datetime.now(timezone.utc)
        await self.repo.expire_active_by_task_id(task_id, now)
        return await self.create_token(task_id=task_id, expires_hours=expires_hours)
