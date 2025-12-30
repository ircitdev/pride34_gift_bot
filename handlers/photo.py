"""Photo handling and gender selection."""
import logging
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.keyboards import get_gender_keyboard, get_share_keyboard
from bot.states import QuizStates
from bot.quiz_data import get_prediction
from bot.texts import TextManager
from database.engine import async_session_maker
from database.crud import UserCRUD, UserPhotoCRUD, QuizAnswerCRUD
from config import settings
from services.image_processor import ImageProcessor
from services.forum_service import ForumService

router = Router()
logger = logging.getLogger(__name__)


async def ask_gender(message: Message, state: FSMContext):
    """Ask user to select gender."""
    user_id = message.from_user.id
    logger.info(f"👤 ASK_GENDER: Starting for user {user_id}")

    # Get text from TextManager
    text = TextManager.get('gender.text')
    logger.info(f"👤 ASK_GENDER: Got text from TextManager")

    try:
        await message.answer(
            text=text,
            reply_markup=get_gender_keyboard()
        )
        logger.info(f"✅ ASK_GENDER: Gender selection sent to user {user_id}")
    except Exception as e:
        logger.error(f"❌ ASK_GENDER: Error sending gender selection: {e}", exc_info=True)
        raise

    await state.set_state(QuizStates.waiting_for_gender)
    logger.info(f"✅ ASK_GENDER: State set to waiting_for_gender")


async def ask_gender_from_callback(callback: CallbackQuery, state: FSMContext):
    """Ask user to select gender (from callback after quiz)."""
    user_id = callback.from_user.id
    logger.info(f"👤 ASK_GENDER_FROM_CALLBACK: Starting for user {user_id}")

    # Get text from TextManager
    text = TextManager.get('gender.text')
    logger.info(f"👤 ASK_GENDER_FROM_CALLBACK: Got text from TextManager")

    try:
        await callback.message.answer(
            text=text,
            reply_markup=get_gender_keyboard()
        )
        logger.info(f"✅ ASK_GENDER_FROM_CALLBACK: Gender selection sent to user {user_id}")
    except Exception as e:
        logger.error(f"❌ ASK_GENDER_FROM_CALLBACK: Error sending gender selection: {e}", exc_info=True)
        raise

    await state.set_state(QuizStates.waiting_for_gender)
    logger.info(f"✅ ASK_GENDER_FROM_CALLBACK: State set to waiting_for_gender")


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

    # Ask for photo (get text from TextManager)
    text = TextManager.get('photo.text')

    await callback.message.delete()
    await callback.message.answer(text=text)
    await state.set_state(QuizStates.waiting_for_photo)


@router.message(QuizStates.waiting_for_photo, F.photo)
async def handle_photo_upload(message: Message, state: FSMContext):
    """Handle photo upload from user."""
    user_id = message.from_user.id
    logger.info(f"📸 PHOTO HANDLER: Started for user {user_id}")

    # Check current state
    current_state = await state.get_state()
    logger.info(f"📸 PHOTO HANDLER: Current state = {current_state}")

    try:
        # Get the largest photo
        photo = message.photo[-1]
        file_id = photo.file_id
        logger.info(f"📸 PHOTO HANDLER: Got photo file_id: {file_id}")

        # Download photo
        file_info = await message.bot.get_file(file_id)
        file_path = settings.USER_PHOTOS_DIR / f"{user_id}.jpg"
        logger.info(f"📸 PHOTO HANDLER: Downloading to {file_path}")

        await message.bot.download_file(file_info.file_path, file_path)
        logger.info(f"📸 PHOTO HANDLER: Photo downloaded successfully to {file_path}")
    except Exception as download_error:
        logger.error(f"❌ PHOTO HANDLER: Download error: {download_error}", exc_info=True)
        await message.answer("Произошла ошибка при загрузке фото. Попробуйте еще раз.")
        return

    # Check if face is detected in photo
    logger.info(f"🔍 PHOTO HANDLER: Starting face detection")
    try:
        import cv2
        img = cv2.imread(str(file_path))

        if img is None:
            logger.error(f"❌ PHOTO HANDLER: Failed to read image file {file_path}")
            await message.answer("Произошла ошибка при обработке фото. Попробуйте отправить другое фото.")
            file_path.unlink()
            return

        logger.info(f"🔍 PHOTO HANDLER: Image loaded, shape: {img.shape}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        logger.info(f"🔍 PHOTO HANDLER: Detected {len(faces)} face(s)")

        if len(faces) == 0:
            logger.warning(f"⚠️ PHOTO HANDLER: No faces detected, asking user to resend")
            await message.answer(
                "❌ К сожалению, на вашем фото не обнаружено лицо.\n\n"
                "Пожалуйста, отправьте фото где:\n"
                "• Видно ваше лицо\n"
                "• Вы смотрите в камеру\n"
                "• Хорошее освещение\n"
                "• Вы один в кадре"
            )
            file_path.unlink()  # Delete invalid photo
            return
    except Exception as face_error:
        logger.error(f"❌ PHOTO HANDLER: Face detection error: {face_error}", exc_info=True)
        await message.answer("Произошла ошибка при обработке фото. Попробуйте отправить другое фото.")
        if file_path.exists():
            file_path.unlink()
        return

    # Save photo info to database
    logger.info(f"💾 PHOTO HANDLER: Saving photo info to database")
    try:
        async with async_session_maker() as session:
            await UserPhotoCRUD.add_photo(
                session,
                user_id=user_id,
                file_id=file_id,
                file_path=str(file_path)
            )
            await UserCRUD.update_photo_status(session, user_id, uploaded=True)
        logger.info(f"✅ PHOTO HANDLER: Photo info saved to database")
    except Exception as db_error:
        logger.error(f"❌ PHOTO HANDLER: Database error: {db_error}", exc_info=True)
        await message.answer("Произошла ошибка при сохранении данных. Попробуйте еще раз.")
        return

    # Send processing message with hourglass animation
    logger.info(f"⏳ PHOTO HANDLER: Sending processing message")
    processing_msg = await message.answer(
        "⏳ Колдуем над твоим новогодним образом ✨\n\n"
        "Ещё пару мгновений — и всё будет готово"
    )

    # Get user data
    logger.info(f"📋 PHOTO HANDLER: Getting user data from state")
    data = await state.get_data()
    gender = data.get("gender", "male")
    answers = data.get("answers", [])
    logger.info(f"📋 PHOTO HANDLER: Gender={gender}, Answers count={len(answers)}")

    # Process image with periodic chat action updates
    logger.info(f"🎨 PHOTO HANDLER: Starting image generation")
    import asyncio

    async def send_typing_periodically():
        """Send typing action every 4 seconds to keep animation alive"""
        while True:
            try:
                await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
                await asyncio.sleep(4)
            except:
                break

    typing_task = asyncio.create_task(send_typing_periodically())

    try:
        processor = ImageProcessor()
        logger.info(f"🎨 PHOTO HANDLER: ImageProcessor created, calling create_christmas_figure")
        generated_path = await processor.create_christmas_figure(
            user_photo_path=file_path,
            gender=gender,
            user_id=user_id
        )
        typing_task.cancel()  # Stop typing animation
        logger.info(f"✅ PHOTO HANDLER: Image generated successfully: {generated_path}")

        # Update database with generated path
        logger.info(f"💾 PHOTO HANDLER: Updating database with generated path")
        async with async_session_maker() as session:
            await UserPhotoCRUD.update_generated_path(session, user_id, str(generated_path))
            await UserCRUD.update_quiz_status(session, user_id, completed=True)
        logger.info(f"✅ PHOTO HANDLER: Database updated")

        # Delete processing message
        logger.info(f"🗑️ PHOTO HANDLER: Deleting processing message")
        await processing_msg.delete()

        # Send result to user
        logger.info(f"📤 PHOTO HANDLER: Sending final result to user")
        await send_final_result(message, state, generated_path, answers)
        logger.info(f"✅ PHOTO HANDLER: Final result sent")

        # Create forum topic with user data
        logger.info(f"📝 PHOTO HANDLER: Creating forum topic")
        try:
            # Get user data with pride_gift_id and referrer info
            logger.info(f"📝 PHOTO HANDLER: Getting user data for forum topic")
            async with async_session_maker() as session:
                user = await UserCRUD.get(session, user_id)
                if not user:
                    logger.error(f"User {user_id} not found in database")
                    raise ValueError(f"User {user_id} not found")

                # Get quiz answers from database (text, not indices)
                quiz_answers_db = await QuizAnswerCRUD.get_user_answers(session, user_id)
                quiz_answers_text = [qa.answer for qa in quiz_answers_db]

                # Get referrer information if exists
                referrer_id = user.referrer_id if user.referrer_id else None
                referrer_topic_id = None
                referrer_pride_gift_id = None

                if referrer_id:
                    referrer = await UserCRUD.get(session, referrer_id)
                    if referrer:
                        referrer_topic_id = referrer.forum_topic_id
                        referrer_pride_gift_id = referrer.pride_gift_id
                        logger.info(f"User {user_id} was referred by {referrer_id}")

            # Create topic and STORE topic_id
            topic_id = await ForumService.create_user_topic(
                bot=message.bot,
                user_id=user_id,
                pride_gift_id=user.pride_gift_id,
                username=message.from_user.username or "",
                full_name=message.from_user.full_name or "",
                gender=gender,
                quiz_answers=quiz_answers_text,
                user_photo_path=file_path,
                generated_photo_path=generated_path,
                referrer_id=referrer_id,
                referrer_topic_id=referrer_topic_id,
                referrer_pride_gift_id=referrer_pride_gift_id
            )

            # ✨ НОВОЕ: Сохранить topic_id в базе данных
            if topic_id > 0:
                async with async_session_maker() as session:
                    await UserCRUD.update_forum_topic(session, user_id, topic_id)
                    # Отметить пользователя как завершившего квиз
                    await UserCRUD.mark_quiz_completed(session, user_id)
                logger.info(f"Stored topic_id {topic_id} and marked quiz completed for user {user_id}")

        except Exception as forum_error:
            logger.error(f"Error creating forum topic for user {user_id}: {forum_error}")

    except Exception as e:
        typing_task.cancel()  # Stop typing animation on error
        logger.error(f"❌ PHOTO HANDLER: Error processing image for user {user_id}: {e}", exc_info=True)
        try:
            await processing_msg.delete()
        except:
            pass
        await message.answer(
            "Произошла ошибка при обработке фото. Попробуйте отправить другое фото."
        )
        logger.info(f"❌ PHOTO HANDLER: Error message sent to user")


async def send_final_result(message: Message, state: FSMContext, image_path: Path, answers: list):
    """Send final result with prediction and generated image."""
    logger.info(f"📊 SEND_FINAL_RESULT: Starting for user {message.from_user.id}")

    # Get prediction
    prediction = get_prediction(answers)
    logger.info(f"📊 SEND_FINAL_RESULT: Prediction generated")

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

    # Get bot info for username
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    user_id = message.from_user.id

    # Check if user has Telegram Premium
    has_premium = message.from_user.is_premium or False

    # Send photo with text
    logger.info(f"📤 SEND_FINAL_RESULT: Sending photo to user")
    try:
        photo = FSInputFile(image_path)
        await message.answer_photo(
            photo=photo,
            caption=final_text,
            reply_markup=get_share_keyboard(bot_username, user_id, has_premium)
        )
        logger.info(f"✅ SEND_FINAL_RESULT: Photo sent successfully")
    except Exception as e:
        logger.error(f"❌ SEND_FINAL_RESULT: Error sending photo: {e}", exc_info=True)
        logger.info(f"📤 SEND_FINAL_RESULT: Sending as text message instead")
        await message.answer(
            text=final_text,
            reply_markup=get_share_keyboard(bot_username, user_id, has_premium)
        )

    logger.info(f"✅ SEND_FINAL_RESULT: Setting state to completed")
    await state.set_state(QuizStates.completed)
    logger.info(f"✅ SEND_FINAL_RESULT: Complete")


@router.message(QuizStates.waiting_for_photo)
async def handle_invalid_photo(message: Message):
    """Handle invalid photo uploads."""
    await message.answer(
        "Пожалуйста, отправьте фото (не файл и не документ).\n\n"
        "Фото должно быть в хорошем качестве, где чётко видно ваше лицо."
    )


@router.callback_query(F.data == "share_with_friends")
async def handle_share_with_friends(callback: CallbackQuery):
    """Handle 'Рассказать друзьям' button - opens contact list with referral link."""
    user_id = callback.from_user.id

    # Get bot info for username
    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username

    # Generate referral link
    from database.crud import UserCRUD
    referral_link = UserCRUD.generate_referral_link(bot_username, user_id)

    # Create sharing text
    share_text = (
        f"🎄 Привет! Я прошёл новогодний квиз от PRIDE Fitness и получил своё фитнес-предсказание на 2026 год!\n\n"
        f"Попробуй и ты — узнай, что тебя ждёт в новом году, и получи классное праздничное фото! 🎁\n\n"
        f"👉 {referral_link}"
    )

    # Answer callback
    await callback.answer(
        text="Нажмите на кнопку ниже, чтобы выбрать друзей для отправки",
        show_alert=False
    )

    # Create keyboard with contact picker button
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton, SwitchInlineQueryChosenChat

    builder = InlineKeyboardBuilder()

    # Create SwitchInlineQueryChosenChat object for contact picker
    switch_inline = SwitchInlineQueryChosenChat(
        query=share_text,
        allow_user_chats=True,
        allow_bot_chats=False,
        allow_group_chats=False,
        allow_channel_chats=False
    )

    builder.row(
        InlineKeyboardButton(
            text="📤 Выбрать друзей и отправить",
            switch_inline_query_chosen_chat=switch_inline
        )
    )
    builder.button(
        text="◀️ Назад",
        callback_data="close_share_menu"
    )

    await callback.message.edit_reply_markup(reply_markup=builder.as_markup())


@router.callback_query(F.data == "close_share_menu")
async def handle_close_share_menu(callback: CallbackQuery):
    """Return to original share keyboard."""
    await callback.answer()

    user_id = callback.from_user.id

    # Get bot info
    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username

    # Check if user has Telegram Premium
    has_premium = callback.from_user.is_premium or False

    # Restore original keyboard
    await callback.message.edit_reply_markup(
        reply_markup=get_share_keyboard(bot_username, user_id, has_premium)
    )


@router.callback_query(F.data.startswith("share_instagram_"))
async def handle_instagram_story_share(callback: CallbackQuery):
    """Handle Instagram Stories sharing."""
    user_id = callback.from_user.id

    # Get bot info
    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username

    # Generate referral link
    from database.crud import UserCRUD
    referral_link = UserCRUD.generate_referral_link(bot_username, user_id)

    # Get user's generated photo from database
    async with async_session_maker() as session:
        photo = await UserPhotoCRUD.get_photo(session, user_id)
        if not photo or not photo.generated_path:
            await callback.answer("Открытка не найдена. Пройдите квиз заново.", show_alert=True)
            return

    # Instruction message
    instruction_text = (
        f"📸 <b>Как опубликовать в Instagram Stories:</b>\n\n"
        f"1️⃣ Сохраните открытку на устройство (нажмите на фото → Сохранить)\n"
        f"2️⃣ Откройте Instagram\n"
        f"3️⃣ Нажмите ➕ → История\n"
        f"4️⃣ Выберите сохранённую открытку\n"
        f"5️⃣ Добавьте стикер \"Ссылка\" и вставьте:\n"
        f"<code>{referral_link}</code>\n\n"
        f"6️⃣ Опубликуйте! 🎉\n\n"
        f"<i>Ваши друзья смогут перейти по ссылке и пройти квиз</i>"
    )

    await callback.answer()
    await callback.message.answer(text=instruction_text)


@router.callback_query(F.data.startswith("share_vk_"))
async def handle_vk_story_share(callback: CallbackQuery):
    """Handle VK Stories sharing."""
    user_id = callback.from_user.id

    # Get bot info
    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username

    # Generate referral link
    from database.crud import UserCRUD
    referral_link = UserCRUD.generate_referral_link(bot_username, user_id)

    # Get user's generated photo
    async with async_session_maker() as session:
        photo = await UserPhotoCRUD.get_photo(session, user_id)
        if not photo or not photo.generated_path:
            await callback.answer("Открытка не найдена. Пройдите квиз заново.", show_alert=True)
            return

    # Instruction message
    instruction_text = (
        f"📱 <b>Как опубликовать в VK Stories:</b>\n\n"
        f"1️⃣ Сохраните открытку на устройство (нажмите на фото → Сохранить)\n"
        f"2️⃣ Откройте ВКонтакте\n"
        f"3️⃣ Нажмите на камеру (создать историю)\n"
        f"4️⃣ Выберите сохранённую открытку\n"
        f"5️⃣ Добавьте текст или стикер \"Ссылка\" и вставьте:\n"
        f"<code>{referral_link}</code>\n\n"
        f"6️⃣ Опубликуйте! 🎉\n\n"
        f"<i>Ваши друзья смогут перейти по ссылке и пройти квиз</i>"
    )

    await callback.answer()
    await callback.message.answer(text=instruction_text)


@router.callback_query(F.data.startswith("share_tg_story_"))
async def handle_telegram_story_share(callback: CallbackQuery):
    """Handle Telegram Stories sharing (Premium only)."""
    user_id = callback.from_user.id

    if not callback.from_user.is_premium:
        await callback.answer(
            "Эта функция доступна только для Telegram Premium подписчиков",
            show_alert=True
        )
        return

    # Get bot info
    bot_info = await callback.bot.get_me()
    bot_username = bot_info.username

    # Generate referral link
    from database.crud import UserCRUD
    referral_link = UserCRUD.generate_referral_link(bot_username, user_id)

    # Get user's generated photo
    async with async_session_maker() as session:
        photo = await UserPhotoCRUD.get_photo(session, user_id)
        if not photo or not photo.generated_path:
            await callback.answer("Открытка не найдена. Пройдите квиз заново.", show_alert=True)
            return

    # Instruction message
    instruction_text = (
        f"✈️ <b>Как опубликовать в Telegram Stories:</b>\n\n"
        f"1️⃣ Сохраните открытку на устройство (нажмите на фото → Сохранить)\n"
        f"2️⃣ В Telegram перейдите в \"Настройки\" → \"Моя история\"\n"
        f"3️⃣ Нажмите ➕ (добавить историю)\n"
        f"4️⃣ Выберите сохранённую открытку\n"
        f"5️⃣ Добавьте текст с реферальной ссылкой:\n"
        f"<code>{referral_link}</code>\n\n"
        f"6️⃣ Опубликуйте! 🎉\n\n"
        f"<i>Ваши друзья смогут перейти по ссылке и пройти квиз</i>"
    )

    await callback.answer()
    await callback.message.answer(text=instruction_text)
