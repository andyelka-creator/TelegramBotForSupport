import pytest

from app.repositories.tasks import TaskRepository
from app.schemas.common import Role, TaskStatus, TaskType
from app.services.permission_service import PermissionDeniedError
from app.services.task_service import TaskService


async def test_admin_cannot_mark_done_by_sysadmin(session):
    service = TaskService(session)
    task = await service.create_task(TaskType.TOPUP, actor_id=1, initial_data={'card_no': '001'})
    await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.DATA_COLLECTED)
    await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.IN_PROGRESS)

    with pytest.raises(PermissionDeniedError):
        await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.DONE_BY_SYSADMIN)


async def test_sysadmin_cannot_confirm(session):
    service = TaskService(session)
    task = await service.create_task(TaskType.TOPUP, actor_id=1, initial_data={'card_no': '001'})
    await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.DATA_COLLECTED)
    await service.transition(task.id, actor_id=1, actor_role=Role.ADMIN, new_status=TaskStatus.IN_PROGRESS)
    await service.transition(task.id, actor_id=2, actor_role=Role.SYSADMIN, new_status=TaskStatus.DONE_BY_SYSADMIN)

    with pytest.raises(PermissionDeniedError):
        await service.transition(task.id, actor_id=2, actor_role=Role.SYSADMIN, new_status=TaskStatus.CONFIRMED)


async def test_unauthorized_transition_raises_controlled_error(session):
    service = TaskService(session)
    task = await TaskRepository(session).create_task(TaskType.ISSUE_NEW, created_by=1)
    await session.commit()

    with pytest.raises(PermissionDeniedError):
        await service.transition(task.id, actor_id=2, actor_role=Role.SYSADMIN, new_status=TaskStatus.CANCELLED)
