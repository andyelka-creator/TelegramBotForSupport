import uuid
from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def task_actions_markup(task_id: uuid.UUID, invite_link: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    sid = str(task_id)
    if invite_link:
        share_url = f'https://t.me/share/url?url={quote_plus(invite_link)}&text={quote_plus("Заполните анкету по ссылке:")}'
        builder.button(text='Поделиться ссылкой', url=share_url)
        builder.button(text='Открыть анкету', url=invite_link)
        builder.button(text='Показать ссылку', callback_data=f'task:copy_link:{sid}')
        builder.button(text='Обновить ссылку', callback_data=f'task:regen_link:{sid}')
    builder.button(text='📋 Скопировать JSON для PDS', callback_data=f'task:copy_json:{sid}')
    builder.button(text='🧩 Скопировать шаги для PDS', callback_data=f'task:copy_steps:{sid}')
    builder.button(text='Взять в работу', callback_data=f'task:take:{sid}')
    builder.button(text='Готово (сисадмин)', callback_data=f'task:done:{sid}')
    builder.button(text='Отменить задачу', callback_data=f'task:cancel:{sid}')
    if invite_link:
        builder.adjust(2, 2, 2, 3)
    else:
        builder.adjust(2, 3)
    return builder.as_markup()
