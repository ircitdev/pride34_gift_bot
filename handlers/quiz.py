"""Quiz handler."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_quiz_keyboard
from bot.states import QuizStates
from bot.quiz_data import get_quiz_questions
from database.engine import async_session_maker
from database.crud import QuizAnswerCRUD

router = Router()
logger = logging.getLogger(__name__)


async def send_question(message: Message, state: FSMContext, question_number: int):
    """Send quiz question to user."""
    if question_number > 5:
        # Quiz completed, move to gender selection
        from handlers.photo import ask_gender
        await ask_gender(message, state)
        return

    # Get questions dynamically to support text editing
    quiz_questions = get_quiz_questions()
    question_data = quiz_questions[question_number]
    question_text = question_data["text"]
    options = question_data["options"]

    # Create progress indicator
    progress = "⭐️" * question_number + "⚪️" * (5 - question_number)
    full_text = f"Вопрос {question_number}/5 {progress}\n\n{question_text}"

    await message.answer(
        text=full_text,
        reply_markup=get_quiz_keyboard(question_number, options)
    )

    # Set appropriate state
    state_map = {
        1: QuizStates.question_1,
        2: QuizStates.question_2,
        3: QuizStates.question_3,
        4: QuizStates.question_4,
        5: QuizStates.question_5
    }
    await state.set_state(state_map[question_number])


@router.callback_query(F.data.startswith("quiz_"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext):
    """Handle quiz answer."""
    await callback.answer()

    # Parse callback data: quiz_{question_number}_{answer_index}
    parts = callback.data.split("_")
    question_number = int(parts[1])
    answer_index = int(parts[2])

    # Get answer text (reload to get latest)
    quiz_questions = get_quiz_questions()
    answer_text = quiz_questions[question_number]["options"][answer_index]

    # Save answer to database
    user_id = callback.from_user.id
    async with async_session_maker() as session:
        await QuizAnswerCRUD.add_answer(
            session,
            user_id=user_id,
            question_number=question_number,
            answer=answer_text
        )

    logger.info(f"User {user_id} answered question {question_number}: {answer_text}")

    # Store answer index in state for prediction
    data = await state.get_data()
    answers = data.get("answers", [])
    answers.append(answer_index)
    await state.update_data(answers=answers)

    # Delete previous message and send next question
    await callback.message.delete()
    await send_question(callback.message, state, question_number + 1)
