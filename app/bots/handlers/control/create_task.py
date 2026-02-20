import uuid

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bots.handlers.common import get_actor_from_message
from app.bots.keyboards.task_actions import task_actions_markup
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.common import TaskStatus, TaskType
from app.services.presentation_service import creation_help, render_task_card
from app.services.task_service import TaskService

router = Router()


def _intake_link(token: uuid.UUID) -> str:
    return f'https://t.me/{settings.intake_bot_username}?start={token}'


def _link_explainer(task_id: uuid.UUID, link: str) -> str:
    return (
        f'ID задачи: {task_id}\n'
        f'Ссылка для клиента (одноразовая): {link}\n\n'
        'Назначение кнопок ниже:\n'
        '- Поделиться ссылкой: открыть интерфейс Telegram для отправки клиенту\n'
        '- Открыть анкету: открыть ссылку анкеты\n'
        '- Показать ссылку: прислать ссылку текстом (можно вручную скопировать)\n'
        '- Обновить ссылку: сделать новую ссылку, старая перестанет работать'
    )


@router.message(Command(commands=['vypusk', 'new_issue']))
async def new_issue(message: Message) -> None:
    # /vypusk <card_no>
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer('Формат: /vypusk <card_no>')
        return

    card_no = parts[1].strip()

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return

        service = TaskService(session)
        result = await service.create_task_with_invite(
            TaskType.ISSUE_NEW,
            actor.id,
            {'card_no': str(card_no)},
            invite_expires_hours=settings.invite_expires_hours,
        )
        task = result.task
        link = _intake_link(result.invite_token)
        await message.answer(_link_explainer(task.id, link))
        await message.answer(creation_help(TaskType.ISSUE_NEW, link))
        await message.answer(render_task_card(task), reply_markup=task_actions_markup(task.id, invite_link=link))


@router.message(Command(commands=['zamena', 'new_replace']))
async def new_replace(message: Message) -> None:
    # /zamena <old_card_no> <new_card_no>
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer('Формат: /zamena <old_card_no> <new_card_no>')
        return

    old_card_no, new_card_no = parts[1], parts[2]

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return

        service = TaskService(session)
        result = await service.create_task_with_invite(
            TaskType.REPLACE_DAMAGED,
            actor.id,
            {'old_card_no': str(old_card_no), 'new_card_no': str(new_card_no)},
            invite_expires_hours=settings.invite_expires_hours,
        )
        task = result.task
        link = _intake_link(result.invite_token)
        await message.answer(_link_explainer(task.id, link))
        await message.answer(creation_help(TaskType.REPLACE_DAMAGED, link))
        await message.answer(render_task_card(task), reply_markup=task_actions_markup(task.id, invite_link=link))


@router.message(Command(commands=['popolnenie', 'new_topup']))
async def new_topup(message: Message) -> None:
    # /popolnenie <card_no> <amount_rub> <payment_id> <payer_name>
    parts = message.text.split(maxsplit=4)
    if len(parts) < 5:
        await message.answer('Формат: /popolnenie <card_no> <amount_rub> <payment_id> <payer_name>')
        return

    card_no, amount, payment_id, payer_name = parts[1], parts[2], parts[3], parts[4]

    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return

        service = TaskService(session)
        task = await service.create_task(
            TaskType.TOPUP,
            actor.id,
            {
                'card_no': str(card_no),
                'amount_rub': int(amount),
                'payment_id': payment_id,
                'payer_name': payer_name,
            },
        )
        await service.change_status(task.id, actor.id, actor.role, TaskStatus.DATA_COLLECTED)
        await message.answer(creation_help(TaskType.TOPUP))
        await message.answer(render_task_card(task), reply_markup=task_actions_markup(task.id))
