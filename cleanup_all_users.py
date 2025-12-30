"""Script to delete all users and their files from the database and filesystem."""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent))

from database.engine import async_session_maker, engine
from config import settings


async def cleanup_all_users():
    """Delete all users and their associated files."""

    print("=" * 60)
    print("FULL CLEANUP OF ALL USERS")
    print("=" * 60)

    # Confirm action
    print("\nWARNING! This action will:")
    print("  - Delete ALL records from users, quiz_answers, user_photos, user_messages")
    print("  - Delete ALL files from user_photos/ and generated_photos/")
    print("  - This action is IRREVERSIBLE!")
    print()

    confirmation = input("Type 'DELETE ALL' to confirm: ")

    if confirmation != "DELETE ALL":
        print("\nCancelled. No data was deleted.")
        return

    print("\nStarting cleanup...\n")

    # Step 1: Count users
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        users_count = result.scalar()

        result = await session.execute(text("SELECT COUNT(*) FROM quiz_answers"))
        quiz_answers_count = result.scalar()

        result = await session.execute(text("SELECT COUNT(*) FROM user_photos"))
        user_photos_count = result.scalar()

        result = await session.execute(text("SELECT COUNT(*) FROM user_messages"))
        user_messages_count = result.scalar()

    print(f"Found records:")
    print(f"  - Users: {users_count}")
    print(f"  - Quiz answers: {quiz_answers_count}")
    print(f"  - User photos: {user_photos_count}")
    print(f"  - User messages: {user_messages_count}")
    print()

    # Step 2: Delete database records
    print("Deleting database records...")

    async with engine.begin() as conn:
        # Delete in correct order (foreign keys)
        await conn.execute(text("DELETE FROM user_messages"))
        print("  OK - Deleted all user_messages")

        await conn.execute(text("DELETE FROM quiz_answers"))
        print("  OK - Deleted all quiz_answers")

        await conn.execute(text("DELETE FROM user_photos"))
        print("  OK - Deleted all user_photos")

        await conn.execute(text("DELETE FROM users"))
        print("  OK - Deleted all users")

        # Reset autoincrement counters (if table exists)
        try:
            await conn.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('users', 'quiz_answers', 'user_photos', 'user_messages')"))
            print("  OK - Reset autoincrement counters")
        except Exception as e:
            print(f"  INFO - sqlite_sequence not found (OK for new DB)")

    print()

    # Step 3: Delete photo files
    print("Deleting photo files...")

    user_photos_dir = settings.USER_PHOTOS_DIR
    generated_photos_dir = settings.GENERATED_PHOTOS_DIR

    # Delete user photos
    user_photos_deleted = 0
    if user_photos_dir.exists():
        for file_path in user_photos_dir.glob("*.jpg"):
            try:
                file_path.unlink()
                user_photos_deleted += 1
            except Exception as e:
                print(f"  WARNING - Error deleting {file_path.name}: {e}")

    print(f"  OK - Deleted user photos: {user_photos_deleted}")

    # Delete generated photos
    generated_photos_deleted = 0
    if generated_photos_dir.exists():
        for file_path in generated_photos_dir.glob("*_christmas.jpg"):
            try:
                file_path.unlink()
                generated_photos_deleted += 1
            except Exception as e:
                print(f"  WARNING - Error deleting {file_path.name}: {e}")

    print(f"  OK - Deleted generated cards: {generated_photos_deleted}")

    print()
    print("=" * 60)
    print("CLEANUP COMPLETED")
    print("=" * 60)
    print()
    print("Total deleted:")
    print(f"  - Users: {users_count}")
    print(f"  - Quiz answers: {quiz_answers_count}")
    print(f"  - Photo records: {user_photos_count}")
    print(f"  - Messages: {user_messages_count}")
    print(f"  - Photo files: {user_photos_deleted}")
    print(f"  - Card files: {generated_photos_deleted}")
    print()
    print("Database and files cleaned. Ready for new testing.")
    print()


async def main():
    """Main entry point."""
    try:
        await cleanup_all_users()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
