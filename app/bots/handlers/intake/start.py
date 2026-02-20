from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bots.handlers.intake.issue_new_form import IssueNewStates
from app.bots.handlers.intake.replace_form import ReplaceStates
from app.db.session import AsyncSessionLocal
from app.repositories.tasks import TaskRepository
from app.schemas.common import TaskType
from app.services.invite_service import InviteError, InviteService
from app.repositories.invite_tokens import InviteTokenRepository

router = Router()


@router.message(CommandStart(deep_link=True))
async def start_with_token(message: Message, command: CommandObject, state: FSMContext) -> None:
    token = command.args
    if not token:
        await message.answer('Missing token')
        return

    async with AsyncSessionLocal() as session:
        invite_service = InviteService(InviteTokenRepository(session))
        try:
            invite = await invite_service.validate_token(token)
        except InviteError:
            await message.answer('Link expired. Please contact administrator.')
            return

        task = await TaskRepository(session).get(invite.task_id)
        if task is None:
            await message.answer('Link expired. Please contact administrator.')
            return

        await state.update_data(token=token, task_id=str(task.id))
        if task.type == TaskType.ISSUE_NEW:
            await state.set_state(IssueNewStates.last_name)
            await message.answer('Анкета: Введите фамилию')
        elif task.type == TaskType.REPLACE_DAMAGED:
            await state.set_state(ReplaceStates.damaged_card_photo)
            await message.answer('Пришлите фото поврежденной карты')
        else:
            await message.answer('This task type does not require guest intake')
