"""Script to remove all users except admins from database."""
import asyncio
from sqlalchemy import text
from database.engine import async_session_maker
from config import settings


async def cleanup_users():
    """Remove all users except admins."""
    # Parse ADMIN_IDS string to list of integers
    admin_ids = [int(x.strip()) for x in settings.ADMIN_IDS.split(',') if x.strip()]
    print(f"Admin IDs to keep: {admin_ids}")

    async with async_session_maker() as session:
        # Get all users
        result = await session.execute(text("SELECT id, username, full_name FROM users"))
        all_users = result.fetchall()

        print(f"\nFound {len(all_users)} total users:")
        for user in all_users:
            status = "ADMIN - KEEP" if user[0] in admin_ids else "DELETE"
            print(f"  User {user[0]} (@{user[1]}, {user[2]}) - {status}")

        # Delete non-admin users from all tables
        users_to_delete = [user[0] for user in all_users if user[0] not in admin_ids]

        if not users_to_delete:
            print("\n✅ No users to delete")
            return

        print(f"\n🗑️  Deleting {len(users_to_delete)} users...")

        # Delete related data first (foreign keys)
        for user_id in users_to_delete:
            # Delete quiz answers
            await session.execute(
                text("DELETE FROM quiz_answers WHERE user_id = :user_id"),
                {"user_id": user_id}
            )

            # Delete user photos
            await session.execute(
                text("DELETE FROM user_photos WHERE user_id = :user_id"),
                {"user_id": user_id}
            )

            # Delete user
            await session.execute(
                text("DELETE FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )

            print(f"  ✅ Deleted user {user_id}")

        await session.commit()

        print(f"\n✅ Successfully deleted {len(users_to_delete)} users")
        print(f"✅ Kept {len(admin_ids)} admin users")


if __name__ == "__main__":
    asyncio.run(cleanup_users())
