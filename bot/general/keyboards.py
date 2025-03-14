from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Устройства")],
        [KeyboardButton(text="👤 Аккаунт 👤")]
    ],
    resize_keyboard=True
)