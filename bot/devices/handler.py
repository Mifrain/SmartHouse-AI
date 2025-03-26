from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


from bot.devices.keyboards import *
from bot.devices.service import DeviceService
from bot.devices.states import DeviceStates, ChangeDeviceParamsStates
from bot.users.service import UserService

router = Router()

@router.message(F.text == "Устройства")
async def show_devices_menu(message: Message):
    await message.answer("🔧 Меню устройств", reply_markup=devices_menu)


@router.message(F.text == "Мои устройства")
async def my_devices(message: Message):
    devices = await DeviceService.get_user_devices(message.from_user.id)

    if devices:
        text = "📱 Ваши устройства:\n"

        keyboard = my_devices_keyboard(devices)

        await message.answer(text, reply_markup=keyboard)
    else:
        text = "❌ У вас нет добавленных устройств"
        await message.answer(text)


@router.callback_query(F.data.startswith("my_devices"))
async def my_devices(callback: CallbackQuery):
    devices = await DeviceService.get_user_devices(callback.from_user.id)

    if devices:
        text = "📱 Ваши устройства:\n"

        keyboard = my_devices_keyboard(devices)

        await callback.message.answer(text, reply_markup=keyboard)
    else:
        text = "❌ У вас нет добавленных устройств"
        await callback.message.answer(text)
        await callback.message.delete()


@router.message(F.text == "Добавить устройство")
async def add_device(message: Message, state: FSMContext):
    devices = await DeviceService.get_available_devices()

    if not devices:
        await message.answer("❌ Нет доступных устройств для добавления.")
        return

    # Используем клавиатуру из отдельного файла
    keyboard = device_keyboard(devices)

    await state.set_state(DeviceStates.choosing_device)
    await message.answer("🔍 Выберите устройство из списка:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("choose_device_"))
async def device_keyboard_callback(callback: Message, state: FSMContext):
    device_id = int(callback.data.split("_")[2])  # Получаем device_id из callback_data

    # Проверяем наличие устройства с таким id
    device = await DeviceService.get_device_by_id(device_id)
    if not device:
        await callback.answer("❌ Устройство не найдено. Попробуйте снова.")
        return

    # Сохраняем выбранное устройство в состоянии
    await state.update_data(device_id=device.id)
    await state.set_state(DeviceStates.naming_device)
    await callback.message.answer("✍ Введите название для устройства:")
    await callback.answer()  # Убираем callback-задержку


@router.message(DeviceStates.naming_device)
async def name_device(message: Message, state: FSMContext):
    data = await state.get_data()
    device_id = data["device_id"]

    user = await UserService.get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("❌ Ошибка: Пользователь не найден.")
        return

    await DeviceService.add_user_device(user.id, device_id, message.text)
    await message.answer(f"✅ Устройство '{message.text}' добавлено!", reply_markup=None)
    await state.clear()


@router.callback_query(F.data.startswith("mydevice_"))
async def device_info_handler(callback: CallbackQuery):
    device_id = int(callback.data.split("_")[1])

    device = await DeviceService.get_my_device_by_id(device_id)

    if not device:
        await callback.answer("❌ Устройство не найдено!")
        return

    params = device.params or {}
    condition = "✅ Включено" if params.get("condition") == "ON" else "❌ Выключено"

    text = f"📱 Устройство: {device.name}\n\n"

    text += f"Состояние: {condition}\n"
    text += f"Параметры: \n{'\n'.join([f"{key}: {value}" for key, value in params.items()])}\n"

    await callback.message.answer(text, reply_markup=device_info_keyboard(device))
    await callback.message.delete()


@router.callback_query(F.data.startswith("toggle_device_"))
async def toggle_device_handler(callback: CallbackQuery):
    device_id = int(callback.data.split("_")[2])

    device = await DeviceService.get_my_device_by_id(device_id)

    if not device:
        await callback.answer("❌ Устройство не найдено!")
        return

    params = device.params or {}
    current_state = params.get("condition", "OFF")

    new_state = "ON" if current_state == "OFF" else "OFF"
    params["condition"] = new_state

    await DeviceService.update_device_state(device_id, params)

    state_text = "✅ Включено" if new_state == "ON" else "❌ Выключено"
    await callback.message.answer(f"Устройство '{device.name}' теперь {state_text}")


    text = f"📱 Устройство: {device.name}\n\n"

    text += f"Состояние: {state_text}\n"
    text += f"Параметры: \n{'\n'.join([f"{key}: {value}" for key, value in params.items()])}\n"

    await callback.message.answer(text, reply_markup=device_info_keyboard(device))
    await callback.message.delete()


@router.callback_query(F.data.startswith("delete_device_"))
async def delete_device_handler(callback: CallbackQuery):
    device_id = int(callback.data.split("_")[2])

    device = await DeviceService.get_my_device_by_id(device_id)

    if not device:
        await callback.answer("❌ Устройство не найдено!")
        return

    await DeviceService.remove_user_device(device_id)

    await callback.message.answer(f"🗑 Устройство '{device.name}' было удалено.")

    await callback.answer(f"Устройство '{device.name}' удалено 🗑")

    devices = await DeviceService.get_user_devices(device_id)
    keyboard = my_devices_keyboard(devices)

    await callback.answer("📱 Ваши устройства:\n", reply_markup=keyboard)
    await callback.message.delete()



@router.callback_query(F.data.startswith("change_params_"))
async def toggle_device_handler(callback: CallbackQuery, state: FSMContext):
    device_id = int(callback.data.split("_")[2])

    await callback.message.answer(f"Введите параметр и установочное значение в формате\nParam: Value\n\nДля отмены просто введите 0")
    await state.set_state(ChangeDeviceParamsStates.new_params)
    await state.update_data(device_id=device_id)


@router.message(ChangeDeviceParamsStates.new_params)
async def register_login_handler(message: Message, state: FSMContext):
    new_params = message.text

    new_params = new_params.split(': ')

    devices = await DeviceService.get_user_devices(message.from_user.id)
    text = "📱 Ваши устройства:\n"
    keyboard = my_devices_keyboard(devices)

    if len(new_params) != 2:
        if new_params == "0":
            await message.answer(text, reply_markup=keyboard)
            await state.clear()
        else:
            await message.answer(
                f"Неверный формат!\n\nВведите параметр и установочное значение в формате\nParam: Value\n\nДля отмены просто введите 0")
            await state.set_state(ChangeDeviceParamsStates.new_params)
        return

    device_id = await state.get_value("device_id")
    device = await DeviceService.get_my_device_by_id(device_id)

    if new_params[0] not in device.params:
        await message.answer(
            f"Такого параметра не существует!!!\n\nВведите параметр и установочное значение в формате\nParam: Value\n\nДля отмены просто введите 0")
        await state.set_state(ChangeDeviceParamsStates.new_params)


    else:
        device.params[new_params[0]] = new_params[1]
        await DeviceService.update_device_state(device_id, device.params)
        await message.answer(f"Параметр изменен!")

        await message.answer(text, reply_markup=keyboard)
        await state.clear()



