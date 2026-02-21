import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bots.handlers.common import get_actor_from_callback
from app.bots.keyboards.task_actions import task_actions_markup
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.common import TaskStatus
from app.services.permission_service import PermissionDeniedError
from app.services.state_machine import StateMachineError
from app.services.task_service import TaskService

router = Router()


def _parse_callback(data: str) -> tuple[str, uuid.UUID]:
    # task:<action>:<task_id>
    _, action, task_id = data.split(":", maxsplit=2)
    return action, uuid.UUID(task_id)


def _intake_link(token: uuid.UUID) -> str:
    return f"https://t.me/{settings.intake_bot_username}?start={token}"


@router.callback_query(F.data.startswith("task:"))
async def task_actions(callback: CallbackQuery) -> None:
    if callback.data is None or callback.message is None:
        await callback.answer("Некорректное действие", show_alert=True)
        return
    if not isinstance(callback.message, Message):
        await callback.answer("Сообщение недоступно", show_alert=True)
        return
    action, task_id = _parse_callback(callback.data)
    cb_message = callback.message

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_callback(callback, session)
        if actor is None:
            return

        service = TaskService(session)
        try:
            if action == "copy_json":
                text = await service.build_pds_payload_json(task_id, actor.id)
                await cb_message.answer(f"```json\n{text}\n```", parse_mode="Markdown")
            elif action == "copy_steps":
                text = await service.build_pds_steps(task_id, actor.id)
                await cb_message.answer(text)
            elif action == "copy_link":
                token = await service.get_active_invite(task_id)
                if token is None:
                    await cb_message.answer('Активной ссылки нет. Нажмите "Обновить ссылку".')
                else:
                    await cb_message.answer(f"Ссылка для клиента: {_intake_link(token)}")
            elif action == "regen_link":
                token = await service.regenerate_invite(task_id, actor.id, settings.invite_expires_hours)
                link = _intake_link(token)
                await cb_message.answer(
                    f"Новая ссылка для клиента: {link}\nСтарая ссылка больше не работает.",
                    reply_markup=task_actions_markup(task_id, invite_link=link),
                )
            elif action == "take":
                result = await service.transition(task_id, actor.id, actor.role, TaskStatus.IN_PROGRESS)
                label = "уже в работе" if not result.applied else "в работе"
                await cb_message.answer(f"Задача {result.task_id}: {label}")
            elif action == "done":
                result = await service.transition(task_id, actor.id, actor.role, TaskStatus.DONE_BY_SYSADMIN)
                label = "уже отмечена как выполненная" if not result.applied else "выполнена сисадмином"
                await cb_message.answer(f"Задача {result.task_id}: {label}")
            elif action == "cancel":
                result = await service.transition(task_id, actor.id, actor.role, TaskStatus.CANCELLED)
                label = "уже отменена" if not result.applied else "отменена"
                await cb_message.answer(f"Задача {result.task_id}: {label}")
        except (PermissionDeniedError, StateMachineError, ValueError) as exc:
            await cb_message.answer(str(exc))
        await callback.answer()
