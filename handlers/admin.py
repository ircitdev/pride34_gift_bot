"""Admin panel handlers."""
import logging
import random
import math
import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import csv
from io import StringIO

from bot.keyboards import (
    get_admin_keyboard,
    get_group_link_keyboard,
    get_broadcast_pagination_keyboard,
    get_broadcast_confirm_keyboard,
    get_winners_count_menu_keyboard,
    get_winners_count_confirm_keyboard,
    get_date_menu_keyboard,
    get_date_confirm_keyboard,
    get_broadcast_group_select_keyboard,
    get_broadcast_preview_keyboard
)
from bot.states import AdminStates
from database.engine import async_session_maker
from database.crud import UserCRUD, QuizAnswerCRUD
from config import settings
from services.env_updater import EnvUpdater

router = Router()
logger = logging.getLogger(__name__)

# Constants
USERS_PER_PAGE = 10

# Group names for broadcast
GROUP_NAMES = {
    'all': '👥 Все пользователи',
    'male': '👨 Мужчины',
    'female': '👩 Женщины',
    'completed': '✅ Получили открытку',
    'incomplete': '⏳ Не дошли до открытки',
    'personal': '👤 Персональная рассылка',
    'admins': '🧪 Тестовая рассылка (админы)'
}


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


# === NEW HANDLERS ===

@router.message(F.text == "Перейти в группу")
async def show_group_link(message: Message):
    """Show link to forum group."""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        text="📢 <b>Форум группы Pride34:</b>",
        reply_markup=get_group_link_keyboard()
    )


# == Winners Count Handlers ==

@router.message(F.text == "Установить кол-во победителей")
async def show_winners_count_menu(message: Message, state: FSMContext):
    """Show current winners count and menu."""
    if not is_admin(message.from_user.id):
        return

    current_count = settings.WINNERS_COUNT

    text = (
        f"<b>Количество победителей</b>\n\n"
        f"Текущее значение: <code>{current_count}</code>\n\n"
        f"Это количество пользователей, которые будут выбраны "
        f"случайным образом при розыгрыше."
    )

    await message.answer(
        text=text,
        reply_markup=get_winners_count_menu_keyboard()
    )

    await state.set_state(AdminStates.winners_count_menu)


@router.callback_query(F.data == "admin_winners_edit", AdminStates.winners_count_menu)
async def ask_new_winners_count(callback: CallbackQuery, state: FSMContext):
    """Ask for new winners count."""
    await callback.answer()
    await callback.message.delete()

    await callback.message.answer(
        "<b>Введите новое количество победителей</b>\n\n"
        "Должно быть положительным целым числом.\n\n"
        "Для отмены используйте /cancel"
    )

    await state.set_state(AdminStates.winners_count_input)


@router.message(AdminStates.winners_count_input, F.text)
async def handle_winners_count_input(message: Message, state: FSMContext):
    """Handle winners count input and show confirmation."""
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    # Validate input
    try:
        new_count = int(message.text.strip())
        if new_count <= 0:
            raise ValueError("Must be positive")
    except (ValueError, AttributeError):
        await message.answer(
            "❌ Некорректное значение. Введите положительное целое число."
        )
        return

    # Store in state
    await state.update_data(new_winners_count=new_count)

    # Show confirmation
    old_count = settings.WINNERS_COUNT

    text = (
        f"<b>Подтверждение изменения</b>\n\n"
        f"Старое значение: <code>{old_count}</code>\n"
        f"Новое значение: <code>{new_count}</code>\n\n"
        f"Сохранить изменения?"
    )

    await message.answer(
        text=text,
        reply_markup=get_winners_count_confirm_keyboard()
    )

    await state.set_state(AdminStates.winners_count_confirm)


@router.callback_query(F.data == "admin_winners_save", AdminStates.winners_count_confirm)
async def save_winners_count(callback: CallbackQuery, state: FSMContext):
    """Save winners count to .env file."""
    await callback.answer()

    data = await state.get_data()
    new_count = data.get("new_winners_count")

    if not new_count:
        await callback.message.answer("Ошибка: значение не найдено")
        await state.clear()
        return

    # Update .env file
    success = EnvUpdater.update_value("WINNERS_COUNT", str(new_count))

    if success:
        await callback.message.edit_text(
            f"✅ <b>Сохранено!</b>\n\n"
            f"Новое количество победителей: <code>{new_count}</code>\n\n"
            f"<i>Примечание: Для применения изменений требуется "
            f"перезапуск бота.</i>"
        )
        logger.info(f"Admin {callback.from_user.id} updated WINNERS_COUNT to {new_count}")
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сохранении в .env файл. "
            "Проверьте логи."
        )

    await state.clear()


@router.callback_query(F.data == "admin_winners_cancel")
async def cancel_winners_count_change(callback: CallbackQuery, state: FSMContext):
    """Cancel winners count change."""
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("❌ Изменение отменено")
    await state.clear()


@router.callback_query(F.data == "admin_back")
async def handle_admin_back(callback: CallbackQuery, state: FSMContext):
    """Handle back button from menu."""
    await callback.answer()
    await callback.message.delete()
    await state.clear()


# == Date Handlers ==

@router.message(F.text == "Установить дату розыгрыша")
async def show_date_menu(message: Message, state: FSMContext):
    """Show current raffle date and menu."""
    if not is_admin(message.from_user.id):
        return

    current_date = settings.QUIZ_END_DATE

    text = (
        f"<b>Дата окончания розыгрыша</b>\n\n"
        f"Текущая дата: <code>{current_date}</code>\n\n"
        f"Это дата, когда будет проведён розыгрыш призов."
    )

    await message.answer(
        text=text,
        reply_markup=get_date_menu_keyboard()
    )

    await state.set_state(AdminStates.date_menu)


@router.callback_query(F.data == "admin_date_edit", AdminStates.date_menu)
async def ask_new_date(callback: CallbackQuery, state: FSMContext):
    """Ask for new raffle date."""
    await callback.answer()
    await callback.message.delete()

    await callback.message.answer(
        "<b>Введите новую дату розыгрыша</b>\n\n"
        "Формат: <code>ДД-ММ-ГГГГ</code>\n"
        "Пример: <code>31-12-2025</code>\n\n"
        "Для отмены используйте /cancel"
    )

    await state.set_state(AdminStates.date_input)


@router.message(AdminStates.date_input, F.text)
async def handle_date_input(message: Message, state: FSMContext):
    """Handle date input and show confirmation."""
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    input_date = message.text.strip()

    # Validate date format
    try:
        # Parse DD-MM-YYYY
        date_obj = datetime.strptime(input_date, "%d-%m-%Y")

        # Check if date is in the future
        if date_obj < datetime.now():
            await message.answer(
                "❌ Дата должна быть в будущем. Попробуйте снова."
            )
            return

    except ValueError:
        await message.answer(
            "❌ Некорректный формат даты.\n\n"
            "Используйте формат: <code>ДД-ММ-ГГГГ</code>\n"
            "Пример: <code>31-12-2025</code>"
        )
        return

    # Store in state (keep DD-MM-YYYY format)
    await state.update_data(new_date=input_date)

    # Show confirmation
    old_date = settings.QUIZ_END_DATE

    text = (
        f"<b>Подтверждение изменения</b>\n\n"
        f"Старая дата: <code>{old_date}</code>\n"
        f"Новая дата: <code>{input_date}</code>\n\n"
        f"Сохранить изменения?"
    )

    await message.answer(
        text=text,
        reply_markup=get_date_confirm_keyboard()
    )

    await state.set_state(AdminStates.date_confirm)


@router.callback_query(F.data == "admin_date_save", AdminStates.date_confirm)
async def save_date(callback: CallbackQuery, state: FSMContext):
    """Save raffle date to .env file."""
    await callback.answer()

    data = await state.get_data()
    new_date = data.get("new_date")

    if not new_date:
        await callback.message.answer("Ошибка: дата не найдена")
        await state.clear()
        return

    # Update .env file
    success = EnvUpdater.update_value("QUIZ_END_DATE", new_date)

    if success:
        await callback.message.edit_text(
            f"✅ <b>Сохранено!</b>\n\n"
            f"Новая дата розыгрыша: <code>{new_date}</code>\n\n"
            f"<i>Примечание: Для применения изменений требуется "
            f"перезапуск бота.</i>"
        )
        logger.info(f"Admin {callback.from_user.id} updated QUIZ_END_DATE to {new_date}")
    else:
        await callback.message.edit_text(
            "❌ Ошибка при сохранении в .env файл. "
            "Проверьте логи."
        )

    await state.clear()


@router.callback_query(F.data == "admin_date_cancel")
async def cancel_date_change(callback: CallbackQuery, state: FSMContext):
    """Cancel date change."""
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("❌ Изменение отменено")
    await state.clear()


@router.callback_query(F.data == "admin_date_back")
async def handle_date_back(callback: CallbackQuery, state: FSMContext):
    """Handle back button from date menu."""
    await callback.answer()
    await callback.message.delete()
    await state.clear()


# Handle /cancel command in admin flows
@router.message(Command("cancel"))
async def handle_cancel_command(message: Message, state: FSMContext):
    """Handle /cancel command in admin flows."""
    current_state = await state.get_state()

    if current_state and current_state.startswith("AdminStates:"):
        await state.clear()
        await message.answer("❌ Операция отменена")


@router.callback_query(F.data == "admin_noop")
async def handle_noop(callback: CallbackQuery):
    """Handle no-op callback (for disabled buttons)."""
    await callback.answer()
# == Enhanced Broadcast Handlers ==

@router.message(F.text == "Отправить рассылку")
async def start_enhanced_broadcast(message: Message, state: FSMContext):
    """Start enhanced broadcast with group selection."""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "<b>📢 Отправка рассылки</b>\n\n"
        "Выберите группу получателей:",
        reply_markup=get_broadcast_group_select_keyboard()
    )

    await state.set_state(AdminStates.broadcast_select_group)


@router.callback_query(F.data.startswith("broadcast_group_"))
async def handle_group_selection(callback: CallbackQuery, state: FSMContext):
    """Handle broadcast group selection."""
    await callback.answer()

    group_type = callback.data.replace("broadcast_group_", "")

    # Handle personal broadcast separately
    if group_type == "personal":
        await callback.message.edit_text(
            "<b>👤 Персональная рассылка</b>\n\n"
            "Введите Telegram ID пользователя:"
        )
        await state.update_data(broadcast_group='personal')
        await state.set_state(AdminStates.broadcast_personal_id_input)
        return

    # Get users for selected group
    async with async_session_maker() as session:
        users = await UserCRUD.get_users_by_filter(session, group_type)

    if not users:
        await callback.message.edit_text(
            f"❌ В группе <b>{GROUP_NAMES[group_type]}</b> нет пользователей.\n\n"
            "Выберите другую группу:",
            reply_markup=get_broadcast_group_select_keyboard()
        )
        return

    # Store group info
    total_pages = math.ceil(len(users) / USERS_PER_PAGE)
    await state.update_data(
        broadcast_group=group_type,
        broadcast_users=[u.id for u in users],
        broadcast_total_pages=total_pages,
        broadcast_current_page=0
    )

    # Show preview
    await show_group_preview_page(callback.message, state, 0)
    await state.set_state(AdminStates.broadcast_preview_group)


@router.message(AdminStates.broadcast_personal_id_input, F.text)
async def handle_personal_id_input(message: Message, state: FSMContext):
    """Handle personal broadcast user ID input."""
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID. Введите число:")
        return

    # Check if user exists
    async with async_session_maker() as session:
        user = await UserCRUD.get(session, user_id)

    if not user:
        await message.answer(
            f"❌ Пользователь с ID <code>{user_id}</code> не найден.\n\n"
            "Попробуйте другой ID:"
        )
        return

    # Store single user
    display_name = user.full_name or f"User {user.id}"
    await state.update_data(
        broadcast_group='personal',
        broadcast_users=[user_id]
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await message.answer(
        f"<b>👤 Персональная рассылка</b>\n\n"
        f"Получатель: {display_name}\n"
        f"ID: <code>{user_id}</code>\n\n"
        "Отправьте сообщение для рассылки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_broadcast_cancel")
        ]])
    )

    await state.set_state(AdminStates.broadcast_waiting_message)


async def show_group_preview_page(message: Message, state: FSMContext, page: int):
    """Display a page of users in selected group."""
    data = await state.get_data()
    user_ids = data.get("broadcast_users", [])
    total_pages = data.get("broadcast_total_pages", 1)
    group_type = data.get("broadcast_group", "all")

    # Get users for this page
    start_idx = page * USERS_PER_PAGE
    end_idx = start_idx + USERS_PER_PAGE
    page_user_ids = user_ids[start_idx:end_idx]

    # Fetch details
    async with async_session_maker() as session:
        users = []
        for uid in page_user_ids:
            user = await UserCRUD.get(session, uid)
            if user:
                users.append(user)

    # Build text
    group_name = GROUP_NAMES[group_type]
    text = f"<b>{group_name}</b>\n"
    text += f"Страница {page + 1}/{total_pages}\n\n"
    text += f"📊 Всего получателей: {len(user_ids)}\n\n"

    for user in users:
        display_name = user.full_name or f"User {user.id}"
        gender_emoji = "👨" if user.gender == "male" else "👩"
        status_emoji = "✅" if user.quiz_completed else "⏳"

        if user.forum_topic_id:
            link = f"https://t.me/c/3652398755/{user.forum_topic_id}"
            text += f'{gender_emoji}{status_emoji} <a href="{link}">{display_name}</a>\n'
        else:
            text += f"{gender_emoji}{status_emoji} {display_name}\n"

    try:
        await message.edit_text(
            text=text,
            reply_markup=get_broadcast_preview_keyboard(page, total_pages, group_name),
            disable_web_page_preview=True
        )
    except:
        await message.answer(
            text=text,
            reply_markup=get_broadcast_preview_keyboard(page, total_pages, group_name),
            disable_web_page_preview=True
        )


@router.callback_query(F.data.startswith("broadcast_preview_page_"))
async def handle_preview_pagination(callback: CallbackQuery, state: FSMContext):
    """Handle pagination in group preview."""
    await callback.answer()

    page = int(callback.data.split("_")[-1])
    await state.update_data(broadcast_current_page=page)
    await show_group_preview_page(callback.message, state, page)


@router.callback_query(F.data == "broadcast_write_message")
async def broadcast_write_message(callback: CallbackQuery, state: FSMContext):
    """Proceed to message input."""
    await callback.answer()

    await callback.message.edit_text(
        "📢 <b>Отправьте сообщение для рассылки</b>\n\n"
        "Поддерживается:\n"
        "• Текст с HTML-форматированием\n"
        "• Фото с подписью\n"
        "• Видео с подписью\n"
        "• Документы\n\n"
        "Для отмены используйте /cancel"
    )

    await state.set_state(AdminStates.broadcast_waiting_message)


@router.callback_query(F.data == "broadcast_change_group")
async def broadcast_change_group(callback: CallbackQuery, state: FSMContext):
    """Return to group selection."""
    await callback.answer()

    await callback.message.edit_text(
        "<b>📢 Отправка рассылки</b>\n\n"
        "Выберите группу получателей:",
        reply_markup=get_broadcast_group_select_keyboard()
    )

    await state.set_state(AdminStates.broadcast_select_group)


# == Old Broadcast Handlers (for compatibility) ==

async def start_broadcast_flow_old(message: Message, state: FSMContext):
    """Old broadcast flow - kept for compatibility."""
    if not is_admin(message.from_user.id):
        return

    # Get all quiz-completed users
    async with async_session_maker() as session:
        users = await UserCRUD.get_all_participants(session)

    if not users:
        await message.answer("Нет пользователей для рассылки.")
        return

    total_pages = math.ceil(len(users) / USERS_PER_PAGE)

    # Store in state
    await state.update_data(
        broadcast_users=[u.id for u in users],  # Store only IDs
        broadcast_current_page=0,
        broadcast_total_pages=total_pages
    )

    # Show first page
    await show_broadcast_user_page(message, state, 0)
    await state.set_state(AdminStates.broadcast_viewing_users)


async def show_broadcast_user_page(message: Message, state: FSMContext, page: int):
    """Display a page of users for broadcast preview."""
    data = await state.get_data()
    user_ids = data.get("broadcast_users", [])
    total_pages = data.get("broadcast_total_pages", 1)

    # Get users for this page
    start_idx = page * USERS_PER_PAGE
    end_idx = start_idx + USERS_PER_PAGE
    page_user_ids = user_ids[start_idx:end_idx]

    # Fetch user details
    async with async_session_maker() as session:
        users = []
        for uid in page_user_ids:
            user = await UserCRUD.get(session, uid)
            if user:
                users.append(user)

    # Build user list text
    text = f"<b>Получатели рассылки (страница {page + 1}/{total_pages}):</b>\n\n"
    text += f"Всего пользователей: {len(user_ids)}\n\n"

    for user in users:
        # Format display name
        if user.full_name and user.full_name.strip():
            display_name = user.full_name
        else:
            display_name = f"User {user.id}"

        # Create link to forum topic
        if user.forum_topic_id:
            link = f"https://t.me/c/3652398755/{user.forum_topic_id}"
            text += f'• <a href="{link}">{display_name}</a>\n'
        else:
            text += f"• {display_name} (нет топика)\n"

    await message.answer(
        text=text,
        reply_markup=get_broadcast_pagination_keyboard(page, total_pages),
        disable_web_page_preview=True
    )


@router.callback_query(F.data.startswith("admin_broadcast_page_"))
async def handle_broadcast_pagination(callback: CallbackQuery, state: FSMContext):
    """Handle pagination for broadcast user list."""
    await callback.answer()

    page = int(callback.data.split("_")[-1])
    await state.update_data(broadcast_current_page=page)

    await callback.message.delete()
    await show_broadcast_user_page(callback.message, state, page)


@router.callback_query(F.data == "admin_broadcast_continue")
async def broadcast_ask_message(callback: CallbackQuery, state: FSMContext):
    """Ask admin for broadcast message."""
    await callback.answer()
    await callback.message.delete()

    await callback.message.answer(
        "📢 <b>Отправьте сообщение для рассылки</b>\n\n"
        "Поддерживается:\n"
        "• Текст с HTML-форматированием\n"
        "• Фото с подписью\n"
        "• Видео с подписью\n\n"
        "Для отмены используйте /cancel"
    )

    await state.set_state(AdminStates.broadcast_waiting_message)


@router.message(AdminStates.broadcast_waiting_message)
async def handle_broadcast_message_input(message: Message, state: FSMContext):
    """Handle broadcast message input and show confirmation."""
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    # Store message details
    await state.update_data(
        broadcast_message_id=message.message_id,
        broadcast_chat_id=message.chat.id
    )

    data = await state.get_data()
    total_users = len(data.get("broadcast_users", []))

    # Show confirmation
    confirm_text = (
        f"<b>Подтверждение рассылки</b>\n\n"
        f"Получателей: {total_users}\n\n"
        f"Готовы отправить?"
    )

    await message.answer(
        text=confirm_text,
        reply_markup=get_broadcast_confirm_keyboard()
    )

    await state.set_state(AdminStates.broadcast_confirmation)


@router.callback_query(F.data == "admin_broadcast_send", AdminStates.broadcast_confirmation)
async def execute_broadcast(callback: CallbackQuery, state: FSMContext):
    """Execute the broadcast to all users."""
    await callback.answer()

    data = await state.get_data()
    user_ids = data.get("broadcast_users", [])
    message_id = data.get("broadcast_message_id")
    chat_id = data.get("broadcast_chat_id")

    if not user_ids or not message_id:
        await callback.message.answer("Ошибка: данные рассылки не найдены")
        await state.clear()
        return

    # Delete confirmation message
    await callback.message.delete()

    # Start broadcasting
    status_msg = await callback.message.answer(
        f"🚀 Начинаю рассылку...\n\n"
        f"Отправлено: 0/{len(user_ids)}"
    )

    success_count = 0
    failed_count = 0

    for i, user_id in enumerate(user_ids, 1):
        try:
            # Copy message to user
            await callback.bot.copy_message(
                chat_id=user_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            success_count += 1

            # Update status every 10 users
            if i % 10 == 0:
                await status_msg.edit_text(
                    f"🚀 Рассылка в процессе...\n\n"
                    f"Отправлено: {success_count}/{len(user_ids)}\n"
                    f"Ошибок: {failed_count}"
                )

            # Anti-flood delay
            await asyncio.sleep(0.05)

        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            failed_count += 1

    # Final report
    final_text = (
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 Статистика:\n"
        f"• Всего пользователей: {len(user_ids)}\n"
        f"• Успешно отправлено: {success_count}\n"
        f"• Ошибок: {failed_count}\n"
        f"• Процент доставки: {(success_count/len(user_ids)*100):.1f}%"
    )

    await status_msg.edit_text(final_text)
    await state.clear()

    logger.info(
        f"Broadcast completed by admin {callback.from_user.id}: "
        f"{success_count} sent, {failed_count} failed"
    )


@router.callback_query(F.data == "admin_broadcast_cancel")
async def cancel_broadcast_flow(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast flow."""
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("❌ Рассылка отменена")
    await state.clear()
