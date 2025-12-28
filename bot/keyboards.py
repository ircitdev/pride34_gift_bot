"""Keyboard builders for the bot."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Get start button keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Начать квиз /start", callback_data="start_quiz")
    return builder.as_markup()


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Get gender selection keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Мужской", callback_data="gender_male")
    builder.button(text="Женский", callback_data="gender_female")
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


def get_share_keyboard() -> InlineKeyboardMarkup:
    """Get share result keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Поделиться в Instagram", url="https://www.instagram.com/pride34.ru/")
    builder.button(text="Начать заново", callback_data="start_quiz")
    builder.adjust(1)
    return builder.as_markup()


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Get admin panel keyboard with 8 buttons."""
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

    builder.adjust(2, 2, 2, 2)  # 4 rows with 2 buttons each
    return builder.as_markup(resize_keyboard=True)


def get_group_link_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard with link to forum group."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Открыть группу",
        url="https://t.me/c/3652398755/"
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
