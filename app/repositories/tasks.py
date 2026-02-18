import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task
from app.db.models.task_data import TaskData
from app.schemas.common import TaskStatus, TaskType


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(self, task_type: TaskType, created_by: int, status: TaskStatus = TaskStatus.CREATED) -> Task:
        task = Task(type=task_type, created_by=created_by, status=status)
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: uuid.UUID) -> Task | None:
        return await self.session.get(Task, task_id)

    async def get_for_update(self, task_id: uuid.UUID) -> Task | None:
        result = await self.session.execute(select(Task).where(Task.id == task_id).with_for_update())
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Task]:
        result = await self.session.execute(
            select(Task).where(Task.status.notin_([TaskStatus.CLOSED, TaskStatus.CANCELLED])).order_by(Task.created_at.desc())
        )
        return list(result.scalars().all())

    async def set_data(self, task_id: uuid.UUID, payload: dict) -> TaskData:
        row = await self.session.get(TaskData, task_id)
        if row is None:
            row = TaskData(task_id=task_id, json_data=payload)
            self.session.add(row)
        else:
            row.json_data = payload
        await self.session.flush()
        return row

    async def get_data(self, task_id: uuid.UUID) -> TaskData | None:
        return await self.session.get(TaskData, task_id)
