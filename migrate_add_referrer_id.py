"""Migration: Add referrer_id to users table for referral system."""
import asyncio
import logging
from sqlalchemy import text
from database.engine import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add referrer_id column to users table."""
    async with engine.begin() as conn:
        try:
            # Check if column exists using SQLite PRAGMA
            result = await conn.execute(text("PRAGMA table_info(users);"))
            columns = result.fetchall()
            column_names = [col[1] for col in columns]  # col[1] is the column name

            if 'referrer_id' in column_names:
                logger.info("Column 'referrer_id' already exists in 'users' table")
                return

            # Add referrer_id column
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN referrer_id BIGINT NULL;"
            ))
            logger.info("✅ Added column 'referrer_id' to 'users' table")

            # Add index for better performance
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_users_referrer_id ON users(referrer_id);"
            ))
            logger.info("✅ Added index on 'referrer_id'")

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
    logger.info("🎉 Migration completed successfully!")
