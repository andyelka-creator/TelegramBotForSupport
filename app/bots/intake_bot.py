import asyncio

from aiogram import Bot, Dispatcher

from app.bots.handlers.intake.issue_new_form import router as issue_router
from app.bots.handlers.intake.replace_form import router as replace_router
from app.bots.handlers.intake.start import router as start_router
from app.config import settings


async def run_intake_bot() -> None:
    if not settings.intake_bot_token:
        raise RuntimeError('INTAKE_BOT_TOKEN is not configured')

    bot = Bot(settings.intake_bot_token)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(issue_router)
    dp.include_router(replace_router)

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(run_intake_bot())
