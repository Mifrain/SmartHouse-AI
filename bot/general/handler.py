from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.general.keyboards import main_menu

router = Router()


@router.message(Command("menu"))
async def show_main_menu(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_menu)

@router.message(F.text == "⬅️ Назад")
async def go_back(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_menu)


# Для работы Мидлвейра
# Можно перенести, но пока оставить
@router.message()
async def default_handler(message: Message):
    await message.answer("Я не понимаю этот запрос")

