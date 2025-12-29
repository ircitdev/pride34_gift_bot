"""Migration: Add user_messages table for forum communication."""
import asyncio
from sqlalchemy import text
from database.engine import engine


async def migrate():
    """Create user_messages table."""
    print("Starting migration: creating user_messages table...")

    async with engine.begin() as conn:
        try:
            # Create user_messages table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    forum_message_id INTEGER NOT NULL,
                    user_message_id INTEGER,
                    direction VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("[OK] Created user_messages table")

            # Create index for faster user lookups
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_messages_user_id
                ON user_messages(user_id)
            """))
            print("[OK] Created index on user_id")

        except Exception as e:
            print(f"[ERROR] Error during migration: {e}")
            raise

    print("[OK] Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
