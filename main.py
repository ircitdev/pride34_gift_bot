"""Main entry point for the Pride34 Gift Bot."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.engine import init_db
from handlers import start, quiz, photo, admin, broadcast


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
    dp.include_router(start.router)
    dp.include_router(quiz.router)
    dp.include_router(photo.router)
    dp.include_router(admin.router)
    dp.include_router(broadcast.router)

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
