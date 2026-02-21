from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bots.handlers.common import get_actor_from_message
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.users import UserRepository
from app.schemas.common import Role

router = Router()


@router.message(Command(commands=["ktoya", "whoami"]))
async def whoami(message: Message) -> None:
    if message.from_user is None:
        await message.answer("Не удалось определить пользователя")
        return
    async with AsyncSessionLocal() as session:
        user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
        if user is None:
            owner_note = ""
            if settings.owner_telegram_id and message.from_user.id == settings.owner_telegram_id:
                owner_note = " (владелец настроен: отправьте любую админ-команду для авто-выдачи роли)"
            await message.answer(f"Ваш telegram_id: {message.from_user.id}\nРоль: не назначена{owner_note}")
            return

        await message.answer(f"Ваш telegram_id: {message.from_user.id}\nРоль: {user.role.value}")


@router.message(Command(commands=["dat_dostup", "grant"]))
async def grant(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer("Формат: /dat_dostup <telegram_id> <ADMIN|SYSADMIN>")
        return

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return
        if actor.role != Role.ADMIN:
            await message.answer("Только ADMIN может выдавать роли")
            return

        try:
            target_telegram_id = int(parts[1])
            target_role = Role(parts[2].upper())
        except ValueError:
            await message.answer("Неверные аргументы. Формат: /dat_dostup <telegram_id> <ADMIN|SYSADMIN>")
            return

        repo = UserRepository(session)
        target = await repo.get_by_telegram_id(target_telegram_id)
        if target is None:
            target = await repo.create(target_telegram_id, target_role)
            action = "created"
        else:
            target.role = target_role
            action = "updated"
        await session.commit()
        action_text = "создан" if action == "created" else "обновлен"
        await message.answer(f"Пользователь {target_telegram_id} {action_text}, роль: {target.role.value}")


@router.message(Command(commands=["ubrat_dostup", "revoke"]))
async def revoke(message: Message) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2:
        await message.answer("Формат: /ubrat_dostup <telegram_id>")
        return

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return
        if actor.role != Role.ADMIN:
            await message.answer("Только ADMIN может отзывать роли")
            return

        try:
            target_telegram_id = int(parts[1])
        except ValueError:
            await message.answer("Неверный telegram_id. Формат: /ubrat_dostup <telegram_id>")
            return

        if settings.owner_telegram_id and target_telegram_id == settings.owner_telegram_id:
            await message.answer("Доступ владельца нельзя отозвать через команду бота")
            return

        deleted = await UserRepository(session).delete_by_telegram_id(target_telegram_id)
        await session.commit()
        if not deleted:
            await message.answer(f"Пользователь {target_telegram_id} не найден")
            return
        await message.answer(f"Доступ пользователя {target_telegram_id} отозван")
