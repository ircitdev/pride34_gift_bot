# План работ: Расширенная система рассылки и двусторонней коммуникации

## Обзор

Создание продвинутой системы рассылки с группировкой пользователей и двусторонней коммуникацией через форум.

### Ключевые возможности:
1. **Группировка пользователей** - автоматическая сегментация по полу и статусу прохождения квиза
2. **Таргетированная рассылка** - отправка разным группам пользователей
3. **Персональная рассылка** - отправка конкретному пользователю по ID
4. **Тестовая рассылка** - отправка только админам
5. **Двусторонняя коммуникация** - переписка админа с пользователем через форум

---

## Этап 1: Расширение базы данных

### 1.1 Добавить поле quiz_completed в модель User

**Файл:** `database/models.py`

```python
# После поля forum_topic_id добавить:
quiz_completed: Mapped[bool] = mapped_column(Boolean, default=False)  # User completed quiz and got card
```

**Зачем:** Отслеживать пользователей, которые дошли до получения открытки.

---

### 1.2 Обновить CRUD методы

**Файл:** `database/crud.py`

Добавить методы в класс `UserCRUD`:

```python
@staticmethod
async def mark_quiz_completed(session: AsyncSession, user_id: int):
    """Mark user as completed quiz (received card)."""
    await session.execute(
        update(User).where(User.id == user_id).values(quiz_completed=True)
    )
    await session.commit()

@staticmethod
async def get_users_by_filter(
    session: AsyncSession,
    filter_type: str
) -> List[User]:
    """
    Get users by filter type.

    Filter types:
    - 'all': All users
    - 'male': Male users
    - 'female': Female users
    - 'completed': Users who received card
    - 'incomplete': Users who didn't complete quiz
    - 'admins': Admin users only (for testing)
    """
    query = select(User)

    if filter_type == 'male':
        query = query.where(User.gender == 'male')
    elif filter_type == 'female':
        query = query.where(User.gender == 'female')
    elif filter_type == 'completed':
        query = query.where(User.quiz_completed == True)
    elif filter_type == 'incomplete':
        query = query.where(User.quiz_completed == False)
    elif filter_type == 'admins':
        from config import settings
        query = query.where(User.id.in_(settings.admin_ids_list))
    # 'all' - no filter

    result = await session.execute(query)
    return list(result.scalars().all())
```

---

### 1.3 Создать миграцию

**Файл:** `migrate_add_quiz_completed.py` (НОВЫЙ)

```python
"""Migration: Add quiz_completed field to users table."""
import asyncio
from sqlalchemy import text
from database.engine import engine


async def migrate():
    """Add quiz_completed column to users table."""
    print("Starting migration: adding quiz_completed to users table...")

    async with engine.begin() as conn:
        try:
            # Add column
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN quiz_completed BOOLEAN DEFAULT FALSE"
            ))
            print("✅ Added quiz_completed column")

            # Update existing users who have photos as completed
            await conn.execute(text("""
                UPDATE users
                SET quiz_completed = TRUE
                WHERE id IN (SELECT DISTINCT user_id FROM user_photos)
            """))
            print("✅ Marked existing users with photos as completed")

        except Exception as e:
            print(f"⚠️  Column might already exist: {e}")

    print("✅ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## Этап 2: FSM States для новой системы рассылки

**Файл:** `bot/states.py`

Обновить класс `AdminStates`:

```python
class AdminStates(StatesGroup):
    """States for admin panel flows."""

    # ... existing states ...

    # Enhanced broadcast flow
    broadcast_select_group = State()       # Select target group
    broadcast_preview_group = State()      # Preview selected group (paginated)
    broadcast_personal_id_input = State()  # Input user ID for personal message
    broadcast_waiting_message = State()    # Waiting for message content
    broadcast_confirmation = State()       # Confirm before sending
```

---

## Этап 3: Клавиатуры для группировки

**Файл:** `bot/keyboards.py`

### 3.1 Клавиатура выбора группы

```python
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
```

### 3.2 Обновить пагинацию - добавить информацию о группе

```python
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

    builder.adjust(3, 1, 1)
    return builder.as_markup()
```

---

## Этап 4: Обновление обработчиков рассылки

**Файл:** `handlers/admin.py`

### 4.1 Константы для отображения групп

```python
# После USERS_PER_PAGE добавить:
GROUP_NAMES = {
    'all': '👥 Все пользователи',
    'male': '👨 Мужчины',
    'female': '👩 Женщины',
    'completed': '✅ Получили открытку',
    'incomplete': '⏳ Не дошли до открытки',
    'personal': '👤 Персональная рассылка',
    'admins': '🧪 Тестовая рассылка (админы)'
}
```

### 4.2 Новый обработчик "Отправить рассылку"

```python
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
```

### 4.3 Обработчик выбора группы

```python
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
```

### 4.4 Обработчик персональной рассылки

```python
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
```

### 4.5 Helper функция для отображения группы

```python
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
```

### 4.6 Обработчики навигации по превью

```python
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
```

---

## Этап 5: Двусторонняя коммуникация через форум

### 5.1 Добавить таблицу для отслеживания связи пользователь-топик

**Файл:** `database/models.py`

```python
class UserMessage(Base):
    """User message tracking for forum communication."""
    __tablename__ = "user_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    forum_message_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Message ID in forum
    user_message_id: Mapped[int] = mapped_column(Integer, nullable=True)    # Message ID in private chat
    direction: Mapped[str] = mapped_column(String, nullable=False)  # 'to_user' or 'from_user'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

### 5.2 CRUD для сообщений

**Файл:** `database/crud.py`

```python
class UserMessageCRUD:
    """CRUD operations for user messages."""

    @staticmethod
    async def log_message(
        session: AsyncSession,
        user_id: int,
        forum_message_id: int,
        user_message_id: int,
        direction: str
    ):
        """Log a message exchange."""
        message = UserMessage(
            user_id=user_id,
            forum_message_id=forum_message_id,
            user_message_id=user_message_id,
            direction=direction
        )
        session.add(message)
        await session.commit()
```

### 5.3 Создать обработчик сообщений в форуме

**Файл:** `handlers/forum_communication.py` (НОВЫЙ)

```python
"""Forum communication handlers for two-way messaging."""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import ChatMemberUpdatedFilter

from database.engine import async_session_maker
from database.crud import UserCRUD, UserMessageCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.chat.id == settings.FORUM_GROUP_ID, F.message_thread_id)
async def handle_admin_message_in_topic(message: Message):
    """
    Handle admin message in user topic - forward to user.
    Only processes messages in topics (not in general chat).
    """
    topic_id = message.message_thread_id

    if not topic_id:
        return  # Not in a topic

    # Find user by forum_topic_id
    async with async_session_maker() as session:
        # Get user with this topic ID
        result = await session.execute(
            select(User).where(User.forum_topic_id == topic_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"No user found for topic {topic_id}")
        return

    # Don't forward bot's own messages
    if message.from_user.id == message.bot.id:
        return

    # Forward message to user
    try:
        sent_message = await message.bot.copy_message(
            chat_id=user.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Log the message
        async with async_session_maker() as session:
            await UserMessageCRUD.log_message(
                session,
                user_id=user.id,
                forum_message_id=message.message_id,
                user_message_id=sent_message.message_id,
                direction='to_user'
            )

        logger.info(f"Forwarded message from topic {topic_id} to user {user.id}")

    except Exception as e:
        logger.error(f"Failed to forward message to user {user.id}: {e}")
```

### 5.4 Обработчик ответов пользователя

**Файл:** `handlers/user_replies.py` (НОВЫЙ)

```python
"""Handle user replies and forward to forum."""
import logging
from aiogram import Router, F
from aiogram.types import Message

from database.engine import async_session_maker
from database.crud import UserCRUD, UserMessageCRUD
from config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.chat.type == "private", F.from_user.id)
async def handle_user_reply(message: Message):
    """
    Handle user message in private chat - forward to their forum topic.
    Only for users who have completed quiz and have a topic.
    """
    user_id = message.from_user.id

    # Skip admin messages
    if user_id in settings.admin_ids_list:
        return

    # Get user data
    async with async_session_maker() as session:
        user = await UserCRUD.get(session, user_id)

    if not user or not user.forum_topic_id:
        # User doesn't have a forum topic yet
        return

    # Forward to forum topic
    try:
        sent_message = await message.bot.copy_message(
            chat_id=settings.FORUM_GROUP_ID,
            message_thread_id=user.forum_topic_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Log the message
        async with async_session_maker() as session:
            await UserMessageCRUD.log_message(
                session,
                user_id=user_id,
                forum_message_id=sent_message.message_id,
                user_message_id=message.message_id,
                direction='from_user'
            )

        logger.info(f"Forwarded user {user_id} message to topic {user.forum_topic_id}")

    except Exception as e:
        logger.error(f"Failed to forward user {user_id} message to forum: {e}")
```

---

## Этап 6: Обновление photo.py для отметки завершения

**Файл:** `handlers/photo.py`

В функции, где создается топик форума и отправляется открытка, добавить:

```python
# После успешной отправки открытки и создания топика
# Отметить пользователя как завершившего квиз
async with async_session_maker() as session:
    await UserCRUD.mark_quiz_completed(session, user_id)
logger.info(f"Marked user {user_id} as quiz completed")
```

---

## Этап 7: Регистрация новых роутеров

**Файл:** `main.py`

```python
# Импорты
from handlers import (
    start,
    quiz,
    photo,
    admin,
    forum_communication,  # НОВЫЙ
    user_replies          # НОВЫЙ
)

# Регистрация роутеров
dp.include_router(start.router)
dp.include_router(quiz.router)
dp.include_router(photo.router)
dp.include_router(admin.router)
dp.include_router(forum_communication.router)  # НОВЫЙ
dp.include_router(user_replies.router)         # НОВЫЙ
```

---

## Этап 8: Тестирование

### Сценарии тестирования:

**8.1 Группировка пользователей:**
- [ ] Рассылка всем
- [ ] Рассылка только мужчинам
- [ ] Рассылка только женщинам
- [ ] Рассылка получившим открытку
- [ ] Рассылка не дошедшим до открытки
- [ ] Персональная рассылка по ID
- [ ] Тестовая рассылка (только админам)

**8.2 Типы контента:**
- [ ] Текстовое сообщение
- [ ] Фото с подписью
- [ ] Видео с подписью
- [ ] Документ

**8.3 Двусторонняя коммуникация:**
- [ ] Админ пишет в топик → пользователь получает
- [ ] Пользователь отвечает → сообщение в топике форума
- [ ] Логирование сообщений в БД

---

## Последовательность внедрения

1. ✅ **Этап 1:** База данных (models, CRUD, миграция)
2. ✅ **Этап 2:** FSM States
3. ✅ **Этап 3:** Клавиатуры
4. ✅ **Этап 4:** Обработчики рассылки с группировкой
5. ✅ **Этап 5:** Двусторонняя коммуникация (новые роутеры)
6. ✅ **Этап 6:** Обновление photo.py
7. ✅ **Этап 7:** Регистрация роутеров в main.py
8. ✅ **Этап 8:** Тестирование

---

## Важные замечания

### Безопасность:
- Все обработчики проверяют `is_admin()` для админских функций
- Пользовательские сообщения не могут попасть в чужие топики (проверка по forum_topic_id)
- Валидация ID при персональной рассылке

### Производительность:
- Пагинация при показе больших групп (10 пользователей на страницу)
- Сохранение только ID в state, загрузка деталей по требованию
- Anti-flood задержка 0.05с при рассылке

### UX:
- Эмодзи для визуального разделения групп (👨👩✅⏳)
- Превью группы перед отправкой
- Возможность вернуться и выбрать другую группу
- Статистика после рассылки

### Логирование:
- Все пересылки сообщений логируются в БД
- История переписки админ-пользователь сохраняется
- Можно добавить просмотр истории в админ-панель (опционально)

---

## Оценка времени

- **Этап 1:** База данных - 30 мин
- **Этап 2:** States - 15 мин
- **Этап 3:** Клавиатуры - 30 мин
- **Этап 4:** Обработчики рассылки - 2 часа
- **Этап 5:** Двусторонняя коммуникация - 1.5 часа
- **Этап 6:** Обновление photo.py - 15 мин
- **Этап 7:** Регистрация роутеров - 10 мин
- **Этап 8:** Тестирование - 2 часа

**Итого:** ~7 часов для полной реализации

---

## Статус: 🔴 Ожидает команды на внедрение

**Команда для старта:** "Начинай внедрение рассылки"
