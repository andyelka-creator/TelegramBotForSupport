from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.user import User
from app.repositories.users import UserRepository
from app.schemas.common import Role


async def resolve_actor_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(telegram_id)

    if user is None and settings.owner_telegram_id and telegram_id == settings.owner_telegram_id:
        user = await repo.create(telegram_id=telegram_id, role=Role.ADMIN)
        await session.commit()

    if user is None or user.role not in {Role.ADMIN, Role.SYSADMIN}:
        return None
    return user


async def get_actor_from_message(message: Message, session: AsyncSession):
    if message.from_user is None:
        await message.answer('Не удалось определить пользователя. Отключите анонимный режим администратора в группе.')
        return None

    user = await resolve_actor_by_telegram_id(session, message.from_user.id)
    # Close implicit read transaction before write operations in handlers.
    await session.commit()
    if user is None:
        await message.answer('Access denied')
        return None
    return user


async def get_actor_from_callback(callback: CallbackQuery, session: AsyncSession):
    if callback.from_user is None:
        await callback.answer('Не удалось определить пользователя', show_alert=True)
        return None

    user = await resolve_actor_by_telegram_id(session, callback.from_user.id)
    # Close implicit read transaction before write operations in handlers.
    await session.commit()
    if user is None:
        await callback.answer('Access denied', show_alert=True)
        return None
    return user
