"""CRUD operations for database."""
from typing import List, Optional
import random
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, QuizAnswer, UserPhoto, QuizQuestion


class UserCRUD:
    """CRUD operations for User model."""

    @staticmethod
    async def _generate_unique_pride_id(session: AsyncSession) -> int:
        """Generate unique 5-digit Pride GIFT ID."""
        max_attempts = 100
        for _ in range(max_attempts):
            pride_id = random.randint(10000, 99999)
            # Check if this ID already exists
            result = await session.execute(
                select(User).where(User.pride_gift_id == pride_id)
            )
            if not result.scalar_one_or_none():
                return pride_id
        raise ValueError("Could not generate unique Pride GIFT ID")

    @staticmethod
    async def get_or_create(session: AsyncSession, user_id: int, username: str = None, full_name: str = None) -> User:
        """Get existing user or create new one."""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            pride_gift_id = await UserCRUD._generate_unique_pride_id(session)
            user = User(
                id=user_id,
                pride_gift_id=pride_gift_id,
                username=username,
                full_name=full_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user

    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_quiz_status(session: AsyncSession, user_id: int, completed: bool = True):
        """Update quiz completion status."""
        await session.execute(
            update(User).where(User.id == user_id).values(quiz_completed=completed)
        )
        await session.commit()

    @staticmethod
    async def update_photo_status(session: AsyncSession, user_id: int, uploaded: bool = True):
        """Update photo upload status."""
        await session.execute(
            update(User).where(User.id == user_id).values(photo_uploaded=uploaded)
        )
        await session.commit()

    @staticmethod
    async def set_gender(session: AsyncSession, user_id: int, gender: str):
        """Set user gender."""
        await session.execute(
            update(User).where(User.id == user_id).values(gender=gender)
        )
        await session.commit()

    @staticmethod
    async def set_winner(session: AsyncSession, user_id: int, is_winner: bool = True):
        """Mark user as winner."""
        await session.execute(
            update(User).where(User.id == user_id).values(is_winner=is_winner)
        )
        await session.commit()

    @staticmethod
    async def get_all_users(session: AsyncSession) -> List[User]:
        """Get all users."""
        result = await session.execute(select(User))
        return list(result.scalars().all())

    @staticmethod
    async def get_all_participants(session: AsyncSession) -> List[User]:
        """Get all users who completed quiz."""
        result = await session.execute(
            select(User).where(User.quiz_completed == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_winners(session: AsyncSession) -> List[User]:
        """Get all winners."""
        result = await session.execute(
            select(User).where(User.is_winner == True)
        )
        return list(result.scalars().all())



class QuizAnswerCRUD:
    """CRUD operations for QuizAnswer model."""

    @staticmethod
    async def add_answer(session: AsyncSession, user_id: int, question_number: int, answer: str):
        """Add quiz answer."""
        quiz_answer = QuizAnswer(
            user_id=user_id,
            question_number=question_number,
            answer=answer
        )
        session.add(quiz_answer)
        await session.commit()

    @staticmethod
    async def get_user_answers(session: AsyncSession, user_id: int) -> List[QuizAnswer]:
        """Get all answers for a user."""
        result = await session.execute(
            select(QuizAnswer).where(QuizAnswer.user_id == user_id).order_by(QuizAnswer.question_number)
        )
        return list(result.scalars().all())


class UserPhotoCRUD:
    """CRUD operations for UserPhoto model."""

    @staticmethod
    async def add_photo(session: AsyncSession, user_id: int, file_id: str, file_path: str):
        """Add user photo."""
        photo = UserPhoto(
            user_id=user_id,
            file_id=file_id,
            file_path=file_path
        )
        session.add(photo)
        await session.commit()
        await session.refresh(photo)
        return photo

    @staticmethod
    async def get_photo(session: AsyncSession, user_id: int) -> Optional[UserPhoto]:
        """Get user photo."""
        result = await session.execute(
            select(UserPhoto).where(UserPhoto.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_generated_path(session: AsyncSession, user_id: int, generated_path: str):
        """Update generated photo path."""
        await session.execute(
            update(UserPhoto).where(UserPhoto.user_id == user_id).values(generated_path=generated_path)
        )
        await session.commit()


class QuizQuestionCRUD:
    """CRUD operations for QuizQuestion model."""

    @staticmethod
    async def get_question(session: AsyncSession, question_number: int) -> Optional[QuizQuestion]:
        """Get question by number."""
        result = await session.execute(
            select(QuizQuestion).where(QuizQuestion.question_number == question_number)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_questions(session: AsyncSession) -> List[QuizQuestion]:
        """Get all questions."""
        result = await session.execute(
            select(QuizQuestion).order_by(QuizQuestion.question_number)
        )
        return list(result.scalars().all())
