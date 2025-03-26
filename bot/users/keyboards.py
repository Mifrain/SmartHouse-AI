from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.users.service import UserService

auth_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔑 Логин"), KeyboardButton(text="🆕 Регистрация")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

async def get_account_keyboard(user_id):

    user_voice_mode_on = await UserService.get_user_by_tg_id(user_id)
    user_voice_mode_on = user_voice_mode_on.voice_on

    account_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✏️ Сменить логин"), KeyboardButton(text="🔑 Сменить пароль")],
            [KeyboardButton(text=f"{'Разрешить' if not user_voice_mode_on else 'Запретить'} голосовые ответы")],
            [KeyboardButton(text="🚪 Выйти")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
    )

    return account_keyboard
