import uuid

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ForceReply, Message

from app.bots.handlers.control.help import HELP_TEXT
from app.bots.handlers.common import get_actor_from_message
from app.bots.keyboards.control_menu import control_menu_keyboard
from app.bots.keyboards.task_actions import task_actions_markup
from app.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.schemas.common import TaskStatus, TaskType
from app.services.presentation_service import creation_help, render_task_card
from app.services.task_service import TaskService

router = Router()


class CreateFromMenuStates(StatesGroup):
    issue_card_no = State()
    replace_old_card_no = State()
    replace_new_card_no = State()
    topup_card_no = State()
    topup_amount = State()
    topup_payment_id = State()
    topup_payer_name = State()


def _menu_hint() -> str:
    return (
        'Меню управления задачами.\n'
        'Используйте кнопки ниже или slash-команды:\n'
        '/vypusk, /zamena, /popolnenie, /aktivnye, /ktoya, /pomosh'
    )


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


@router.message(Command(commands=['start', 'menu']))
async def open_menu(message: Message) -> None:
    await message.answer(_menu_hint(), reply_markup=control_menu_keyboard)


@router.message(F.text == 'Меню')
async def menu_button(message: Message) -> None:
    await message.answer(_menu_hint(), reply_markup=control_menu_keyboard)


@router.message(F.text == 'Помощь')
async def help_button(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=control_menu_keyboard)


@router.message(F.text == 'Кто я')
async def whoami_button(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserRepository(session).get_by_telegram_id(message.from_user.id)
        if user is None:
            await message.answer(
                f'Ваш telegram_id: {message.from_user.id}\nРоль: не назначена',
                reply_markup=control_menu_keyboard,
            )
            return
        await message.answer(
            f'Ваш telegram_id: {message.from_user.id}\nРоль: {user.role.value}',
            reply_markup=control_menu_keyboard,
        )


@router.message(F.text == 'Активные задачи')
async def active_button(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return

        tasks = await TaskRepository(session).list_active()
        if not tasks:
            await message.answer('Активных задач нет', reply_markup=control_menu_keyboard)
            return

        for task in tasks[:20]:
            data = await TaskRepository(session).get_data(task.id)
            has_photo = bool((data.json_data if data else {}).get('damaged_photos'))
            await message.answer(
                render_task_card(task, photo_attached=has_photo),
                reply_markup=control_menu_keyboard,
            )


@router.message(F.text == 'Новая карта')
async def issue_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateFromMenuStates.issue_card_no)
    await message.answer('Введите номер новой карты:', reply_markup=ForceReply(selective=True))


@router.message(CreateFromMenuStates.issue_card_no)
async def issue_finish(message: Message, state: FSMContext) -> None:
    card_no = (message.text or '').strip()
    if not card_no:
        await message.answer('Номер карты пустой. Введите номер новой карты:')
        return

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

    await state.clear()


@router.message(F.text == 'Замена карты')
async def replace_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateFromMenuStates.replace_old_card_no)
    await message.answer('Введите номер старой карты:', reply_markup=ForceReply(selective=True))


@router.message(CreateFromMenuStates.replace_old_card_no)
async def replace_old(message: Message, state: FSMContext) -> None:
    old_card_no = (message.text or '').strip()
    if not old_card_no:
        await message.answer('Номер старой карты пустой. Введите номер старой карты:')
        return
    await state.update_data(old_card_no=old_card_no)
    await state.set_state(CreateFromMenuStates.replace_new_card_no)
    await message.answer('Введите номер новой карты:', reply_markup=ForceReply(selective=True))


@router.message(CreateFromMenuStates.replace_new_card_no)
async def replace_finish(message: Message, state: FSMContext) -> None:
    new_card_no = (message.text or '').strip()
    if not new_card_no:
        await message.answer('Номер новой карты пустой. Введите номер новой карты:')
        return

    data = await state.get_data()
    old_card_no = data.get('old_card_no', '')

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

    await state.clear()


@router.message(F.text == 'Создать пополнение')
async def topup_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateFromMenuStates.topup_card_no)
    await message.answer('Введите номер карты для пополнения:', reply_markup=ForceReply(selective=True))


@router.message(CreateFromMenuStates.topup_card_no)
async def topup_card_no(message: Message, state: FSMContext) -> None:
    card_no = (message.text or '').strip()
    if not card_no:
        await message.answer('Номер карты пустой. Введите номер карты:')
        return
    await state.update_data(card_no=card_no)
    await state.set_state(CreateFromMenuStates.topup_amount)
    await message.answer('Введите сумму в рублях (целое число):', reply_markup=ForceReply(selective=True))


@router.message(CreateFromMenuStates.topup_amount)
async def topup_amount(message: Message, state: FSMContext) -> None:
    text = (message.text or '').strip()
    try:
        amount = int(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer('Сумма должна быть положительным целым числом. Введите сумму:')
        return
    await state.update_data(amount_rub=amount)
    await state.set_state(CreateFromMenuStates.topup_payment_id)
    await message.answer('Введите payment_id:', reply_markup=ForceReply(selective=True))


@router.message(CreateFromMenuStates.topup_payment_id)
async def topup_payment_id(message: Message, state: FSMContext) -> None:
    payment_id = (message.text or '').strip()
    if not payment_id:
        await message.answer('payment_id пустой. Введите payment_id:')
        return
    await state.update_data(payment_id=payment_id)
    await state.set_state(CreateFromMenuStates.topup_payer_name)
    await message.answer('Введите ФИО плательщика:', reply_markup=ForceReply(selective=True))


@router.message(CreateFromMenuStates.topup_payer_name)
async def topup_finish(message: Message, state: FSMContext) -> None:
    payer_name = (message.text or '').strip()
    if not payer_name:
        await message.answer('ФИО плательщика пустое. Введите ФИО плательщика:')
        return

    data = await state.get_data()
    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return

        service = TaskService(session)
        task = await service.create_task(
            TaskType.TOPUP,
            actor.id,
            {
                'card_no': str(data['card_no']),
                'amount_rub': int(data['amount_rub']),
                'payment_id': str(data['payment_id']),
                'payer_name': payer_name,
            },
        )
        await service.change_status(task.id, actor.id, actor.role, TaskStatus.DATA_COLLECTED)
        await message.answer(creation_help(TaskType.TOPUP))
        await message.answer(render_task_card(task), reply_markup=task_actions_markup(task.id))

    await state.clear()
