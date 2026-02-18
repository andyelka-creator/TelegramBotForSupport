from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.models import *  # noqa: F401,F403
from app.db.models.user import User
from app.schemas.common import Role

@pytest.fixture()
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine('sqlite+aiosqlite:///:memory:', future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db:
        admin = User(telegram_id=111, role=Role.ADMIN)
        sysadmin = User(telegram_id=222, role=Role.SYSADMIN)
        db.add_all([admin, sysadmin])
        await db.commit()
        yield db

    await engine.dispose()
