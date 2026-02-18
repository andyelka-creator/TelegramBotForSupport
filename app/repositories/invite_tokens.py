import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.invite_token import InviteToken


class InviteTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, task_id: uuid.UUID, expires_at: datetime) -> InviteToken:
        invite = InviteToken(task_id=task_id, expires_at=expires_at)
        self.session.add(invite)
        await self.session.flush()
        return invite

    async def get_by_token(self, token: uuid.UUID) -> InviteToken | None:
        result = await self.session.execute(select(InviteToken).where(InviteToken.token == token))
        return result.scalar_one_or_none()
