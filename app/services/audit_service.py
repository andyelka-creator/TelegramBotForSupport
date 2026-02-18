import uuid

from app.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, repo: AuditRepository):
        self.repo = repo

    async def log(self, task_id: uuid.UUID, actor_id: int, action: str, metadata: dict | None = None) -> None:
        await self.repo.log(task_id=task_id, actor_id=actor_id, action=action, metadata=metadata or {})
