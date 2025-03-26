from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from bot.devices.service import DeviceService
from bot.general.keyboards import main_menu
from bot.AI.llm import process_user_input
router = Router()


@router.message(Command("menu"))
async def show_main_menu(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_menu)

@router.message(F.text == "⬅️ Назад")
async def go_back(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_menu)


@router.message()
async def default_handler(message: Message):
    answer = await process_user_input(message.text, message.from_user.id)
    await message.answer(answer)

