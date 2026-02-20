import uuid

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def task_actions_markup(task_id: uuid.UUID, invite_link: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sid = str(task_id)
    if invite_link:
        builder.button(text='Send link to client', url=invite_link)
        builder.button(text='Copy link', callback_data=f'task:copy_link:{sid}')
        builder.button(text='Regenerate link', callback_data=f'task:regen_link:{sid}')
    builder.button(text='📋 Copy PDS JSON', callback_data=f'task:copy_json:{sid}')
    builder.button(text='🧩 Copy PDS Steps', callback_data=f'task:copy_steps:{sid}')
    builder.button(text='Take', callback_data=f'task:take:{sid}')
    builder.button(text='Done', callback_data=f'task:done:{sid}')
    builder.button(text='Cancel', callback_data=f'task:cancel:{sid}')
    if invite_link:
        builder.adjust(1, 2, 2, 3)
    else:
        builder.adjust(2, 3)
    return builder.as_markup()
