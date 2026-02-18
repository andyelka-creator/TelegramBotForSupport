import uuid

from sqlalchemy import ForeignKey, JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

JSONType = JSON().with_variant(JSONB, 'postgresql')


class TaskData(Base):
    __tablename__ = 'task_data'

    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey('tasks.id'), primary_key=True)
    json_data: Mapped[dict] = mapped_column(JSONType, default=dict)

    task = relationship('Task', back_populates='data')
