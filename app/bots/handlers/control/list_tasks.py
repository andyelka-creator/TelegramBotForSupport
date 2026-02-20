from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bots.handlers.common import get_actor_from_message
from app.db.session import AsyncSessionLocal
from app.repositories.tasks import TaskRepository
from app.services.presentation_service import render_task_card

router = Router()


@router.message(Command(commands=['aktivnye', 'active']))
async def active_tasks(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        actor = await get_actor_from_message(message, session)
        if actor is None:
            return

        tasks = await TaskRepository(session).list_active()
        if not tasks:
            await message.answer('Активных задач нет')
            return

        for task in tasks[:20]:
            data = await TaskRepository(session).get_data(task.id)
            has_photo = bool((data.json_data if data else {}).get('damaged_photos'))
            await message.answer(render_task_card(task, photo_attached=has_photo))
