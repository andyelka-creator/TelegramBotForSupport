from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

HELP_TEXT = '\n'.join(
    [
        'Доступные команды:',
        '/vypusk <card_no> - выпуск новой карты (ISSUE_NEW)',
        '/zamena <old_card_no> <new_card_no> - замена карты (REPLACE_DAMAGED)',
        '/popolnenie <card_no> <amount_rub> <payment_id> <payer_name> - пополнение (TOPUP)',
        '/aktivnye - показать активные задачи',
        '/ktoya - показать ваш telegram_id и роль',
        '/dat_dostup <telegram_id> <ADMIN|SYSADMIN> - выдать/изменить роль (только ADMIN)',
        '/ubrat_dostup <telegram_id> - отозвать доступ (только ADMIN)',
        '/pomosh - показать эту справку',
    ]
)

router = Router()


@router.message(Command(commands=['pomosh', 'help']))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)
