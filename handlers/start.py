"""Start command handler."""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_start_keyboard
from bot.states import QuizStates
from database.engine import async_session_maker
from database.crud import UserCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command."""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Register user in database
    async with async_session_maker() as session:
        await UserCRUD.get_or_create(
            session,
            user_id=user_id,
            username=username,
            full_name=full_name
        )

    logger.info(f"User {user_id} started the bot")

    # Send welcome message with image
    welcome_image_path = settings.IMAGES_DIR / "welcome.jpg"

    welcome_text = (
        "<b>Новогодний квиз от СК ПРАЙД</b>\n\n"
        "Что может делать этот бот?\n\n"
        "Пройди новогодний фитнес-квиз, получи персональное предсказание "
        "на 2026 год, подарок и праздничное фото!\n\n"
        "<b>Добро пожаловать в наш новогодний фитнес-квиз!</b>\n\n"
        "Тебя ждат 5 лёгких и весёлых вопросов о том, как ты встречаешь "
        "Новый год, тренируешься, относишься к сладкому и находишь мотивацию.\n\n"
        "В конце ты получишь <b>персональное фитнес-предсказание на 2026 год</b>, "
        "а также <b>приятный бонус</b>.\n\n"
        "<b>Важно:</b> каждый участник квиза принимает участие в большом розыгрыше "
        "денежных сертификатов на шопинг! 30 декабря случайно выберем победителей. "
        "Если тебе повезёт — напишем об этом сюда.\n\n"
        "С наступающим! Пусть твой 2026 год будет ярким, успешным и энергичным!"
    )

    # Try to send image, fallback to text if image not found
    try:
        if welcome_image_path.exists():
            photo = FSInputFile(welcome_image_path)
            await message.answer_photo(
                photo=photo,
                caption=welcome_text,
                reply_markup=get_start_keyboard()
            )
        else:
            await message.answer(
                text=welcome_text,
                reply_markup=get_start_keyboard()
            )
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")
        await message.answer(
            text=welcome_text,
            reply_markup=get_start_keyboard()
        )

    await state.set_state(QuizStates.waiting_for_start)


@router.callback_query(F.data == "start_quiz")
async def start_quiz_callback(callback: CallbackQuery, state: FSMContext):
    """Handle start quiz button."""
    await callback.answer()

    # Import here to avoid circular import
    from handlers.quiz import send_question

    await callback.message.delete()
    await send_question(callback.message, state, question_number=1)
