import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings

from bot.users.handler import router as users_router
from bot.devices.handler import router as devices_router
from bot.general.handler import router as general_router
from bot.middleware import RegistrationMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


dp.message.middleware.register(RegistrationMiddleware())

# Routers
dp.include_router(users_router)
dp.include_router(devices_router)
dp.include_router(general_router)


if __name__ == "__main__":
    logger.info("Бот Запущен")
    try:
        dp.run_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
