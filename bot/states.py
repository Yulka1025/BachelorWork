from aiogram.fsm.state import State, StatesGroup

class CheckoutStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_address = State()
    waiting_for_payment = State()
    waiting_for_phone = State()