import uuid

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def task_actions_markup(task_id: uuid.UUID) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sid = str(task_id)
    builder.button(text='📋 Copy PDS JSON', callback_data=f'task:copy_json:{sid}')
    builder.button(text='🧩 Copy PDS Steps', callback_data=f'task:copy_steps:{sid}')
    builder.button(text='Take', callback_data=f'task:take:{sid}')
    builder.button(text='Done', callback_data=f'task:done:{sid}')
    builder.button(text='Cancel', callback_data=f'task:cancel:{sid}')
    builder.adjust(2, 3)
    return builder.as_markup()
