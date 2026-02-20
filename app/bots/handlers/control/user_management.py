from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bots.handlers.common import get_actor_from_message
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.users import UserRepository
from app.schemas.common import Role

router = Router()


@router.message(Command('whoami'))
async def whoami(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
        if user is None:
            owner_note = ''
            if settings.owner_telegram_id and message.from_user.id == settings.owner_telegram_id:
                owner_note = ' (OWNER configured: send any admin command once to auto-bootstrap)'
            await message.answer(f'Your telegram_id: {message.from_user.id}\nRole: not assigned{owner_note}')
            return

        await message.answer(f'Your telegram_id: {message.from_user.id}\nRole: {user.role.value}')


@router.message(Command('grant'))
async def grant(message: Message) -> None:
    parts = (message.text or '').split()
    if len(parts) != 3:
        await message.answer('Usage: /grant <telegram_id> <ADMIN|SYSADMIN>')
        return

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return
        if actor.role != Role.ADMIN:
            await message.answer('Only ADMIN can grant roles')
            return

        try:
            target_telegram_id = int(parts[1])
            target_role = Role(parts[2].upper())
        except ValueError:
            await message.answer('Invalid arguments. Usage: /grant <telegram_id> <ADMIN|SYSADMIN>')
            return

        repo = UserRepository(session)
        target = await repo.get_by_telegram_id(target_telegram_id)
        if target is None:
            target = await repo.create(target_telegram_id, target_role)
            action = 'created'
        else:
            target.role = target_role
            action = 'updated'
        await session.commit()
        await message.answer(f'User {target_telegram_id} {action} with role {target.role.value}')


@router.message(Command('revoke'))
async def revoke(message: Message) -> None:
    parts = (message.text or '').split()
    if len(parts) != 2:
        await message.answer('Usage: /revoke <telegram_id>')
        return

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return
        if actor.role != Role.ADMIN:
            await message.answer('Only ADMIN can revoke roles')
            return

        try:
            target_telegram_id = int(parts[1])
        except ValueError:
            await message.answer('Invalid telegram_id. Usage: /revoke <telegram_id>')
            return

        if settings.owner_telegram_id and target_telegram_id == settings.owner_telegram_id:
            await message.answer('Owner access cannot be revoked via bot command')
            return

        deleted = await UserRepository(session).delete_by_telegram_id(target_telegram_id)
        await session.commit()
        if not deleted:
            await message.answer(f'User {target_telegram_id} not found')
            return
        await message.answer(f'User {target_telegram_id} revoked')
