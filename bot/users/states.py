from aiogram.fsm.state import StatesGroup, State

class AuthStates(StatesGroup):
    entering_login = State()
    entering_password = State()


class RegisterStates(StatesGroup):
    entering_login = State()
    entering_password = State()

# Сделано, чтобы middleware не прерывал работу
class ChooseActionStates(StatesGroup):
    choose_action = State()


class AccountStates(StatesGroup):
    choosing_action = State()
    entering_new_login = State()
    entering_old_password = State()
    entering_new_password = State()