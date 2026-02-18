import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(self, task_id: uuid.UUID, actor_id: int, action: str, metadata: dict | None = None) -> AuditLog:
        row = AuditLog(task_id=task_id, actor_id=actor_id, action=action, metadata_=metadata or {})
        self.session.add(row)
        await self.session.flush()
        return row
