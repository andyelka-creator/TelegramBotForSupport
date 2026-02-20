import uuid

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.bots.keyboards.task_actions import task_actions_markup
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.tasks import TaskRepository
from app.services.presentation_service import render_task_card
from app.services.task_service import TaskService
from app.services.invite_service import InviteService
from app.repositories.invite_tokens import InviteTokenRepository
from app.schemas.payloads import IssueNewForm

router = Router()


class IssueNewStates(StatesGroup):
    last_name = State()
    first_name = State()
    middle_name = State()
    phone = State()
    email = State()


@router.message(IssueNewStates.last_name)
async def issue_last_name(message: Message, state: FSMContext) -> None:
    await state.update_data(last_name=message.text.strip())
    await state.set_state(IssueNewStates.first_name)
    await message.answer('Введите имя')


@router.message(IssueNewStates.first_name)
async def issue_first_name(message: Message, state: FSMContext) -> None:
    await state.update_data(first_name=message.text.strip())
    await state.set_state(IssueNewStates.middle_name)
    await message.answer('Введите отчество (или -)')


@router.message(IssueNewStates.middle_name)
async def issue_middle_name(message: Message, state: FSMContext) -> None:
    value = message.text.strip()
    await state.update_data(middle_name=None if value == '-' else value)
    await state.set_state(IssueNewStates.phone)
    await message.answer('Введите телефон')


@router.message(IssueNewStates.phone)
async def issue_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await state.set_state(IssueNewStates.email)
    await message.answer('Введите email (или -)')


@router.message(IssueNewStates.email)
async def issue_email(message: Message, state: FSMContext) -> None:
    value = message.text.strip()
    await state.update_data(email=None if value == '-' else value)

    data = await state.get_data()
    task_id = uuid.UUID(data['task_id'])
    token = data['token']

    async with AsyncSessionLocal() as session:
        task_repo = TaskRepository(session)
        task = await task_repo.get(task_id)
        existing = await task_repo.get_data(task_id)
        merged = dict((existing.json_data if existing else {}))
        candidate = {
            **merged,
            'last_name': data['last_name'],
            'first_name': data['first_name'],
            'middle_name': data.get('middle_name'),
            'phone': data['phone'],
            'email': data.get('email'),
        }
        try:
            validated = IssueNewForm.model_validate(candidate)
        except Exception:
            await message.answer('Ошибка валидации анкеты. Проверьте email/телефон и начните заново.')
            await state.clear()
            return

        merged.update(
            {
                'last_name': validated.last_name,
                'first_name': validated.first_name,
                'middle_name': validated.middle_name,
                'phone': validated.phone,
                'email': str(validated.email) if validated.email else None,
            }
        )

        service = TaskService(session)
        invite_service = InviteService(InviteTokenRepository(session))
        async with session.begin():
            await service.fill_data(task_id, task.created_by, merged, auto_commit=False)
            await invite_service.use_token(token)
            await service.audit.log(
                task_id=task_id,
                actor_id=task.created_by,
                action='INVITE_TOKEN_USED',
                metadata={'token': token},
            )

        await message.answer('Спасибо. Анкета отправлена.')
        await message.bot.send_message(
            chat_id=settings.control_group_id,
            text=render_task_card(task, guest_name=f"{data['last_name']} {data['first_name']}"),
            reply_markup=task_actions_markup(task.id),
        )

    await state.clear()
