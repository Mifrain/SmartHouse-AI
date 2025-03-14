from aiogram.fsm.state import State, StatesGroup

class DeviceStates(StatesGroup):
    choosing_device = State()
    naming_device = State()
