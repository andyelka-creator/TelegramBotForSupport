import uuid

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def task_actions_markup(task_id: uuid.UUID, invite_link: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sid = str(task_id)
    if invite_link:
        builder.button(text='Отправить ссылку клиенту', url=invite_link)
        builder.button(text='Показать ссылку', callback_data=f'task:copy_link:{sid}')
        builder.button(text='Обновить ссылку', callback_data=f'task:regen_link:{sid}')
    builder.button(text='📋 Скопировать JSON для PDS', callback_data=f'task:copy_json:{sid}')
    builder.button(text='🧩 Скопировать шаги для PDS', callback_data=f'task:copy_steps:{sid}')
    builder.button(text='Взять в работу', callback_data=f'task:take:{sid}')
    builder.button(text='Готово (сисадмин)', callback_data=f'task:done:{sid}')
    builder.button(text='Отменить задачу', callback_data=f'task:cancel:{sid}')
    if invite_link:
        builder.adjust(1, 2, 2, 3)
    else:
        builder.adjust(2, 3)
    return builder.as_markup()
