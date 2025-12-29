"""Handle user replies and forward to forum."""
import logging
from aiogram import Router, F
from aiogram.types import Message

from database.engine import async_session_maker
from database.crud import UserCRUD, UserMessageCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.chat.type == "private", F.from_user.id)
async def handle_user_reply(message: Message):
    """
    Handle user message in private chat - forward to their forum topic.
    Only for users who have completed quiz and have a topic.
    """
    user_id = message.from_user.id

    # Skip admin messages
    if user_id in settings.admin_ids_list:
        return

    # Get user data
    async with async_session_maker() as session:
        user = await UserCRUD.get(session, user_id)

    if not user or not user.forum_topic_id:
        # User doesn't have a forum topic yet
        return

    # Forward to forum topic
    try:
        sent_message = await message.bot.copy_message(
            chat_id=settings.FORUM_GROUP_ID,
            message_thread_id=user.forum_topic_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Log the message
        async with async_session_maker() as session:
            await UserMessageCRUD.log_message(
                session,
                user_id=user_id,
                forum_message_id=sent_message.message_id,
                user_message_id=message.message_id,
                direction='from_user'
            )

        logger.info(f"Forwarded user {user_id} message to topic {user.forum_topic_id}")

    except Exception as e:
        logger.error(f"Failed to forward user {user_id} message to forum: {e}")
