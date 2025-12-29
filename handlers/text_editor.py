"""Text editor handlers for admin."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards import (
    get_text_edit_categories_keyboard,
    get_text_items_keyboard,
    get_text_edit_back_keyboard,
    get_admin_keyboard
)
from bot.states import AdminStates
from bot.texts import TextManager
from config import settings

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in settings.admin_ids_list


@router.message(F.text == "Редактировать тексты")
async def text_edit_menu(message: Message, state: FSMContext):
    """Show text editing categories."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return

    await message.answer(
        "📝 <b>Редактирование текстов бота</b>\n\n"
        "Выберите категорию для редактирования:",
        reply_markup=get_text_edit_categories_keyboard()
    )
    await state.set_state(AdminStates.text_edit_category)


@router.callback_query(F.data == "text_back_admin")
async def text_back_to_admin(callback: CallbackQuery, state: FSMContext):
    """Return to admin panel."""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("◀️ Возврат в админ-панель")
    await callback.message.answer(
        "🔐 <b>Админ-панель</b>",
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "text_back_categories")
async def text_back_to_categories(callback: CallbackQuery, state: FSMContext):
    """Return to category selection."""
    await callback.answer()
    await callback.message.edit_text(
        "📝 <b>Редактирование текстов бота</b>\n\n"
        "Выберите категорию для редактирования:",
        reply_markup=get_text_edit_categories_keyboard()
    )
    await state.set_state(AdminStates.text_edit_category)


# Welcome text editing
@router.callback_query(F.data == "text_cat_welcome")
async def edit_welcome_text(callback: CallbackQuery, state: FSMContext):
    """Edit welcome message."""
    await callback.answer()

    current_text = TextManager.get('welcome.text')

    await callback.message.edit_text(
        f"📝 <b>Редактирование: Приветственное сообщение</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text}\n\n"
        f"Отправьте новый текст сообщения:",
        reply_markup=get_text_edit_back_keyboard()
    )

    await state.update_data(edit_path='welcome.text', edit_title='Приветственное сообщение')
    await state.set_state(AdminStates.text_edit_input)


# Gender selection text editing
@router.callback_query(F.data == "text_cat_gender")
async def edit_gender_text(callback: CallbackQuery, state: FSMContext):
    """Edit gender selection message."""
    await callback.answer()

    current_text = TextManager.get('gender.text')

    await callback.message.edit_text(
        f"📝 <b>Редактирование: Выбор пола</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text}\n\n"
        f"Отправьте новый текст сообщения:",
        reply_markup=get_text_edit_back_keyboard()
    )

    await state.update_data(edit_path='gender.text', edit_title='Выбор пола')
    await state.set_state(AdminStates.text_edit_input)


# Photo request text editing
@router.callback_query(F.data == "text_cat_photo")
async def edit_photo_text(callback: CallbackQuery, state: FSMContext):
    """Edit photo request message."""
    await callback.answer()

    current_text = TextManager.get('photo.text')

    await callback.message.edit_text(
        f"📝 <b>Редактирование: Запрос фото</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text}\n\n"
        f"Отправьте новый текст сообщения:",
        reply_markup=get_text_edit_back_keyboard()
    )

    await state.update_data(edit_path='photo.text', edit_title='Запрос фото')
    await state.set_state(AdminStates.text_edit_input)


# Quiz questions editing
@router.callback_query(F.data == "text_cat_quiz")
async def show_quiz_questions(callback: CallbackQuery, state: FSMContext):
    """Show list of quiz questions to edit."""
    await callback.answer()

    items = []
    for i in range(1, 6):
        question_text = TextManager.get(f'quiz.question_{i}.text')
        short_text = question_text[:50] + "..." if len(question_text) > 50 else question_text
        items.append((f'quiz_q{i}', f'Вопрос {i}: {short_text}'))

    await callback.message.edit_text(
        "❓ <b>Вопросы квиза</b>\n\n"
        "Выберите вопрос для редактирования:",
        reply_markup=get_text_items_keyboard('quiz', items)
    )
    await state.set_state(AdminStates.text_edit_item)


@router.callback_query(F.data.startswith("text_item_quiz_q"))
async def edit_quiz_question(callback: CallbackQuery, state: FSMContext):
    """Edit specific quiz question."""
    await callback.answer()

    # Extract question number
    q_num = callback.data.split('_')[-1][1]  # Gets number from 'quiz_q1'

    current_text = TextManager.get(f'quiz.question_{q_num}.text')
    options = TextManager.get_list(f'quiz.question_{q_num}.options')

    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])

    items = [
        (f'quiz_q{q_num}_text', '📝 Редактировать текст вопроса'),
        (f'quiz_q{q_num}_opt0', f'1️⃣ {options[0][:30]}...'),
        (f'quiz_q{q_num}_opt1', f'2️⃣ {options[1][:30]}...'),
        (f'quiz_q{q_num}_opt2', f'3️⃣ {options[2][:30]}...'),
        (f'quiz_q{q_num}_opt3', f'4️⃣ {options[3][:30]}...'),
    ]

    await callback.message.edit_text(
        f"❓ <b>Вопрос {q_num}</b>\n\n"
        f"<b>Текст вопроса:</b>\n{current_text}\n\n"
        f"<b>Варианты ответов:</b>\n{options_text}\n\n"
        f"Что хотите отредактировать?",
        reply_markup=get_text_items_keyboard('quiz_detail', items)
    )


@router.callback_query(F.data.startswith("text_item_quiz_q") & F.data.contains("_text"))
async def edit_quiz_question_text(callback: CallbackQuery, state: FSMContext):
    """Edit quiz question text."""
    await callback.answer()

    # Extract question number
    parts = callback.data.split('_')
    q_num = parts[3][1]  # Gets number from 'quiz_q1_text'

    current_text = TextManager.get(f'quiz.question_{q_num}.text')

    await callback.message.edit_text(
        f"📝 <b>Редактирование текста вопроса {q_num}</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text}\n\n"
        f"Отправьте новый текст вопроса:",
        reply_markup=get_text_edit_back_keyboard()
    )

    await state.update_data(
        edit_path=f'quiz.question_{q_num}.text',
        edit_title=f'Вопрос {q_num}'
    )
    await state.set_state(AdminStates.text_edit_input)


@router.callback_query(F.data.startswith("text_item_quiz_q") & F.data.contains("_opt"))
async def edit_quiz_option(callback: CallbackQuery, state: FSMContext):
    """Edit quiz question option."""
    await callback.answer()

    # Extract question number and option number
    parts = callback.data.split('_')
    q_num = parts[3][1]  # Gets number from 'quiz_q1_opt0'
    opt_num = parts[3][-1]  # Gets option number

    current_text = TextManager.get_list(f'quiz.question_{q_num}.options')[int(opt_num)]

    await callback.message.edit_text(
        f"📝 <b>Редактирование варианта ответа {int(opt_num)+1}</b>\n"
        f"<b>Вопрос {q_num}</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text}\n\n"
        f"Отправьте новый текст варианта:",
        reply_markup=get_text_edit_back_keyboard()
    )

    await state.update_data(
        edit_path=f'quiz.question_{q_num}.options.{opt_num}',
        edit_title=f'Вопрос {q_num}, вариант {int(opt_num)+1}',
        is_list_item=True,
        list_path=f'quiz.question_{q_num}.options',
        list_index=int(opt_num)
    )
    await state.set_state(AdminStates.text_edit_input)


# Predictions editing
@router.callback_query(F.data == "text_cat_predictions")
async def show_predictions(callback: CallbackQuery, state: FSMContext):
    """Show list of predictions to edit."""
    await callback.answer()

    predictions = {
        'fitness_enthusiast': '💪 Фитнес-энтузиаст',
        'balanced_lifestyle': '⚖️ Сбалансированный подход',
        'sweet_lover': '🍬 Любитель сладкого',
        'beginner': '🌟 Новичок',
        'default': '📌 По умолчанию'
    }

    items = [(f'pred_{key}', title) for key, title in predictions.items()]

    await callback.message.edit_text(
        "🔮 <b>Предсказания</b>\n\n"
        "Выберите предсказание для редактирования:",
        reply_markup=get_text_items_keyboard('predictions', items)
    )
    await state.set_state(AdminStates.text_edit_item)


@router.callback_query(F.data.startswith("text_item_pred_"))
async def edit_prediction(callback: CallbackQuery, state: FSMContext):
    """Edit specific prediction."""
    await callback.answer()

    # Extract prediction key
    pred_key = callback.data.replace('text_item_pred_', '')

    current_text = TextManager.get(f'predictions.{pred_key}')

    pred_names = {
        'fitness_enthusiast': 'Фитнес-энтузиаст',
        'balanced_lifestyle': 'Сбалансированный подход',
        'sweet_lover': 'Любитель сладкого',
        'beginner': 'Новичок',
        'default': 'По умолчанию'
    }

    await callback.message.edit_text(
        f"🔮 <b>Редактирование предсказания: {pred_names.get(pred_key, pred_key)}</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text}\n\n"
        f"Отправьте новый текст предсказания:",
        reply_markup=get_text_edit_back_keyboard()
    )

    await state.update_data(
        edit_path=f'predictions.{pred_key}',
        edit_title=f'Предсказание: {pred_names.get(pred_key, pred_key)}'
    )
    await state.set_state(AdminStates.text_edit_input)


# Buttons editing
@router.callback_query(F.data == "text_cat_buttons")
async def show_buttons(callback: CallbackQuery, state: FSMContext):
    """Show list of buttons to edit."""
    await callback.answer()

    items = [
        ('btn_start', f'🎯 Кнопка "Начать": {TextManager.get("buttons.start")}'),
        ('btn_male', f'👨 Кнопка "Мужской": {TextManager.get("buttons.gender_male")}'),
        ('btn_female', f'👩 Кнопка "Женский": {TextManager.get("buttons.gender_female")}'),
    ]

    await callback.message.edit_text(
        "🔘 <b>Кнопки</b>\n\n"
        "Выберите кнопку для редактирования:",
        reply_markup=get_text_items_keyboard('buttons', items)
    )
    await state.set_state(AdminStates.text_edit_item)


@router.callback_query(F.data.startswith("text_item_btn_"))
async def edit_button(callback: CallbackQuery, state: FSMContext):
    """Edit specific button text."""
    await callback.answer()

    # Extract button key
    btn_key = callback.data.replace('text_item_btn_', '')

    path_map = {
        'start': 'buttons.start',
        'male': 'buttons.gender_male',
        'female': 'buttons.gender_female'
    }

    title_map = {
        'start': 'Кнопка "Начать"',
        'male': 'Кнопка "Мужской"',
        'female': 'Кнопка "Женский"'
    }

    path = path_map.get(btn_key)
    current_text = TextManager.get(path)

    await callback.message.edit_text(
        f"🔘 <b>Редактирование: {title_map.get(btn_key)}</b>\n\n"
        f"<b>Текущий текст:</b>\n{current_text}\n\n"
        f"Отправьте новый текст кнопки:",
        reply_markup=get_text_edit_back_keyboard()
    )

    await state.update_data(
        edit_path=path,
        edit_title=title_map.get(btn_key)
    )
    await state.set_state(AdminStates.text_edit_input)


# Handle text input
@router.message(AdminStates.text_edit_input)
async def save_edited_text(message: Message, state: FSMContext):
    """Save edited text."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой функции")
        return

    data = await state.get_data()
    edit_path = data.get('edit_path')
    edit_title = data.get('edit_title')
    is_list_item = data.get('is_list_item', False)

    new_text = message.text

    try:
        if is_list_item:
            # Handle list items (quiz options)
            list_path = data.get('list_path')
            list_index = data.get('list_index')

            # Get current list
            current_list = TextManager.get_list(list_path)
            # Update specific item
            current_list[list_index] = new_text
            # Save entire list
            success = TextManager.set(list_path, current_list)
        else:
            # Handle regular text
            success = TextManager.set(edit_path, new_text)

        if success:
            # Reload texts
            TextManager.load_texts()

            await message.answer(
                f"✅ <b>Текст сохранен!</b>\n\n"
                f"<b>{edit_title}</b>\n"
                f"<b>Новый текст:</b>\n{new_text}\n\n"
                f"Изменения вступят в силу при следующем использовании.",
                reply_markup=get_text_edit_categories_keyboard()
            )
            await state.set_state(AdminStates.text_edit_category)
        else:
            await message.answer(
                "❌ Ошибка при сохранении текста. Попробуйте еще раз.",
                reply_markup=get_text_edit_back_keyboard()
            )
    except Exception as e:
        logger.error(f"Error saving text: {e}")
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=get_text_edit_back_keyboard()
        )
