"""Forum communication handlers for two-way messaging."""
import logging
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.engine import async_session_maker
from database.crud import UserCRUD, UserMessageCRUD
from database.models import User
from config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.chat.id == settings.FORUM_GROUP_ID, F.message_thread_id)
async def handle_admin_message_in_topic(message: Message):
    """
    Handle admin message in user topic - forward to user.
    Only processes messages in topics (not in general chat).
    """
    topic_id = message.message_thread_id

    if not topic_id:
        return  # Not in a topic

    # Find user by forum_topic_id
    async with async_session_maker() as session:
        # Get user with this topic ID
        result = await session.execute(
            select(User).where(User.forum_topic_id == topic_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"No user found for topic {topic_id}")
        return

    # Don't forward bot's own messages
    if message.from_user.id == message.bot.id:
        return

    # Forward message to user
    try:
        sent_message = await message.bot.copy_message(
            chat_id=user.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Log the message
        async with async_session_maker() as session:
            await UserMessageCRUD.log_message(
                session,
                user_id=user.id,
                forum_message_id=message.message_id,
                user_message_id=sent_message.message_id,
                direction='to_user'
            )

        logger.info(f"Forwarded message from topic {topic_id} to user {user.id}")

    except Exception as e:
        logger.error(f"Failed to forward message to user {user.id}: {e}")
