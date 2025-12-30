"""Quiz handler."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_quiz_keyboard
from bot.states import QuizStates
from bot.quiz_data import get_quiz_questions, get_prediction
from database.engine import async_session_maker
from database.crud import QuizAnswerCRUD

router = Router()
logger = logging.getLogger(__name__)


async def send_question(message: Message, state: FSMContext, question_number: int):
    """Send quiz question to user."""
    logger.info(f"🎯 SEND_QUESTION: Called with question_number={question_number}")

    if question_number > 5:
        # Quiz completed, move to gender selection
        logger.info(f"🎯 SEND_QUESTION: Quiz completed, calling ask_gender")
        from handlers.photo import ask_gender
        try:
            await ask_gender(message, state)
            logger.info(f"✅ SEND_QUESTION: ask_gender completed")
        except Exception as e:
            logger.error(f"❌ SEND_QUESTION: Error calling ask_gender: {e}", exc_info=True)
            raise
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


async def show_quiz_result(callback: CallbackQuery, state: FSMContext):
    """Show quiz result with prediction."""
    logger.info(f"🎊 SHOW_QUIZ_RESULT: Starting for user {callback.from_user.id}")

    # Get answers from state
    data = await state.get_data()
    answers = data.get("answers", [])
    logger.info(f"🎊 SHOW_QUIZ_RESULT: Got answers: {answers}")

    # Get prediction
    prediction = get_prediction(answers)
    logger.info(f"🎊 SHOW_QUIZ_RESULT: Generated prediction")

    # Prepare result message
    result_text = (
        f"<b>🎉 Квиз завершен!</b>\n\n"
        f"<b>Твой результат:</b>\n\n"
        f"{prediction}\n\n"
        f"Готов создать свою персонализированную новогоднюю фигурку?"
    )

    # Create continue button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Создать фигурку!", callback_data="quiz_continue")]
    ])

    await callback.message.answer(
        text=result_text,
        reply_markup=keyboard
    )
    logger.info(f"✅ SHOW_QUIZ_RESULT: Result sent to user {callback.from_user.id}")


@router.callback_query(F.data == "quiz_continue")
async def handle_quiz_continue(callback: CallbackQuery, state: FSMContext):
    """Handle continue after quiz result."""
    logger.info(f"👤 QUIZ_CONTINUE: User {callback.from_user.id} clicked continue")
    await callback.answer()

    # Now ask for gender
    from handlers.photo import ask_gender_from_callback
    try:
        await ask_gender_from_callback(callback, state)
        logger.info(f"✅ QUIZ_CONTINUE: ask_gender_from_callback completed")
    except Exception as e:
        logger.error(f"❌ QUIZ_CONTINUE: Error calling ask_gender: {e}", exc_info=True)
        raise


async def send_question_from_callback(callback: CallbackQuery, state: FSMContext, question_number: int):
    """Send quiz question from callback (after answer)."""
    logger.info(f"🎯 SEND_QUESTION_FROM_CALLBACK: Called with question_number={question_number}")

    if question_number > 5:
        # Quiz completed, show result first
        logger.info(f"🎯 SEND_QUESTION_FROM_CALLBACK: Quiz completed, showing result")
        try:
            await show_quiz_result(callback, state)
            logger.info(f"✅ SEND_QUESTION_FROM_CALLBACK: Quiz result shown")
        except Exception as e:
            logger.error(f"❌ SEND_QUESTION_FROM_CALLBACK: Error showing result: {e}", exc_info=True)
            raise
        return

    # Get questions dynamically to support text editing
    quiz_questions = get_quiz_questions()
    question_data = quiz_questions[question_number]
    question_text = question_data["text"]
    options = question_data["options"]

    # Create progress indicator
    progress = "⭐️" * question_number + "⚪️" * (5 - question_number)
    full_text = f"Вопрос {question_number}/5 {progress}\n\n{question_text}"

    await callback.message.answer(
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
    try:
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Starting handler")
        await callback.answer()
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Callback answered")

        # Parse callback data: quiz_{question_number}_{answer_index}
        parts = callback.data.split("_")
        question_number = int(parts[1])
        answer_index = int(parts[2])
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Parsed question={question_number}, answer={answer_index}")

        # Get answer text (reload to get latest)
        quiz_questions = get_quiz_questions()
        answer_text = quiz_questions[question_number]["options"][answer_index]
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Got answer text: {answer_text}")

        # Save answer to database
        user_id = callback.from_user.id
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Saving to database for user {user_id}")
        async with async_session_maker() as session:
            await QuizAnswerCRUD.add_answer(
                session,
                user_id=user_id,
                question_number=question_number,
                answer=answer_text
            )
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Database save completed")

        logger.info(f"User {user_id} answered question {question_number}: {answer_text}")

        # Store answer index in state for prediction
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Getting state data")
        data = await state.get_data()
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Got state data: {data}")
        answers = data.get("answers", [])
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Current answers: {answers}")
        answers.append(answer_index)
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Updated answers: {answers}")
        await state.update_data(answers=answers)
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Stored answers, total count: {len(answers)}")

        # Delete previous message
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Deleting previous message")
        await callback.message.delete()
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Deleted previous message, about to send question {question_number + 1}")

        # Send next question - use callback to have correct user context
        logger.info(f"📋 HANDLE_QUIZ_ANSWER: Calling send_question_from_callback")
        await send_question_from_callback(callback, state, question_number + 1)
        logger.info(f"✅ HANDLE_QUIZ_ANSWER: Completed for question {question_number}")
    except Exception as e:
        logger.error(f"❌ HANDLE_QUIZ_ANSWER: EXCEPTION: {e}", exc_info=True)
        try:
            await callback.message.answer(f"❌ Произошла ошибка при обработке ответа: {e}\nПопробуйте еще раз с /start")
        except:
            pass
        raise
