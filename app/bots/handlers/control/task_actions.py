import uuid

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bots.handlers.common import get_actor_from_callback
from app.db.session import AsyncSessionLocal
from app.schemas.common import TaskStatus
from app.services.permission_service import PermissionDeniedError
from app.services.state_machine import StateMachineError
from app.services.task_service import TaskService

router = Router()


def _parse_callback(data: str) -> tuple[str, uuid.UUID]:
    # task:<action>:<task_id>
    _, action, task_id = data.split(':', maxsplit=2)
    return action, uuid.UUID(task_id)


@router.callback_query(F.data.startswith('task:'))
async def task_actions(callback: CallbackQuery) -> None:
    action, task_id = _parse_callback(callback.data)

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_callback(callback, session)
        if actor is None:
            return

        service = TaskService(session)
        try:
            if action == 'copy_json':
                text = await service.build_pds_payload_json(task_id, actor.id)
                await callback.message.answer(f'```json\n{text}\n```', parse_mode='Markdown')
            elif action == 'copy_steps':
                text = await service.build_pds_steps(task_id, actor.id)
                await callback.message.answer(text)
            elif action == 'take':
                result = await service.transition(task_id, actor.id, actor.role, TaskStatus.IN_PROGRESS)
                label = 'already IN_PROGRESS' if not result.applied else 'IN_PROGRESS'
                await callback.message.answer(f'Task {result.task_id} -> {label}')
            elif action == 'done':
                result = await service.transition(task_id, actor.id, actor.role, TaskStatus.DONE_BY_SYSADMIN)
                label = 'already DONE_BY_SYSADMIN' if not result.applied else 'DONE_BY_SYSADMIN'
                await callback.message.answer(f'Task {result.task_id} -> {label}')
            elif action == 'cancel':
                result = await service.transition(task_id, actor.id, actor.role, TaskStatus.CANCELLED)
                label = 'already CANCELLED' if not result.applied else 'CANCELLED'
                await callback.message.answer(f'Task {result.task_id} -> {label}')
        except (PermissionDeniedError, StateMachineError, ValueError) as exc:
            await callback.message.answer(str(exc))
        await callback.answer()
