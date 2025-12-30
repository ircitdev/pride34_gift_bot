"""Check if bot handlers are properly registered."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Dispatcher
from handlers import photo, start, quiz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_handlers():
    """Check handlers registration."""
    dp = Dispatcher()

    # Register routers in the same order as main.py
    dp.include_router(start.router)
    dp.include_router(quiz.router)
    dp.include_router(photo.router)

    logger.info("=" * 60)
    logger.info("CHECKING REGISTERED HANDLERS")
    logger.info("=" * 60)

    # Check photo router handlers
    logger.info("\n📸 PHOTO ROUTER HANDLERS:")
    for handler in photo.router.message.handlers:
        logger.info(f"  - {handler.callback.__name__}")
        if hasattr(handler, 'filters'):
            logger.info(f"    Filters: {handler.filters}")

    for handler in photo.router.callback_query.handlers:
        logger.info(f"  - {handler.callback.__name__} (callback)")

    logger.info("\n🎯 QUIZ ROUTER HANDLERS:")
    for handler in quiz.router.callback_query.handlers:
        logger.info(f"  - {handler.callback.__name__} (callback)")

    logger.info("\n🏁 START ROUTER HANDLERS:")
    for handler in start.router.message.handlers:
        logger.info(f"  - {handler.callback.__name__}")

    logger.info("\n" + "=" * 60)
    logger.info("HANDLER CHECK COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    check_handlers()
