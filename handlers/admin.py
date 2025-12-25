"""Admin panel handlers."""
import logging
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import csv
from io import StringIO

from bot.keyboards import get_admin_keyboard
from database.engine import async_session_maker
from database.crud import UserCRUD, QuizAnswerCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in settings.admin_ids_list


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command."""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к админ-панели.")
        return

    text = (
        "<b>Админ-панель Pride34 Gift Bot</b>\n\n"
        "Выберите действие:"
    )

    await message.answer(
        text=text,
        reply_markup=get_admin_keyboard()
    )


@router.message(F.text == "Статистика")
async def show_statistics(message: Message):
    """Show bot statistics."""
    if not is_admin(message.from_user.id):
        return

    async with async_session_maker() as session:
        all_users = await UserCRUD.get_all_participants(session)
        winners = await UserCRUD.get_winners(session)

    # Calculate stats
    total_users = len(all_users)
    users_with_photo = sum(1 for u in all_users if u.photo_uploaded)
    total_winners = len(winners)

    text = (
        f"<b>Статистика бота:</b>\n\n"
        f"Всего участников: {total_users}\n"
        f"Прошли квиз: {total_users}\n"
        f"Загрузили фото: {users_with_photo}\n"
        f"Победителей: {total_winners}\n\n"
        f"Дата окончания розыгрыша: {settings.QUIZ_END_DATE}\n"
        f"Количество призов: {settings.WINNERS_COUNT}"
    )

    await message.answer(text=text)


@router.message(F.text == "Розыгрыш")
async def conduct_raffle(message: Message):
    """Conduct the raffle and select winners."""
    if not is_admin(message.from_user.id):
        return

    async with async_session_maker() as session:
        # Get all participants who completed quiz
        participants = await UserCRUD.get_all_participants(session)

        if len(participants) == 0:
            await message.answer("Нет участников для розыгрыша.")
            return

        # Check if raffle already conducted
        existing_winners = await UserCRUD.get_winners(session)
        if len(existing_winners) > 0:
            await message.answer(
                f"Розыгрыш уже проведён. Победителей: {len(existing_winners)}\n"
                "Используйте кнопку 'Победители' для просмотра."
            )
            return

        # Select random winners
        winners_count = min(settings.WINNERS_COUNT, len(participants))
        winners = random.sample(participants, winners_count)

        # Mark winners in database
        for winner in winners:
            await UserCRUD.set_winner(session, winner.id, True)

        logger.info(f"Raffle conducted: {winners_count} winners selected")

    # Prepare response
    text = (
        f"<b>Розыгрыш проведён!</b>\n\n"
        f"Выбрано победителей: {winners_count}\n\n"
        f"Список победителей доступен через кнопку 'Победители'."
    )

    await message.answer(text=text)

    # Notify winners
    for winner in winners:
        try:
            await message.bot.send_message(
                chat_id=winner.id,
                text=(
                    "<b>Поздравляем!</b> 🎉\n\n"
                    "Вы стали победителем в розыгрыше сертификатов от СК ПРАЙД!\n\n"
                    "С вами свяжется администратор для получения приза."
                )
            )
        except Exception as e:
            logger.error(f"Failed to notify winner {winner.id}: {e}")


@router.message(F.text == "Победители")
async def show_winners(message: Message):
    """Show list of winners."""
    if not is_admin(message.from_user.id):
        return

    async with async_session_maker() as session:
        winners = await UserCRUD.get_winners(session)

    if len(winners) == 0:
        await message.answer("Розыгрыш ещё не проведён.")
        return

    # Format winners list
    text = f"<b>Победители ({len(winners)}):</b>\n\n"

    for idx, winner in enumerate(winners, 1):
        username = f"@{winner.username}" if winner.username else "без username"
        text += f"{idx}. {winner.full_name or 'N/A'} ({username}) - ID: {winner.id}\n"

    await message.answer(text=text)


@router.message(F.text == "Экспорт данных")
async def export_data(message: Message):
    """Export user data to CSV."""
    if not is_admin(message.from_user.id):
        return

    async with async_session_maker() as session:
        users = await UserCRUD.get_all_participants(session)

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID', 'Username', 'Full Name', 'Gender', 'Quiz Completed',
            'Photo Uploaded', 'Is Winner', 'Created At'
        ])

        # Write data
        for user in users:
            # Get user's answers
            answers = await QuizAnswerCRUD.get_user_answers(session, user.id)
            answers_text = "; ".join([f"Q{a.question_number}: {a.answer}" for a in answers])

            writer.writerow([
                user.id,
                user.username or '',
                user.full_name or '',
                user.gender or '',
                'Да' if user.quiz_completed else 'Нет',
                'Да' if user.photo_uploaded else 'Нет',
                'Да' if user.is_winner else 'Нет',
                user.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])

    # Send CSV file
    csv_content = output.getvalue().encode('utf-8-sig')  # UTF-8 with BOM for Excel
    filename = f"pride34_bot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    from aiogram.types import BufferedInputFile
    file = BufferedInputFile(csv_content, filename=filename)

    await message.answer_document(
        document=file,
        caption=f"Экспорт данных: {len(users)} участников"
    )

    logger.info(f"Admin {message.from_user.id} exported data: {len(users)} users")
