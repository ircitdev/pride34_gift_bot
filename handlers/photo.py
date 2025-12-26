"""Photo handling and gender selection."""
import logging
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_gender_keyboard, get_share_keyboard
from bot.states import QuizStates
from bot.quiz_data import get_prediction
from database.engine import async_session_maker
from database.crud import UserCRUD, UserPhotoCRUD
from config import settings
from services.image_processor import ImageProcessor
from services.forum_service import ForumService

router = Router()
logger = logging.getLogger(__name__)


async def ask_gender(message: Message, state: FSMContext):
    """Ask user to select gender."""
    text = (
        "Отлично! Квиз завершён!\n\n"
        "Ну что, добавим немного новогоднего волшебства?\n\n"
        "Давай сделаем для тебя праздничное фото — такое, чтобы "
        "захотелось сохранить и поделиться.\n\n"
        "Для начала подскажи свой пол:"
    )

    await message.answer(
        text=text,
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(QuizStates.waiting_for_gender)


@router.callback_query(F.data.startswith("gender_"))
async def handle_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Handle gender selection."""
    await callback.answer()

    gender = "male" if callback.data == "gender_male" else "female"
    user_id = callback.from_user.id

    # Save gender to database
    async with async_session_maker() as session:
        await UserCRUD.set_gender(session, user_id, gender)

    logger.info(f"User {user_id} selected gender: {gender}")

    # Store gender in state
    await state.update_data(gender=gender)

    # Ask for photo
    text = (
        "Теперь отправь улыбчивое фото, в хорошем качестве, где видно "
        "твоё лицо\n\n"
        "Желательно, чтобы ты был один в кадре — так магия сработает лучше\n\n"
        "<i>Примечание: Фото используется только для создания вашего новогоднего "
        "образа и не сохраняется после генерации.</i>"
    )

    await callback.message.delete()
    await callback.message.answer(text=text)
    await state.set_state(QuizStates.waiting_for_photo)


@router.message(QuizStates.waiting_for_photo, F.photo)
async def handle_photo_upload(message: Message, state: FSMContext):
    """Handle photo upload from user."""
    user_id = message.from_user.id

    # Get the largest photo
    photo = message.photo[-1]
    file_id = photo.file_id

    # Download photo
    file_info = await message.bot.get_file(file_id)
    file_path = settings.USER_PHOTOS_DIR / f"{user_id}.jpg"

    await message.bot.download_file(file_info.file_path, file_path)
    logger.info(f"User {user_id} uploaded photo, saved to {file_path}")

    # Save photo info to database
    async with async_session_maker() as session:
        await UserPhotoCRUD.add_photo(
            session,
            user_id=user_id,
            file_id=file_id,
            file_path=str(file_path)
        )
        await UserCRUD.update_photo_status(session, user_id, uploaded=True)

    # Send processing message
    processing_msg = await message.answer(
        "Колдуем над твоим новогодним образом ✨\n\n"
        "Ещё пару мгновений — и всё будет готово"
    )

    # Get user data
    data = await state.get_data()
    gender = data.get("gender", "male")
    answers = data.get("answers", [])

    # Process image
    try:
        processor = ImageProcessor()
        generated_path = await processor.create_christmas_figure(
            user_photo_path=file_path,
            gender=gender,
            user_id=user_id
        )

        # Update database with generated path
        async with async_session_maker() as session:
            await UserPhotoCRUD.update_generated_path(session, user_id, str(generated_path))
            await UserCRUD.update_quiz_status(session, user_id, completed=True)

        # Delete processing message
        await processing_msg.delete()

        # Send result to user
        await send_final_result(message, state, generated_path, answers)

        # Create forum topic with user data
        try:
            await ForumService.create_user_topic(
                bot=message.bot,
                user_id=user_id,
                username=message.from_user.username or "",
                full_name=message.from_user.full_name or "",
                gender=gender,
                quiz_answers=answers,
                user_photo_path=file_path,
                generated_photo_path=generated_path
            )
        except Exception as forum_error:
            logger.error(f"Error creating forum topic for user {user_id}: {forum_error}")

    except Exception as e:
        logger.error(f"Error processing image for user {user_id}: {e}")
        await processing_msg.delete()
        await message.answer(
            "Произошла ошибка при обработке фото. Попробуйте отправить другое фото."
        )


async def send_final_result(message: Message, state: FSMContext, image_path: Path, answers: list):
    """Send final result with prediction and generated image."""
    # Get prediction
    prediction = get_prediction(answers)

    # Prepare final message
    final_text = (
        f"<b>Готово!</b>\n\n"
        f"{prediction}\n\n"
        f"<b>Специальное предложение для тебя:</b>\n"
        f"Скидка 20% на PRIDE Fitness FEST по промокоду <code>НОВЫЙФЕСТ</code>\n\n"
        f"👉 Нажми и купи билеты по выгодной цене\n\n"
        f"<i>Промокод действует до 15.01.2026</i>\n\n"
        f"Делись этим новогодним фото в своих социальных сетях с хештегом "
        f"<b>#PRIDEFitnessКвиз</b>. Пусть твои друзья тоже пройдут наш квиз, "
        f"получат фитнес-предсказание и праздничное фото.\n\n"
        f"А ещё ты теперь участвуешь в нашем <b>большом розыгрыше денежных "
        f"сертификатов на шопинг!</b> 30 декабря случайно выберем победителей. "
        f"Если тебе повезёт — напишем об этом сюда.\n\n"
        f"С наступающим! Пусть твой 2026 год будет ярким, успешным и энергичным!"
    )

    # Send photo with text
    try:
        photo = FSInputFile(image_path)
        await message.answer_photo(
            photo=photo,
            caption=final_text,
            reply_markup=get_share_keyboard()
        )
    except Exception as e:
        logger.error(f"Error sending final result: {e}")
        await message.answer(
            text=final_text,
            reply_markup=get_share_keyboard()
        )

    await state.set_state(QuizStates.completed)


@router.message(QuizStates.waiting_for_photo)
async def handle_invalid_photo(message: Message):
    """Handle invalid photo uploads."""
    await message.answer(
        "Пожалуйста, отправьте фото (не файл и не документ).\n\n"
        "Фото должно быть в хорошем качестве, где чётко видно ваше лицо."
    )
