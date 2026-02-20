from aiogram import Bot
from aiogram.types import BotCommand


CONTROL_BOT_COMMANDS = [
    BotCommand(command='new_issue', description='Create ISSUE_NEW task'),
    BotCommand(command='new_replace', description='Create REPLACE_DAMAGED task'),
    BotCommand(command='new_topup', description='Create TOPUP task'),
    BotCommand(command='active', description='List active tasks'),
    BotCommand(command='whoami', description='Show your telegram_id and role'),
    BotCommand(command='grant', description='Grant role (ADMIN only)'),
    BotCommand(command='revoke', description='Revoke access (ADMIN only)'),
    BotCommand(command='help', description='Show command help'),
]


async def setup_control_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(CONTROL_BOT_COMMANDS)
