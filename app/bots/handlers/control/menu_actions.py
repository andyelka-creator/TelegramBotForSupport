from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bots.handlers.control.help import HELP_TEXT
from app.bots.handlers.common import get_actor_from_message
from app.bots.keyboards.control_menu import control_menu_keyboard
from app.db.session import AsyncSessionLocal
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.services.presentation_service import render_task_card

router = Router()


def _menu_hint() -> str:
    return (
        'Меню управления задачами.\n'
        'Используйте кнопки ниже или slash-команды:\n'
        '/vypusk, /zamena, /popolnenie, /aktivnye, /ktoya, /pomosh'
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
async def issue_hint(message: Message) -> None:
    await message.answer('Используйте команду:\n/vypusk <card_no>', reply_markup=control_menu_keyboard)


@router.message(F.text == 'Замена карты')
async def replace_hint(message: Message) -> None:
    await message.answer(
        'Используйте команду:\n/zamena <old_card_no> <new_card_no>',
        reply_markup=control_menu_keyboard,
    )


@router.message(F.text == 'Создать пополнение')
async def topup_hint(message: Message) -> None:
    await message.answer(
        'Используйте команду:\n/popolnenie <card_no> <amount_rub> <payment_id> <payer_name>',
        reply_markup=control_menu_keyboard,
    )
