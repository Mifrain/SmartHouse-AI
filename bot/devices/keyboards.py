from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


devices_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мои устройства")],
        [KeyboardButton(text="Добавить устройство")],
        [KeyboardButton(text="⬅️ Назад")]
    ],
    resize_keyboard=True
)


def device_keyboard(devices):
    builder = InlineKeyboardBuilder()

    for device in devices:
        builder.row(InlineKeyboardButton(
            text=device.type,
            callback_data=f"choose_device_{device.id}"
        ))

    return builder.as_markup()


def my_devices_keyboard(devices):
    builder = InlineKeyboardBuilder()

    for device in devices:
        condition = "❌"
        if device.params and device.params.get("condition") == "ON":
            condition = "✅"

        builder.row(InlineKeyboardButton(text=f"{device.name} {condition}", callback_data=f"mydevice_{device.id}"))

    return builder.as_markup()


def device_button(device):
    condition = "✅ Включено" if "ON" in device.params.get("condition", "") else "❌ Выключено"

    # Кнопка с callback
    button = InlineKeyboardButton(
        text=f"{device.name} ({condition})",
        callback_data=f"mydevice_{device.id}"
    )
    return button


def devices_keyboard(devices):
    builder = InlineKeyboardBuilder()

    for device in devices:
        builder.add(device_button(device))

    return builder.as_markup(row_width=1)


# TO:DO Добавить кнопку чтобы изменять параметры
def device_info_keyboard(device):
    params = device.params or {}

    toggle_button = InlineKeyboardButton(
        text=f"🔄 Выключить" if params.get("condition") == "ON" else "🔄 Включить",
        callback_data=f"toggle_device_{device.id}"
    )

    change_params_button = InlineKeyboardButton(
        text="Изменение параметров",
        callback_data=f"change_params_{device.id}",
    )

    delete_button = InlineKeyboardButton(
        text="🗑 Удалить устройство",
        callback_data=f"delete_device_{device.id}"
    )

    back_button = InlineKeyboardButton(
        text="Мои Девайсы",
        callback_data=f"my_devices"
    )

    builder = InlineKeyboardBuilder()

    builder.row(toggle_button)
    builder.row(change_params_button)
    builder.row(delete_button)
    builder.row(back_button)

    return builder.as_markup()