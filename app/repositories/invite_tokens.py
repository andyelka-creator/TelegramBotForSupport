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

    async def get_latest_by_task_id(self, task_id: uuid.UUID) -> InviteToken | None:
        result = await self.session.execute(
            select(InviteToken).where(InviteToken.task_id == task_id).order_by(InviteToken.created_at.desc(), InviteToken.id.desc())
        )
        return result.scalars().first()

    async def get_latest_active_by_task_id(self, task_id: uuid.UUID, now: datetime) -> InviteToken | None:
        result = await self.session.execute(
            select(InviteToken)
            .where(
                InviteToken.task_id == task_id,
                InviteToken.used_at.is_(None),
                InviteToken.expires_at > now,
            )
            .order_by(InviteToken.created_at.desc(), InviteToken.id.desc())
        )
        return result.scalars().first()

    async def expire_active_by_task_id(self, task_id: uuid.UUID, now: datetime) -> int:
        rows = await self.session.execute(
            select(InviteToken).where(
                InviteToken.task_id == task_id,
                InviteToken.used_at.is_(None),
                InviteToken.expires_at > now,
            )
        )
        active_rows = list(rows.scalars().all())
        for row in active_rows:
            row.expires_at = now
        await self.session.flush()
        return len(active_rows)
