"""FSM states for the bot."""
from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    """States for quiz flow."""
    waiting_for_start = State()
    question_1 = State()
    question_2 = State()
    question_3 = State()
    question_4 = State()
    question_5 = State()
    waiting_for_gender = State()
    waiting_for_photo = State()
    completed = State()


class AdminStates(StatesGroup):
    """States for admin panel flows."""

    # Broadcast flow
    broadcast_viewing_users = State()      # Paginated user list
    broadcast_waiting_message = State()    # Waiting for message content
    broadcast_confirmation = State()       # Confirm before sending

    # Winners count flow
    winners_count_menu = State()           # Show current value
    winners_count_input = State()          # Input new value
    winners_count_confirm = State()        # Confirm change

    # Date flow
    date_menu = State()                    # Show current date
    date_input = State()                   # Input new date
    date_confirm = State()                 # Confirm change
