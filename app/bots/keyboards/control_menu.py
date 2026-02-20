from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


control_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Помощь'), KeyboardButton(text='Активные задачи')],
        [KeyboardButton(text='Кто я'), KeyboardButton(text='Меню')],
        [KeyboardButton(text='Создать выпуск'), KeyboardButton(text='Создать замену')],
        [KeyboardButton(text='Создать пополнение')],
    ],
    resize_keyboard=True,
)
