import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ExecutionMode, TaskStatus, TaskType


class TaskRead(BaseModel):
    id: uuid.UUID
    type: TaskType
    status: TaskStatus
    created_by: int
    assigned_to: int | None
    execution_mode: ExecutionMode
    created_at: datetime
    updated_at: datetime


class TaskWithData(TaskRead):
    data: dict
