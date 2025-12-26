"""Broadcast messages to users - admin only."""
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import async_session_maker
from database.crud import UserCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


class BroadcastStates(StatesGroup):
    """States for broadcast."""
    waiting_for_message = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in settings.ADMIN_IDS


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Start broadcast process - admin only."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    await message.answer(
        "📢 <b>Режим рассылки</b>\n\n"
        "Отправьте сообщение, которое нужно разослать всем пользователям.\n\n"
        "Поддерживается:\n"
        "• Текст с форматированием (HTML)\n"
        "• Фото с подписью\n"
        "• Видео с подписью\n\n"
        "Для отмены используйте /cancel"
    )
    await state.set_state(BroadcastStates.waiting_for_message)


@router.message(BroadcastStates.waiting_for_message, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    """Cancel broadcast."""
    await state.clear()
    await message.answer("❌ Рассылка отменена")


@router.message(BroadcastStates.waiting_for_message)
async def handle_broadcast_message(message: Message, state: FSMContext):
    """Handle broadcast message and send to all users."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        await state.clear()
        return

    # Get all users
    async with async_session_maker() as session:
        users = await UserCRUD.get_all_users(session)

    total_users = len(users)

    if total_users == 0:
        await message.answer("❌ Нет пользователей для рассылки")
        await state.clear()
        return

    # Confirm broadcast
    confirm_text = (
        f"📊 <b>Подтверждение рассылки</b>\n\n"
        f"Получателей: {total_users}\n\n"
        f"Начать рассылку? Отправьте <b>ДА</b> для подтверждения\n"
        f"Или /cancel для отмены"
    )

    await message.answer(confirm_text)

    # Store message data
    await state.update_data(
        message_id=message.message_id,
        users=users,
        total=total_users
    )


@router.message(BroadcastStates.waiting_for_message, F.text == "ДА")
async def confirm_and_send_broadcast(message: Message, state: FSMContext):
    """Confirm and send broadcast to all users."""
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    users = data.get("users", [])
    total = data.get("total", 0)
    source_msg_id = data.get("message_id")

    if not users:
        await message.answer("❌ Нет данных для рассылки")
        await state.clear()
        return

    # Start broadcasting
    status_msg = await message.answer(
        f"🚀 Начинаю рассылку...\n\n"
        f"Отправлено: 0/{total}"
    )

    # Get source message
    source_msg = None
    async for msg in message.bot.iter_history(message.chat.id, limit=10):
        if msg.message_id == source_msg_id:
            source_msg = msg
            break

    if not source_msg:
        await message.answer("❌ Исходное сообщение не найдено")
        await state.clear()
        return

    # Send messages
    success_count = 0
    failed_count = 0

    for i, user in enumerate(users, 1):
        try:
            # Copy message to user
            await source_msg.copy_to(user.telegram_id)
            success_count += 1

            # Update status every 10 users
            if i % 10 == 0:
                await status_msg.edit_text(
                    f"🚀 Рассылка в процессе...\n\n"
                    f"Отправлено: {success_count}/{total}\n"
                    f"Ошибок: {failed_count}"
                )

            # Sleep to avoid rate limits
            await asyncio.sleep(0.05)

        except Exception as e:
            logger.error(f"Failed to send message to user {user.telegram_id}: {e}")
            failed_count += 1

    # Final report
    final_text = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Всего пользователей: {total}\n"
        f"• Успешно отправлено: {success_count}\n"
        f"• Ошибок: {failed_count}\n"
        f"• Процент доставки: {(success_count/total*100):.1f}%"
    )

    await status_msg.edit_text(final_text)
    await state.clear()

    logger.info(
        f"Broadcast completed by admin {message.from_user.id}: "
        f"{success_count} sent, {failed_count} failed"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show user statistics - admin only."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    async with async_session_maker() as session:
        users = await UserCRUD.get_all_users(session)
        quiz_completed = sum(1 for u in users if u.quiz_completed)
        photos_uploaded = sum(1 for u in users if u.photo_uploaded)

    stats_text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {len(users)}\n"
        f"✅ Завершили квиз: {quiz_completed}\n"
        f"📸 Загрузили фото: {photos_uploaded}\n"
        f"🎯 Конверсия: {(quiz_completed/len(users)*100 if users else 0):.1f}%"
    )

    await message.answer(stats_text)
