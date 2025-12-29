"""Main entry point for the Pride34 Gift Bot."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.engine import init_db
from handlers import start, quiz, photo, admin, forum_communication, user_replies, text_editor, inline


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Initialize and start the bot."""
    # Create necessary directories
    settings.create_directories()

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers
    # ВАЖНО: Порядок имеет значение!
    # forum_communication и user_replies должны быть последними,
    # чтобы не перехватывать команды и callback'и других обработчиков
    dp.include_router(start.router)
    dp.include_router(quiz.router)
    dp.include_router(photo.router)
    dp.include_router(admin.router)  # Includes advanced broadcast with grouping
    dp.include_router(text_editor.router)          # Text editor
    dp.include_router(inline.router)               # Inline mode for sharing
    dp.include_router(forum_communication.router)  # Forum -> User messaging
    dp.include_router(user_replies.router)         # User -> Forum messaging

    logger.info("Bot started")

    try:
        # Start polling
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
