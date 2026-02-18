import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.common import ExecutionMode, TaskStatus, TaskType


class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType, name='task_type_enum'), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus, name='task_status_enum'), nullable=False, default=TaskStatus.CREATED)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True)
    execution_mode: Mapped[ExecutionMode] = mapped_column(
        Enum(ExecutionMode, name='execution_mode_enum'), nullable=False, default=ExecutionMode.ASSISTED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    data: Mapped['TaskData'] = relationship(back_populates='task', uselist=False, cascade='all, delete-orphan')
