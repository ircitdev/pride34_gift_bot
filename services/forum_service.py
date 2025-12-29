"""Forum service for posting user data to forum topics."""
import logging
from pathlib import Path
from aiogram import Bot
from aiogram.types import FSInputFile
from config import settings
from bot.quiz_data import QUIZ_QUESTIONS

logger = logging.getLogger(__name__)


class ForumService:
    """Service for posting user data to forum topics."""

    @staticmethod
    async def create_user_topic(
        bot: Bot,
        user_id: int,
        pride_gift_id: int,
        username: str,
        full_name: str,
        gender: str,
        quiz_answers: list,
        user_photo_path: Path,
        generated_photo_path: Path,
        referrer_id: int = None,
        referrer_topic_id: int = None,
        referrer_pride_gift_id: int = None
    ) -> int:
        """
        Create a topic for user and post their data.

        Args:
            bot: Bot instance
            user_id: Telegram user ID
            pride_gift_id: Unique Pride GIFT ID
            username: Telegram username
            full_name: User's full name
            gender: User's gender
            quiz_answers: List of quiz answers (answer texts from database)
            user_photo_path: Path to uploaded user photo
            generated_photo_path: Path to generated Christmas image
            referrer_id: ID of user who referred this user (optional)
            referrer_topic_id: Forum topic ID of referrer (optional)
            referrer_pride_gift_id: Pride GIFT ID of referrer (optional)

        Returns:
            Topic ID (message_thread_id)
        """
        if not settings.FORUM_GROUP_ID:
            logger.warning("FORUM_GROUP_ID not set, skipping topic creation")
            return 0

        try:
            # Create topic with user's name (full_name or username)
            if full_name and full_name.strip():
                topic_name = full_name[:100]  # Telegram limit is 128 chars
            elif username:
                topic_name = f"@{username}"
            else:
                topic_name = f"User {user_id}"

            topic_message = await bot.create_forum_topic(
                chat_id=settings.FORUM_GROUP_ID,
                name=topic_name
            )

            topic_id = topic_message.message_thread_id
            logger.info(f"Created topic {topic_id} for user {user_id}")

            # Get user profile photos
            user_profile_photos = await bot.get_user_profile_photos(user_id, limit=1)

            # Prepare user data message
            gender_emoji = "👨" if gender == "male" else "👩"
            username_text = f"@{username}" if username else "—"

            user_data_text = (
                f"{gender_emoji} <b>Данные пользователя</b>\n\n"
                f"<b>Pride GIFT ID:</b> <code>{pride_gift_id}</code>\n"
                f"<b>Telegram ID:</b> <code>{user_id}</code>\n"
                f"<b>Username:</b> {username_text}\n"
                f"<b>Имя:</b> {full_name or '—'}\n"
                f"<b>Пол:</b> {'Мужской' if gender == 'male' else 'Женский'}\n"
            )

            # Add referral information if user came via referral link
            if referrer_id and referrer_topic_id and referrer_pride_gift_id:
                # Create link to referrer's topic
                topic_link = f"https://t.me/c/{str(settings.FORUM_GROUP_ID)[4:]}/{referrer_topic_id}"
                user_data_text += (
                    f"\n🎁 <b>Реферал от:</b> Pride GIFT ID <code>{referrer_pride_gift_id}</code>\n"
                    f"👉 <a href='{topic_link}'>Перейти к топику реферера</a>\n"
                )

            user_data_text += "\n<b>Ответы на квиз:</b>\n"

            # Add quiz answers with full question and answer text
            for i, answer_text in enumerate(quiz_answers, 1):
                question_text = QUIZ_QUESTIONS[i]["text"]
                user_data_text += f"\n<b>{question_text}</b>\n➜ {answer_text}\n"

            # Send user avatar if available, otherwise send text only
            if user_profile_photos.total_count > 0:
                # User has avatar, send it with caption
                avatar_file_id = user_profile_photos.photos[0][-1].file_id
                await bot.send_photo(
                    chat_id=settings.FORUM_GROUP_ID,
                    message_thread_id=topic_id,
                    photo=avatar_file_id,
                    caption=user_data_text
                )
            else:
                # No avatar, send text only
                await bot.send_message(
                    chat_id=settings.FORUM_GROUP_ID,
                    message_thread_id=topic_id,
                    text=user_data_text
                )

            # Send original user photo
            if user_photo_path.exists():
                photo = FSInputFile(user_photo_path)
                await bot.send_photo(
                    chat_id=settings.FORUM_GROUP_ID,
                    message_thread_id=topic_id,
                    photo=photo,
                    caption="📸 <b>Оригинальное фото пользователя</b>"
                )
            else:
                logger.warning(f"User photo not found: {user_photo_path}")

            # Send generated Christmas card
            if generated_photo_path.exists():
                generated_photo = FSInputFile(generated_photo_path)
                await bot.send_photo(
                    chat_id=settings.FORUM_GROUP_ID,
                    message_thread_id=topic_id,
                    photo=generated_photo,
                    caption="🎄 <b>Сгенерированная открытка</b>"
                )
            else:
                logger.warning(f"Generated photo not found: {generated_photo_path}")

            logger.info(f"Posted all data for user {user_id} to topic {topic_id}")
            return topic_id

        except Exception as e:
            logger.error(f"Error creating topic for user {user_id}: {e}")
            return 0
