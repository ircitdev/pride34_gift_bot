"""Forum service for posting user data to forum topics."""
import logging
from pathlib import Path
from aiogram import Bot
from aiogram.types import FSInputFile
from config import settings

logger = logging.getLogger(__name__)


class ForumService:
    """Service for posting user data to forum topics."""

    @staticmethod
    async def create_user_topic(
        bot: Bot,
        user_id: int,
        username: str,
        full_name: str,
        gender: str,
        quiz_answers: list,
        user_photo_path: Path,
        generated_photo_path: Path
    ) -> int:
        """
        Create a topic for user and post their data.

        Args:
            bot: Bot instance
            user_id: Telegram user ID
            username: Telegram username
            full_name: User's full name
            gender: User's gender
            quiz_answers: List of quiz answers
            user_photo_path: Path to uploaded user photo
            generated_photo_path: Path to generated Christmas image

        Returns:
            Topic ID (message_thread_id)
        """
        if not settings.FORUM_GROUP_ID:
            logger.warning("FORUM_GROUP_ID not set, skipping topic creation")
            return 0

        try:
            # Create topic with user's Telegram ID as name
            topic_name = f"User {user_id}"
            topic_message = await bot.create_forum_topic(
                chat_id=settings.FORUM_GROUP_ID,
                name=topic_name
            )

            topic_id = topic_message.message_thread_id
            logger.info(f"Created topic {topic_id} for user {user_id}")

            # Prepare user data message
            gender_emoji = "👨" if gender == "male" else "👩"
            username_text = f"@{username}" if username else "—"

            user_data_text = (
                f"{gender_emoji} <b>Данные пользователя</b>\n\n"
                f"<b>Telegram ID:</b> <code>{user_id}</code>\n"
                f"<b>Username:</b> {username_text}\n"
                f"<b>Имя:</b> {full_name}\n"
                f"<b>Пол:</b> {'Мужской' if gender == 'male' else 'Женский'}\n\n"
                f"<b>Ответы на квиз:</b>\n"
            )

            # Add quiz answers
            for i, answer in enumerate(quiz_answers, 1):
                user_data_text += f"{i}. {answer}\n"

            # Send user data
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
