import uuid

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.bots.keyboards.task_actions import task_actions_markup
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.tasks import TaskRepository
from app.services.invite_service import InviteService
from app.repositories.invite_tokens import InviteTokenRepository
from app.services.presentation_service import render_task_card
from app.services.task_service import TaskService

router = Router()


class ReplaceStates(StatesGroup):
    damaged_card_photo = State()
    need_guest = State()
    last_name = State()
    first_name = State()


@router.message(ReplaceStates.damaged_card_photo)
async def replace_photo(message: Message, state: FSMContext) -> None:
    if not message.photo:
        await message.answer('Нужно отправить фото поврежденной карты')
        return

    await state.update_data(damaged_photo=message.photo[-1].file_id)
    await state.set_state(ReplaceStates.need_guest)
    await message.answer('Нужны данные гостя? (yes/no)')


@router.message(ReplaceStates.need_guest)
async def replace_need_guest(message: Message, state: FSMContext) -> None:
    ans = message.text.strip().lower()
    if ans in {'no', 'n', 'нет'}:
        await _finish_replace(message, state)
        return
    await state.set_state(ReplaceStates.last_name)
    await message.answer('Введите фамилию')


@router.message(ReplaceStates.last_name)
async def replace_last_name(message: Message, state: FSMContext) -> None:
    await state.update_data(last_name=message.text.strip())
    await state.set_state(ReplaceStates.first_name)
    await message.answer('Введите имя')


@router.message(ReplaceStates.first_name)
async def replace_first_name(message: Message, state: FSMContext) -> None:
    await state.update_data(first_name=message.text.strip())
    await _finish_replace(message, state)


async def _finish_replace(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    task_id = uuid.UUID(data['task_id'])
    token = data['token']

    async with AsyncSessionLocal() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.get(task_id)
        existing = await task_repo.get_data(task_id)
        merged = dict((existing.json_data if existing else {}))
        merged['damaged_photos'] = [data['damaged_photo']]
        if data.get('last_name'):
            merged['last_name'] = data.get('last_name')
        if data.get('first_name'):
            merged['first_name'] = data.get('first_name')

        service = TaskService(session)
        await service.fill_data(task_id, task.created_by, merged)

        invite_service = InviteService(InviteTokenRepository(session))
        await invite_service.use_token(token)
        await session.commit()

        await message.answer('Спасибо. Анкета отправлена.')
        await message.bot.send_message(
            chat_id=settings.control_group_id,
            text=render_task_card(task, guest_name=(data.get('last_name') or 'N/A'), photo_attached=True),
            reply_markup=task_actions_markup(task.id),
        )

    await state.clear()
