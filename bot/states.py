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
