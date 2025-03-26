from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.users.service import UserService
from bot.users.keyboards import auth_keyboard, get_account_keyboard
from bot.general.keyboards import main_menu
from bot.users.states import AuthStates, RegisterStates, ChooseActionStates, AccountStates

router = Router()

async def get_started_message(message: Message):
    await message.answer(
        "Выберите действие:\n\n🔑 Войти в существующий аккаунт\n🆕 Зарегистрироваться",
        reply_markup=auth_keyboard
    )


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user = await UserService.get_user_by_tg_id(message.from_user.id)

    if user:
        await message.answer(f"✅ Добро пожаловать, {user.login}!")
    else:
        await message.answer(
            "Выберите действие:\n\n🔑 Войти в существующий аккаунт\n🆕 Зарегистрироваться",
            reply_markup=auth_keyboard
        )
        await state.set_state(ChooseActionStates.choose_action)


@router.message(ChooseActionStates.choose_action, F.text.in_(["🔑 Логин", "🆕 Регистрация"]))
async def auth_choice_handler(message: Message, state: FSMContext):
    if message.text == "🔑 Логин":
        await state.set_state(AuthStates.entering_login)
        await message.answer("Введите ваш логин:\n\nДля отмены напишите 0")
    else:
        await state.set_state(RegisterStates.entering_login)
        await message.answer("Придумайте логин:\n\nДля отмены напишите 0")

# Auth
@router.message(AuthStates.entering_login)
async def auth_login_handler(message: Message, state: FSMContext):
    if message.text == "0":
        await get_started_message(message)
        await state.set_state(ChooseActionStates.choose_action)
        return

    await state.update_data(login=message.text)
    await state.set_state(AuthStates.entering_password)
    await message.answer("Теперь введите пароль:\n\nДля отмены напишите 0")


@router.message(AuthStates.entering_password)
async def auth_password_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    login = data["login"]
    password = message.text

    if password == "0":
        await get_started_message(message)
        await state.set_state(ChooseActionStates.choose_action)
        return

    if await UserService.user_exists(login) and await UserService.verify_password(login, password):
        await UserService.add_device_to_user(login, message.from_user.id)
        await message.answer("✅ Успешный вход!", reply_markup=None)
        await message.answer("Главное Меню", reply_markup=main_menu)
        await state.clear()
    else:
        await message.answer("❌ Неверный логин/пароль ❌\nПопробуйте снова.", reply_markup=None)
        await message.answer("Введите ваш логин:\n\nДля отмены напишите 0")

        await state.set_state(AuthStates.entering_login)

# Register
@router.message(RegisterStates.entering_login)
async def register_login_handler(message: Message, state: FSMContext):
    login = message.text

    if login == "0":
        await get_started_message(message)
        await state.set_state(ChooseActionStates.choose_action)
        return

    if await UserService.user_exists(login):
        await message.answer("❌ Пользователь с таким логином уже существует.\nПопробуйте другой логин или войдите в аккаунт\n\nДля отмены напишите 0")
    else:
        await state.update_data(login=login)
        await state.set_state(RegisterStates.entering_password)
        await message.answer("Теперь введите пароль:\n\nДля отмены напишите 0")


@router.message(RegisterStates.entering_password)
async def register_password_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    login = data["login"]
    password = message.text

    if len(password) < 8:
        await message.answer("Пароль должен быть минимум 8 символов\n\nДля отмены напишите 0")
        return

    if password == "0":
        await get_started_message(message)
        await state.set_state(ChooseActionStates.choose_action)
        return

    await UserService.create_user(login, password, message.from_user.id)

    await message.answer("✅ Аккаунт создан! Теперь вы можете войти с любого устройства.", reply_markup=None)
    await message.answer("Главное Меню", reply_markup=main_menu)
    await state.clear()

# logout
@router.message(F.text == "🚪 Выйти")
async def logout_handler(message: Message, state: FSMContext):
    """Выход из аккаунта"""
    user = await UserService.get_user_by_tg_id(message.from_user.id)

    if user:
        await UserService.delete_session(user.id)
        await message.answer("✅ Вы вышли из аккаунта\n\nВыберите действие:\n\n🔑 Войти в существующий аккаунт\n🆕 Зарегистрироваться", reply_markup=auth_keyboard)
        await state.set_state(ChooseActionStates.choose_action)
    else:
        await message.answer("❌ Ошибка: пользователь не найден.")

    await state.clear()

# Account
@router.message(F.text == "👤 Аккаунт 👤")
async def account_handler(message: Message, state: FSMContext):
    await message.answer("🔧 Настройки аккаунта:", reply_markup=await get_account_keyboard(message.from_user.id))
    await state.set_state(AccountStates.choosing_action)

# Account Edit
@router.message( F.text == "✏️ Сменить логин")
async def change_login_start(message: Message, state: FSMContext):
    """Запрос нового логина"""
    await state.set_state(AccountStates.entering_new_login)
    await message.answer("✏️ Введите новый логин:\n\nДля отмены напишите 0")


@router.message(AccountStates.entering_new_login)
async def change_login_confirm(message: Message, state: FSMContext):
    """Смена логина"""
    new_login = message.text

    if new_login == "0":
        await message.answer("❌ Отменено.", reply_markup=await get_account_keyboard(message.from_user.id))
        await state.clear()
        return

    user = await UserService.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден.")
        await state.clear()
        return

    success = await UserService.change_login(user.id, new_login)
    if success:
        await message.answer("✅ Логин успешно изменен!", reply_markup=await get_account_keyboard(message.from_user.id))
    else:
        await message.answer("❌ Этот логин уже занят. Попробуйте другой.")

    await state.clear()


@router.message(F.text == "🔑 Сменить пароль")
async def change_password_start(message: Message, state: FSMContext):
    """Запрос старого пароля"""
    await state.set_state(AccountStates.entering_old_password)
    await message.answer("🔑 Введите старый пароль:\n\nДля отмены напишите 0")


@router.message(AccountStates.entering_old_password)
async def change_password_old_check(message: Message, state: FSMContext):
    """Проверка старого пароля"""
    old_password = message.text

    if old_password == "0":
        await message.answer("❌ Отменено.", reply_markup=await get_account_keyboard(message.from_user.id))
        await state.clear()
        return

    user = await UserService.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден.")
        await state.clear()
        return

    if not await UserService.verify_password(user.login, old_password):
        await message.answer("❌ Неверный пароль. Попробуйте снова.")
        return

    await state.update_data(old_password=old_password)
    await state.set_state(AccountStates.entering_new_password)
    await message.answer("✅ Старый пароль подтвержден. Теперь введите новый пароль:")


@router.message(AccountStates.entering_new_password)
async def change_password_confirm(message: Message, state: FSMContext):
    """Изменение пароля"""
    new_password = message.text

    if new_password == "0":
        await message.answer("❌ Отменено.", reply_markup=await get_account_keyboard(message.from_user.id))
        await state.clear()
        return

    data = await state.get_data()
    old_password = data.get("old_password")

    user = await UserService.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка: пользователь не найден.")
        await state.clear()
        return

    success = await UserService.change_password(user.id, old_password, new_password)
    if success:
        await message.answer("✅ Пароль успешно изменен!", reply_markup=await get_account_keyboard(message.from_user.id))
    else:
        await message.answer("❌ Ошибка при изменении пароля.")

    await state.clear()


@router.message(F.text.in_(["Запретить голосовые ответы", "Разрешить голосовые ответы"]))
async def change_user_voice_mode_handler(message: Message):

    if message.text == "Запретить голосовые ответы":
        change = False
    else:
        change = True
    print(message.from_user.id)
    await UserService.change_voice_on(message.from_user.id, change)

    await message.answer(f"Голосовые ответы {'включены' if change else 'выключены'}! ", reply_markup=await get_account_keyboard(message.from_user.id))
