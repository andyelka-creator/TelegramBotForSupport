import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session
from app.repositories.tasks import TaskRepository
from app.schemas.task import TaskRead, TaskWithData

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.get('/active', response_model=list[TaskRead])
async def active_tasks(session: AsyncSession = Depends(db_session)):
    tasks = await TaskRepository(session).list_active()
    return [TaskRead.model_validate(task, from_attributes=True) for task in tasks]


@router.get('/{task_id}', response_model=TaskWithData)
async def get_task(task_id: uuid.UUID, session: AsyncSession = Depends(db_session)):
    repo = TaskRepository(session)
    task = await repo.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    data = await repo.get_data(task_id)

    base = TaskRead.model_validate(task, from_attributes=True)
    return TaskWithData(**base.model_dump(), data=(data.json_data if data else {}))
