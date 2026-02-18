from app.repositories.tasks import TaskRepository
from app.schemas.common import TaskStatus, TaskType
from app.services.task_service import TaskService


async def test_issue_new_creation(session):
    service = TaskService(session)
    task = await service.create_task(TaskType.ISSUE_NEW, actor_id=1, initial_data={'card_no': '001'})

    assert task.type == TaskType.ISSUE_NEW
    assert task.status == TaskStatus.CREATED

    await service.fill_data(
        task.id,
        actor_id=1,
        payload={
            'card_no': '001',
            'last_name': 'Ivanov',
            'first_name': 'Ivan',
            'phone': '+7 (900) 123-45-67',
        },
    )

    refreshed = await TaskRepository(session).get(task.id)
    assert refreshed.status == TaskStatus.DATA_COLLECTED
