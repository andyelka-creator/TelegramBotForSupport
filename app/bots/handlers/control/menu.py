from aiogram import Bot
from aiogram.types import BotCommand

CONTROL_BOT_COMMANDS = [
    BotCommand(command="menu", description="Показать меню"),
    BotCommand(command="vypusk", description="Выпуск новой карты"),
    BotCommand(command="zamena", description="Замена карты"),
    BotCommand(command="popolnenie", description="Пополнение карты"),
    BotCommand(command="aktivnye", description="Активные задачи"),
    BotCommand(command="ktoya", description="Мой ID и роль"),
    BotCommand(command="dat_dostup", description="Выдать роль (ADMIN)"),
    BotCommand(command="ubrat_dostup", description="Отозвать доступ (ADMIN)"),
    BotCommand(command="rotaciya_proxy", description="Ротация MTG secret"),
    BotCommand(command="pomosh", description="Справка по командам"),
]


async def setup_control_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(CONTROL_BOT_COMMANDS)
