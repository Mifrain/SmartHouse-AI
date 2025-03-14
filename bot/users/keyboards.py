from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


auth_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔑 Логин"), KeyboardButton(text="🆕 Регистрация")]],
    resize_keyboard=True,
    one_time_keyboard=True
)


account_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✏️ Сменить логин"), KeyboardButton(text="🔑 Сменить пароль")],
        [KeyboardButton(text="🚪 Выйти")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True,
)
