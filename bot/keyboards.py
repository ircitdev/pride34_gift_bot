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
    """Get admin panel keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="Статистика")
    builder.button(text="Розыгрыш")
    builder.button(text="Победители")
    builder.button(text="Экспорт данных")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)
