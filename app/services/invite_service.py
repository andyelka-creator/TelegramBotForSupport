import uuid
from datetime import datetime, timedelta, timezone

from app.repositories.invite_tokens import InviteTokenRepository


class InviteError(ValueError):
    pass


class InviteService:
    def __init__(self, repo: InviteTokenRepository):
        self.repo = repo

    async def create_token(self, task_id: uuid.UUID, expires_hours: int) -> uuid.UUID:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        invite = await self.repo.create(task_id=task_id, expires_at=expires_at)
        return invite.token

    async def validate_token(self, token: str):
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

    async def use_token(self, token: str):
        invite = await self.validate_token(token)
        invite.used_at = datetime.now(timezone.utc)
        return invite
