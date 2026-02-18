from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.schemas.common import Role


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name='role_enum'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
