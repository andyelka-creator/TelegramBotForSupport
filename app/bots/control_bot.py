import asyncio

from aiogram import Bot, Dispatcher

from app.bots.handlers.control.create_task import router as create_router
from app.bots.handlers.control.help import router as help_router
from app.bots.handlers.control.list_tasks import router as list_router
from app.bots.handlers.control.menu import setup_control_bot_commands
from app.bots.handlers.control.task_actions import router as action_router
from app.bots.handlers.control.user_management import router as user_mgmt_router
from app.config import settings


async def run_control_bot() -> None:
    if not settings.control_bot_token:
        raise RuntimeError('CONTROL_BOT_TOKEN is not configured')

    bot = Bot(settings.control_bot_token)
    await setup_control_bot_commands(bot)

    dp = Dispatcher()
    dp.include_router(help_router)
    dp.include_router(create_router)
    dp.include_router(list_router)
    dp.include_router(action_router)
    dp.include_router(user_mgmt_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(run_control_bot())
