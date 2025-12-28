"""Broadcast messages to users - admin only."""
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session_maker
from database.crud import UserCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


class BroadcastStates(StatesGroup):
    """States for broadcast."""
    waiting_for_message = State()
    confirming = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    admin_ids = [int(x.strip()) for x in settings.ADMIN_IDS.split(',') if x.strip()]
    return user_id in admin_ids


@router.message(Command("broadcast"))
@router.message(Command("mailing"))
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
        "• Видео с подписью\n"
        "• Документы\n\n"
        "Для отмены используйте /cancel"
    )
    await state.set_state(BroadcastStates.waiting_for_message)


@router.message(BroadcastStates.waiting_for_message, Command("cancel"))
@router.message(BroadcastStates.confirming, Command("cancel"))
async def cancel_broadcast(message: Message, state: FSMContext):
    """Cancel broadcast."""
    await state.clear()
    await message.answer("❌ Рассылка отменена")


@router.message(BroadcastStates.waiting_for_message)
async def handle_broadcast_message(message: Message, state: FSMContext):
    """Handle broadcast message and ask for confirmation."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        await state.clear()
        return

    # Get all users count
    async with async_session_maker() as session:
        users = await UserCRUD.get_all_users(session)

    total_users = len(users)

    if total_users == 0:
        await message.answer("❌ Нет пользователей для рассылки")
        await state.clear()
        return

    # Save message data to state
    await state.update_data(message_to_broadcast=message)

    # Create confirmation keyboard
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Начать рассылку", callback_data="broadcast_confirm")
    builder.button(text="❌ Отмена", callback_data="broadcast_cancel")
    builder.adjust(1)

    confirm_text = (
        f"📊 <b>Подтверждение рассылки</b>\n\n"
        f"👥 Получателей: {total_users}\n\n"
        f"Подтвердите начало рассылки:"
    )

    await message.answer(confirm_text, reply_markup=builder.as_markup())
    await state.set_state(BroadcastStates.confirming)


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast via callback."""
    await callback.answer()
    await callback.message.edit_text("❌ Рассылка отменена")
    await state.clear()


@router.callback_query(F.data == "broadcast_confirm")
async def confirm_and_send_broadcast(callback: CallbackQuery, state: FSMContext):
    """Confirm and send broadcast to all users."""
    await callback.answer()

    if not is_admin(callback.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    source_msg = data.get("message_to_broadcast")

    if not source_msg:
        await callback.message.edit_text("❌ Сообщение для рассылки не найдено")
        await state.clear()
        return

    # Get all users
    async with async_session_maker() as session:
        users = await UserCRUD.get_all_users(session)

    total = len(users)

    # Update message
    await callback.message.edit_text(
        f"🚀 Начинаю рассылку...\n\n"
        f"Отправлено: 0/{total}"
    )

    # Send messages
    success_count = 0
    failed_count = 0
    failed_users = []

    for i, user in enumerate(users, 1):
        try:
            # Copy message to user
            await source_msg.copy_to(user.id)
            success_count += 1

            # Update status every 5 users
            if i % 5 == 0 or i == total:
                try:
                    await callback.message.edit_text(
                        f"🚀 Рассылка в процессе...\n\n"
                        f"Отправлено: {success_count}/{total}\n"
                        f"Ошибок: {failed_count}"
                    )
                except:
                    pass  # Ignore edit errors

            # Sleep to avoid rate limits (30 messages per second max)
            await asyncio.sleep(0.04)

        except Exception as e:
            logger.error(f"Failed to send message to user {user.id}: {e}")
            failed_count += 1
            failed_users.append(user.id)

    # Final report
    final_text = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Всего пользователей: {total}\n"
        f"• Успешно отправлено: {success_count}\n"
        f"• Ошибок: {failed_count}\n"
        f"• Процент доставки: {(success_count/total*100 if total > 0 else 0):.1f}%"
    )

    if failed_count > 0 and failed_count <= 10:
        final_text += f"\n\n❌ Не доставлено: {', '.join(map(str, failed_users))}"

    await callback.message.edit_text(final_text)
    await state.clear()

    logger.info(
        f"Broadcast completed by admin {callback.from_user.id}: "
        f"{success_count} sent, {failed_count} failed"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show user statistics - admin only."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    async with async_session_maker() as session:
        all_users = await UserCRUD.get_all_users(session)
        participants = await UserCRUD.get_all_participants(session)
        winners = await UserCRUD.get_winners(session)

    total = len(all_users)
    quiz_completed = len(participants)
    photos_uploaded = sum(1 for u in all_users if u.photo_uploaded)
    winner_count = len(winners)

    stats_text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: {total}\n"
        f"✅ Завершили квиз: {quiz_completed}\n"
        f"📸 Загрузили фото: {photos_uploaded}\n"
        f"🏆 Победителей: {winner_count}\n"
        f"🎯 Конверсия: {(quiz_completed/total*100 if total > 0 else 0):.1f}%"
    )

    await message.answer(stats_text)
