# Инструкция по отладке проблемы с отправкой фото

## Проблема
После отправки фото пользователем ничего не происходит - нет ответа от бота.

## Изменения для отладки

### 1. Добавлено детальное логирование в `handlers/photo.py`

Теперь каждый этап обработки фото логируется с префиксами:
- 📸 PHOTO HANDLER - основной обработчик
- 🔍 PHOTO HANDLER - обнаружение лица
- 💾 PHOTO HANDLER - работа с базой данных
- ⏳ PHOTO HANDLER - обработка изображения
- 📤 PHOTO HANDLER - отправка результата
- ❌ PHOTO HANDLER - ошибки

### 2. Проверочные скрипты

**test_photo_handler.py** - тестирование всей цепочки обработки:
```bash
python test_photo_handler.py
```

**check_bot_handlers.py** - проверка регистрации обработчиков:
```bash
python check_bot_handlers.py
```

## Как отладить проблему

### Шаг 1: Запустить бота с логированием в консоль

```bash
python main.py
```

### Шаг 2: Отправить фото в бота

После отправки фото в логах должна появиться последовательность:

```
INFO - 📸 PHOTO HANDLER: Started for user 123456
INFO - 📸 PHOTO HANDLER: Got photo file_id: xxxxx
INFO - 📸 PHOTO HANDLER: Downloading to user_photos/123456.jpg
INFO - 📸 PHOTO HANDLER: Photo downloaded successfully
INFO - 🔍 PHOTO HANDLER: Starting face detection
INFO - 🔍 PHOTO HANDLER: Image loaded, shape: (height, width, 3)
INFO - 🔍 PHOTO HANDLER: Detected N face(s)
INFO - 💾 PHOTO HANDLER: Saving photo info to database
INFO - ✅ PHOTO HANDLER: Photo info saved to database
INFO - ⏳ PHOTO HANDLER: Sending processing message
INFO - 📋 PHOTO HANDLER: Getting user data from state
INFO - 🎨 PHOTO HANDLER: Starting image generation
INFO - 🎨 PHOTO HANDLER: ImageProcessor created, calling create_christmas_figure
INFO - ✅ PHOTO HANDLER: Image generated successfully
INFO - 💾 PHOTO HANDLER: Updating database with generated path
INFO - ✅ PHOTO HANDLER: Database updated
INFO - 🗑️ PHOTO HANDLER: Deleting processing message
INFO - 📤 PHOTO HANDLER: Sending final result to user
INFO - 📊 SEND_FINAL_RESULT: Starting for user 123456
INFO - 📊 SEND_FINAL_RESULT: Prediction generated
INFO - 📤 SEND_FINAL_RESULT: Sending photo to user
INFO - ✅ SEND_FINAL_RESULT: Photo sent successfully
INFO - ✅ SEND_FINAL_RESULT: Setting state to completed
INFO - ✅ SEND_FINAL_RESULT: Complete
INFO - ✅ PHOTO HANDLER: Final result sent
```

### Шаг 3: Найти где останавливается процесс

Если логи останавливаются на определенном этапе, это укажет на проблему:

1. **Останавливается на "Starting face detection"**
   - Проблема с OpenCV или файлом изображения
   - Проверить что файл создался: `ls user_photos/`

2. **Останавливается на "Saving photo info to database"**
   - Проблема с базой данных
   - Проверить файл bot.db существует

3. **Останавливается на "Starting image generation"**
   - Проблема с ImageProcessor
   - Проверить что шаблоны существуют: `ls images/new_templates/`

4. **Останавливается на "Sending photo to user"**
   - Проблема с отправкой через Telegram API
   - Проверить размер файла: `ls -lh generated_photos/`

### Шаг 4: Проверить state пользователя

Возможная проблема - пользователь не в состоянии `waiting_for_photo`.

Добавить проверку в начало `handle_photo_upload`:

```python
logger.info(f"Current state: {await state.get_state()}")
```

Должно быть: `QuizStates:waiting_for_photo`

## Возможные причины проблемы

### 1. Обработчик не вызывается
- Проверить state пользователя
- Проверить что пользователь отправляет именно фото (не файл)

### 2. Ошибка при скачивании фото
- Проблема с правами доступа к директории `user_photos/`
- Проблема с Telegram Bot API токеном

### 3. Ошибка при обнаружении лица
- OpenCV не установлен или поврежден
- Фото не читается (повреждено)

### 4. Ошибка при генерации изображения
- Нет шаблонов в `images/new_templates/`
- Проблема с ImageProcessor

### 5. Ошибка при отправке результата
- Файл слишком большой (>10MB для фото)
- Проблема с Telegram API

## Быстрая проверка компонентов

```bash
# Проверка OpenCV
python -c "import cv2; print('OpenCV OK:', cv2.__version__)"

# Проверка директорий
ls -la user_photos/ generated_photos/ images/new_templates/

# Проверка базы данных
python -c "from database.engine import init_db; import asyncio; asyncio.run(init_db()); print('DB OK')"

# Проверка ImageProcessor
python test_photo_handler.py
```

## Что делать после обнаружения проблемы

1. **Если проблема в коде** - исправить и перезапустить бота
2. **Если проблема в данных** - проверить .env файл, шаблоны, etc.
3. **Если проблема в API** - проверить токен бота, интернет-соединение

## Полезные команды

```bash
# Смотреть логи в реальном времени (если сохраняются в файл)
tail -f logs/bot.log

# Очистить БД для теста
rm bot.db
python -c "from database.engine import init_db; import asyncio; asyncio.run(init_db())"

# Проверить размер сгенерированных фото
du -sh generated_photos/*

# Проверить есть ли сохраненные фото пользователей
ls -lh user_photos/
```
