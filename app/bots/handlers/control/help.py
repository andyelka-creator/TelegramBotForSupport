from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

HELP_TEXT = '\n'.join(
    [
        'Available commands:',
        '/new_issue <card_no> - Create ISSUE_NEW task',
        '/new_replace <old_card_no> <new_card_no> - Create REPLACE_DAMAGED task',
        '/new_topup <card_no> <amount_rub> <payment_id> <payer_name> - Create TOPUP task',
        '/active - List active tasks',
        '/whoami - Show your telegram_id and role',
        '/grant <telegram_id> <ADMIN|SYSADMIN> - Grant/update role (ADMIN only)',
        '/revoke <telegram_id> - Revoke access (ADMIN only)',
        '/help - Show this help',
    ]
)

router = Router()


@router.message(Command('help'))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)
