import logging

from aiogram import BaseMiddleware
from aiogram.types import Message, ReplyKeyboardRemove
from bot.users.service import UserService


logger = logging.getLogger(__name__)


class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            if isinstance(event, Message):
                user_id = event.from_user.id
                state = data.get("state")
                if state is not None and await state.get_state() is not None:
                    return await handler(event, data)

                if (await UserService.get_user_by_tg_id(user_id) is None) and event.text != "/start":
                    await event.answer(
                        "Вы не зарегистрированы. Пожалуйста, начните регистрацию, вызвав команду /start.",
                        reply_markup=ReplyKeyboardRemove(),
                    )
                    return

            return await handler(event, data)

        except Exception as e:
            logger.error(
                "Ошибка: %s, User: %s, Msg: %s",
                str(e),
                event.from_user.id if isinstance(event, Message) else "N/A",
                event.text if isinstance(event, Message) else "N/A",
            )
            if isinstance(event, Message):
                await event.answer("Произошла ошибка. Попробуйте позже.")
            return None