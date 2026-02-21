import pytest
from sqlalchemy import func, select

from app.db.models.audit_log import AuditLog
from app.repositories.tasks import TaskRepository
from app.schemas.common import Role, TaskStatus, TaskType
from app.services.task_service import TaskService

pytestmark = pytest.mark.integration


async def test_double_transition_is_idempotent_and_audited_once(session):
    service = TaskService(session)
    task = await service.create_task(TaskType.TOPUP, actor_id=1, initial_data={'card_no': '001'})

    await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.DATA_COLLECTED)
    first = await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.IN_PROGRESS)
    second = await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.IN_PROGRESS)

    assert first.applied is True
    assert second.applied is False

    refreshed = await TaskRepository(session).get(task.id)
    assert refreshed.status == TaskStatus.IN_PROGRESS

    result = await session.execute(
        select(func.count(AuditLog.id)).where(AuditLog.task_id == task.id).where(AuditLog.action == 'STATUS_CHANGED')
    )
    assert result.scalar_one() == 2
