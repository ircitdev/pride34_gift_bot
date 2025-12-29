"""Keyboard builders for the bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from bot.texts import TextManager


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Get start button keyboard."""
    builder = InlineKeyboardBuilder()
    button_text = TextManager.get('buttons.start', 'Я готов!')
    builder.button(text=button_text, callback_data="start_quiz")
    return builder.as_markup()


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Get gender selection keyboard."""
    builder = InlineKeyboardBuilder()
    male_text = TextManager.get('buttons.gender_male', 'Мужской')
    female_text = TextManager.get('buttons.gender_female', 'Женский')
    builder.button(text=male_text, callback_data="gender_male")
    builder.button(text=female_text, callback_data="gender_female")
    builder.adjust(2)
    return builder.as_markup()


def get_quiz_keyboard(question_number: int, options: list) -> InlineKeyboardMarkup:
    """Get quiz answer keyboard."""
    builder = InlineKeyboardBuilder()

    for idx, option in enumerate(options):
        builder.button(
            text=option,
            callback_data=f"quiz_{question_number}_{idx}"
        )

    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_share_keyboard(bot_username: str, user_id: int, has_premium: bool = False) -> InlineKeyboardMarkup:
    """
    Get share result keyboard with social sharing options.

    Args:
        bot_username: Bot username for creating referral link
        user_id: User ID for referral system
        has_premium: Whether user has Telegram Premium (for native sharing)
    """
    builder = InlineKeyboardBuilder()

    # Instagram sharing
    builder.button(text="Поделиться в Instagram", url="https://www.instagram.com/pride34.ru/")

    # VK sharing
    vk_share_url = "https://vk.com/share.php?url=https://t.me/PRIDE34_GIFT_BOT"
    builder.button(text="Поделиться в VK", url=vk_share_url)

    # Telegram native sharing (only for Premium users)
    if has_premium:
        builder.button(
            text="Поделиться в Telegram",
            url=f"https://t.me/share/url?url=https://t.me/{bot_username}?start=ref{user_id}"
        )

    # Referral sharing - opens contact list via switch_inline_query
    builder.button(text="🎁 Рассказать друзьям", callback_data="share_with_friends")

    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Get admin panel keyboard with 10 buttons."""
    builder = ReplyKeyboardBuilder()

    # Row 1
    builder.button(text="Статистика")
    builder.button(text="Розыгрыш")

    # Row 2
    builder.button(text="Победители")
    builder.button(text="Экспорт данных")

    # Row 3
    builder.button(text="Перейти в группу")
    builder.button(text="Отправить рассылку")

    # Row 4
    builder.button(text="Установить кол-во победителей")
    builder.button(text="Установить дату розыгрыша")

    # Row 5
    builder.button(text="Редактировать тексты")
    builder.button(text="Выдать сертификат")

    builder.adjust(2, 2, 2, 2, 2)  # 5 rows x 2 buttons
    return builder.as_markup(resize_keyboard=True)


def get_group_link_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with link to forum group."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Открыть группу",
        url="https://t.me/+1MPUf8FMfFw3MDgy"
    )
    return builder.as_markup()


def get_broadcast_pagination_keyboard(
    current_page: int,
    total_pages: int
) -> InlineKeyboardMarkup:
    """Get pagination keyboard for broadcast user list."""
    builder = InlineKeyboardBuilder()

    # Navigation buttons
    if current_page > 0:
        builder.button(text="◀️ Назад", callback_data=f"admin_broadcast_page_{current_page - 1}")
    else:
        builder.button(text=" ", callback_data="admin_noop")

    # Page indicator
    builder.button(
        text=f"{current_page + 1}/{total_pages}",
        callback_data="admin_noop"
    )

    if current_page < total_pages - 1:
        builder.button(text="Вперед ▶️", callback_data=f"admin_broadcast_page_{current_page + 1}")
    else:
        builder.button(text=" ", callback_data="admin_noop")

    builder.adjust(3)

    # Action buttons
    builder.button(text="Продолжить ➡️", callback_data="admin_broadcast_continue")
    builder.button(text="❌ Отмена", callback_data="admin_broadcast_cancel")

    builder.adjust(3, 2)
    return builder.as_markup()


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard for broadcast."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить", callback_data="admin_broadcast_send")
    builder.button(text="❌ Отмена", callback_data="admin_broadcast_cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_winners_count_menu_keyboard() -> InlineKeyboardMarkup:
    """Get winners count menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить", callback_data="admin_winners_edit")
    builder.button(text="◀️ Назад", callback_data="admin_back")
    builder.adjust(2)
    return builder.as_markup()


def get_winners_count_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get winners count confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Сохранить", callback_data="admin_winners_save")
    builder.button(text="❌ Отмена", callback_data="admin_winners_cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_date_menu_keyboard() -> InlineKeyboardMarkup:
    """Get date menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить", callback_data="admin_date_edit")
    builder.button(text="◀️ Назад", callback_data="admin_date_back")
    builder.adjust(2)
    return builder.as_markup()


def get_date_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get date confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Сохранить", callback_data="admin_date_save")
    builder.button(text="❌ Отмена", callback_data="admin_date_cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_broadcast_group_select_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting broadcast target group."""
    builder = InlineKeyboardBuilder()

    # Groups
    builder.button(text="👥 Все пользователи", callback_data="broadcast_group_all")
    builder.button(text="👨 Мужчины", callback_data="broadcast_group_male")
    builder.button(text="👩 Женщины", callback_data="broadcast_group_female")
    builder.button(text="✅ Получили открытку", callback_data="broadcast_group_completed")
    builder.button(text="⏳ Не дошли до открытки", callback_data="broadcast_group_incomplete")
    builder.button(text="👤 Персонально (по ID)", callback_data="broadcast_group_personal")
    builder.button(text="🧪 Тест (только админы)", callback_data="broadcast_group_admins")
    builder.button(text="❌ Отмена", callback_data="admin_broadcast_cancel")

    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_broadcast_preview_keyboard(
    current_page: int,
    total_pages: int,
    group_name: str
) -> InlineKeyboardMarkup:
    """Get preview keyboard with group info."""
    builder = InlineKeyboardBuilder()

    # Navigation
    if current_page > 0:
        builder.button(text="◀️", callback_data=f"broadcast_preview_page_{current_page - 1}")
    else:
        builder.button(text=" ", callback_data="admin_noop")

    builder.button(text=f"{current_page + 1}/{total_pages}", callback_data="admin_noop")

    if current_page < total_pages - 1:
        builder.button(text="▶️", callback_data=f"broadcast_preview_page_{current_page + 1}")
    else:
        builder.button(text=" ", callback_data="admin_noop")

    builder.adjust(3)

    # Actions
    builder.button(text="✏️ Написать сообщение", callback_data="broadcast_write_message")
    builder.button(text="🔙 Выбрать другую группу", callback_data="broadcast_change_group")
    builder.button(text="❌ Отмена", callback_data="admin_broadcast_cancel")

    builder.adjust(3, 1, 1, 1)
    return builder.as_markup()


def get_text_edit_categories_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for text editing categories."""
    builder = InlineKeyboardBuilder()

    categories = [
        ('👋 Приветствие', 'text_cat_welcome'),
        ('❓ Вопросы квиза', 'text_cat_quiz'),
        ('👤 Выбор пола', 'text_cat_gender'),
        ('📸 Запрос фото', 'text_cat_photo'),
        ('🔮 Предсказания', 'text_cat_predictions'),
        ('🔘 Кнопки', 'text_cat_buttons'),
    ]

    for title, callback in categories:
        builder.button(text=title, callback_data=callback)

    builder.button(text="◀️ Назад в админку", callback_data="text_back_admin")
    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_text_items_keyboard(category: str, items: list) -> InlineKeyboardMarkup:
    """Get keyboard for selecting text item to edit."""
    builder = InlineKeyboardBuilder()

    for item_key, item_title in items:
        builder.button(text=item_title, callback_data=f"text_item_{item_key}")

    builder.button(text="◀️ Назад к категориям", callback_data="text_back_categories")
    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_text_edit_back_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with back button for text editing."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="text_back_categories")
    return builder.as_markup()


def get_certificate_users_keyboard(
    users: list,
    current_page: int,
    total_pages: int
) -> InlineKeyboardMarkup:
    """Get keyboard with paginated user list for certificates."""
    builder = InlineKeyboardBuilder()

    # User buttons
    for user in users:
        if user.full_name and user.full_name.strip():
            button_text = user.full_name
        elif user.username:
            button_text = f"@{user.username}"
        else:
            button_text = f"User {user.id}"

        if len(button_text) > 30:
            button_text = button_text[:27] + "..."

        builder.button(text=button_text, callback_data=f"cert_select_{user.id}")

    builder.adjust(2)  # 2 кнопки в ряду

    # Navigation
    if current_page > 0:
        builder.button(text="◀️ Назад", callback_data=f"cert_page_{current_page - 1}")
    else:
        builder.button(text=" ", callback_data="admin_noop")

    builder.button(text=f"{current_page + 1}/{total_pages}", callback_data="admin_noop")

    if current_page < total_pages - 1:
        builder.button(text="Вперед ▶️", callback_data=f"cert_page_{current_page + 1}")
    else:
        builder.button(text=" ", callback_data="admin_noop")

    builder.adjust(2, 2, 3)

    # Exit
    builder.button(text="❌ Выйти", callback_data="cert_exit")
    builder.adjust(2, 2, 3, 1)

    return builder.as_markup()


def get_certificate_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard for certificate sending."""
    builder = InlineKeyboardBuilder()

    builder.button(text="✅ Да, отправить", callback_data="cert_confirm_yes")
    builder.button(text="❌ Отмена", callback_data="cert_confirm_no")

    builder.adjust(2)
    return builder.as_markup()


def get_certificate_after_send_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard after certificate was sent."""
    builder = InlineKeyboardBuilder()

    builder.button(text="📜 Отправить еще", callback_data="cert_send_another")
    builder.button(text="🚪 Выйти", callback_data="cert_exit")

    builder.adjust(2)
    return builder.as_markup()
