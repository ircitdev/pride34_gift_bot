"""Start command handler."""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_start_keyboard
from bot.states import QuizStates
from bot.texts import TextManager
from database.engine import async_session_maker
from database.crud import UserCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command with optional referral parameter."""
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    # Parse referral parameter from /start command
    # Format: /start ref{referrer_user_id}
    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        start_param = message.text.split()[1]
        if start_param.startswith("ref"):
            try:
                referrer_id = int(start_param[3:])  # Extract ID after "ref"
                logger.info(f"User {user_id} came via referral from {referrer_id}")
            except ValueError:
                logger.warning(f"Invalid referral parameter: {start_param}")

    # Register user in database
    async with async_session_maker() as session:
        user = await UserCRUD.get_or_create(
            session,
            user_id=user_id,
            username=username,
            full_name=full_name
        )

        # Set referrer if this is a new user and referral link was used
        if referrer_id and not user.referrer_id:
            # Verify referrer exists
            referrer = await UserCRUD.get(session, referrer_id)
            if referrer:
                await UserCRUD.set_referrer(session, user_id, referrer_id)
                logger.info(f"Set referrer {referrer_id} for user {user_id}")
            else:
                logger.warning(f"Referrer {referrer_id} not found")

    logger.info(f"User {user_id} started the bot")

    # Send welcome message with image
    welcome_image_path = settings.IMAGES_DIR / "welcome.jpg"

    # Get welcome text from TextManager
    welcome_text = TextManager.get('welcome.text')

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
