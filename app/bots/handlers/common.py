from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.users import UserRepository
from app.schemas.common import Role


async def get_actor_from_message(message: Message, session: AsyncSession):
    user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
    if user is None or user.role not in {Role.ADMIN, Role.SYSADMIN}:
        await message.answer('Access denied')
        return None
    return user


async def get_actor_from_callback(callback: CallbackQuery, session: AsyncSession):
    user = await UserRepository(session).get_by_telegram_id(callback.from_user.id)
    if user is None or user.role not in {Role.ADMIN, Role.SYSADMIN}:
        await callback.answer('Access denied', show_alert=True)
        return None
    return user
