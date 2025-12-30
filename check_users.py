#!/usr/bin/env python3
"""Check users with completed quiz."""
import asyncio
from database.engine import async_session_maker
from database.crud import UserCRUD


async def main():
    """Check completed users."""
    async with async_session_maker() as session:
        users = await UserCRUD.get_users_by_filter(session, 'completed')
        print(f"Completed users: {len(users)}")

        for user in users[:10]:  # Show first 10
            print(f"  - {user.id}: {user.full_name or user.username} (quiz_completed={user.quiz_completed})")


if __name__ == "__main__":
    asyncio.run(main())
