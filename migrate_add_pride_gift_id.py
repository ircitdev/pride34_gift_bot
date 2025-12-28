"""Migration script to add pride_gift_id field to users table."""
import asyncio
import random
from sqlalchemy import text
from database.engine import async_session_maker, engine
from database.models import Base, User


async def migrate():
    """Add pride_gift_id column and generate unique IDs for existing users."""
    print("Starting migration: adding pride_gift_id to users table...")

    async with engine.begin() as conn:
        # Add the new column (nullable initially)
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN pride_gift_id INTEGER"
            ))
            print("✅ Added pride_gift_id column")
        except Exception as e:
            print(f"⚠️  Column might already exist: {e}")

    # Generate unique Pride GIFT IDs for existing users
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT id FROM users WHERE pride_gift_id IS NULL"))
        user_ids = [row[0] for row in result.fetchall()]

        if not user_ids:
            print("✅ No users need Pride GIFT ID assignment")
            return

        print(f"Found {len(user_ids)} users without Pride GIFT ID")

        used_ids = set()
        for user_id in user_ids:
            # Generate unique 5-digit ID
            while True:
                pride_id = random.randint(10000, 99999)
                if pride_id not in used_ids:
                    used_ids.add(pride_id)
                    break

            # Update user
            await session.execute(
                text("UPDATE users SET pride_gift_id = :pride_id WHERE id = :user_id"),
                {"pride_id": pride_id, "user_id": user_id}
            )
            print(f"  User {user_id} -> Pride GIFT ID: {pride_id}")

        await session.commit()
        print(f"✅ Assigned Pride GIFT IDs to {len(user_ids)} users")

    # Make the column unique (now that all users have IDs)
    async with engine.begin() as conn:
        try:
            await conn.execute(text(
                "CREATE UNIQUE INDEX idx_pride_gift_id ON users(pride_gift_id)"
            ))
            print("✅ Created unique index on pride_gift_id")
        except Exception as e:
            print(f"⚠️  Index might already exist: {e}")

    print("✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
