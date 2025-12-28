"""Migration script to add forum_topic_id field to users table."""
import asyncio
from sqlalchemy import text
from database.engine import engine


async def migrate():
    """Add forum_topic_id column to users table."""
    print("Starting migration: adding forum_topic_id to users table...")

    async with engine.begin() as conn:
        # Add the new column (nullable)
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN forum_topic_id INTEGER"
            ))
            print("✅ Added forum_topic_id column")
        except Exception as e:
            print(f"⚠️  Column might already exist: {e}")

    print("✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
