"""Inline mode handlers for sharing functionality."""
import logging
from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from database.engine import async_session_maker
from database.crud import UserCRUD

router = Router()
logger = logging.getLogger(__name__)


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery):
    """
    Handle inline queries for sharing referral links.

    When user clicks "Рассказать друзьям" button, this handler
    processes the inline query and shows a single article result
    that can be sent to friends.
    """
    user_id = inline_query.from_user.id
    query_text = inline_query.query

    # Get bot info
    bot_info = await inline_query.bot.get_me()
    bot_username = bot_info.username

    # Generate referral link
    referral_link = UserCRUD.generate_referral_link(bot_username, user_id)

    # Create sharing message
    if query_text:
        # Use the pre-filled query text from the button
        message_text = query_text
    else:
        # Fallback if query is empty
        message_text = (
            f"🎄 Привет! Я прошёл новогодний квиз от PRIDE Fitness и получил своё фитнес-предсказание на 2026 год!\n\n"
            f"Попробуй и ты — узнай, что тебя ждёт в новом году, и получи классное праздничное фото! 🎁\n\n"
            f"👉 {referral_link}"
        )

    # Create inline query result
    result = InlineQueryResultArticle(
        id="share_quiz",
        title="🎄 Поделиться новогодним квизом",
        description="Отправить приглашение пройти квиз с вашей реферальной ссылкой",
        input_message_content=InputTextMessageContent(
            message_text=message_text
        ),
        thumbnail_url="https://i.imgur.com/placeholder.jpg"  # Опционально: добавить превью
    )

    # Answer inline query
    await inline_query.answer(
        results=[result],
        cache_time=1,  # Don't cache results (always fresh referral link)
        is_personal=True  # Results are personal to this user
    )

    logger.info(f"User {user_id} shared quiz via inline mode")
