from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


control_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Помощь'), KeyboardButton(text='Активные задачи')],
        [KeyboardButton(text='Кто я'), KeyboardButton(text='Меню')],
        [KeyboardButton(text='Новая карта'), KeyboardButton(text='Замена карты')],
        [KeyboardButton(text='Создать пополнение')],
    ],
    resize_keyboard=True,
)
