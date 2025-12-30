# Pride34 Gift Bot - AI Generation System (Final Version)

## Обзор системы

Pride34 Gift Bot использует двухэтапную AI-генерацию для создания персонализированных новогодних открыток:

1. **Gemini 2.0 Flash Exp** - анализирует фото пользователя и создаёт текстовое описание лица
2. **DALL-E 3 HD** - генерирует уникальную 3D-фигурку на основе описания
3. **Overlay System** - накладывает брендированный оверлей с #PRIDE2026 и венком

## Текущая конфигурация

### API Ключи
```env
# .env на сервере
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AI_GENERATION_ENABLED=true
NANO_BANANA_API_KEY=AIzaSyBmora6OvrBMZ_DcLlB5FhnNwT_QBDL26k
```

**Примечание**: Реальные ключи хранятся в `.env` файле на сервере и не коммитятся в репозиторий.

### Модели
- **Gemini**: `gemini-2.0-flash-exp` (v1beta API с биллингом)
- **DALL-E**: `dall-e-3` (HD quality, vivid style)
- **Размер изображения**: 1024x1792 (вертикальный формат)

## Процесс генерации

### Шаг 1: Анализ лица через Gemini

**Файл**: `services/ai_generator.py` → `_ask_gemini()`

**API Endpoint**:
```
https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent
```

**Промпт для Gemini**:
```
Describe this person's key facial features for creating a 3D figurine:
- Hair (color, style, length)
- Glasses (yes/no)
- Facial hair (type if present)
- Distinctive features (eyes, cheekbones, lips, face shape)
Keep it concise but specific.
```

**Пример ответа**:
```
She has long, straight dark brown hair. She has no glasses or facial hair.
Her distinct features include prominent cheekbones and full lips.
```

**Обработка ошибок**:
- Если Gemini возвращает ошибку → генерация прерывается с сообщением пользователю
- **Fallback отключён** - описание от Gemini обязательно для качественного результата

### Шаг 2: Генерация изображения через DALL-E 3

**Файл**: `services/ai_generator.py` → `_generate_with_dalle()`

**API Endpoint**:
```
https://api.openai.com/v1/images/generations
```

**Параметры запроса**:
```json
{
  "model": "dall-e-3",
  "prompt": "[детальный промпт]",
  "size": "1024x1792",
  "quality": "hd",
  "style": "vivid",
  "n": 1
}
```

### Система случайных сюжетов

При каждой генерации **случайно выбирается** один из 4 сюжетов:

#### Вариант 1: Вечерние санки у домика 🌙
```python
{
    "pose": "Sitting on a classic wooden sled with curved metal runners",
    "background": "Evening winter forest with snow-covered trees. Cozy wooden cottage with warm glowing windows in the distance",
    "lighting": "Soft evening twilight with warm golden glow from cottage windows",
    "atmosphere": "Magical evening atmosphere with bokeh lights and gentle snowfall"
}
```

#### Вариант 2: Фитнес-поза в комнате 💪
```python
{
    "pose": "Standing in a confident fitness pose with hands on hips or flexing muscles",
    "background": "Cozy indoor room with decorated Christmas tree, warm fireplace, colorful ornaments and garlands",
    "lighting": "Warm indoor lighting from fireplace and Christmas lights",
    "atmosphere": "Festive home atmosphere with Christmas decorations all around"
}
```

#### Вариант 3: Дневные санки в горах ⛷️
```python
{
    "pose": "Sitting on a classic wooden sled with curved metal runners",
    "background": "Bright sunny winter landscape with snowy mountains and pine forest",
    "lighting": "Bright natural daylight with clear blue sky",
    "atmosphere": "Fresh winter morning with sparkling snow and mountain scenery"
}
```

#### Вариант 4: Бодибилдер у ёлки 🎄
```python
{
    "pose": "Standing in a strong bodybuilder pose showing muscles (flexing biceps or victory pose)",
    "background": "Close-up view with decorated Christmas tree full of colorful ornaments and baubles",
    "lighting": "Bright Christmas lights creating colorful bokeh effect",
    "atmosphere": "Festive mood with vibrant Christmas tree decorations filling the background"
}
```

**Логирование**: В логах видно выбранный вариант:
```
🎲 Selected random scene variation: 1/4
```

### Полный промпт для DALL-E 3

```
IMPORTANT: VERTICAL portrait orientation image (tall, not wide).

A 3D stylized figurine in a magical Christmas scene.

CHARACTER DETAILS (based on photo analysis):
[описание от Gemini]

FIGURINE STYLE:
- Gender: {gender}
- 3D collectible toy style (like premium Christmas ornament figurine)
- Smooth semi-realistic features with stylized proportions
- Outfit: sporty blue and orange striped athletic outfit with PRIDE34 logo on chest
- Friendly, cheerful expression
- NOT photorealistic, NOT real person - it's a TOY FIGURINE

POSE & POSITION:
- [случайный сюжет - поза]

BACKGROUND & SCENE:
- [случайный сюжет - фон]

LIGHTING:
- [случайный сюжет - освещение]

ATMOSPHERE:
- [случайный сюжет - атмосфера]

VERTICAL COMPOSITION:
- VERTICAL portrait format with figurine taking most of frame
- Christmas tree branches with decorations at TOP of vertical frame
- Decorative Christmas wreath with PRIDE34 logo at BOTTOM of vertical frame
- Premium product photography quality

TECHNICAL STYLE:
- VERTICAL portrait orientation (1024x1792)
- High-quality 3D render
- Pixar/Disney toy aesthetic (like collectible Christmas figurines)
- Glossy smooth surfaces
- Depth of field with background blur
- Professional studio quality
- The style should match premium Christmas collectible figurines
```

### Шаг 3: Наложение оверлея

**Файл**: `services/ai_generator.py` → `generate_figurine()`

После получения изображения от DALL-E 3 автоматически накладывается `overlay.png`:

```python
# Накладываем overlay.png поверх результата
overlay_path = Path(__file__).parent.parent / "overlay.png"
if overlay_path.exists():
    overlay = Image.open(overlay_path).convert("RGBA")

    # Конвертируем в RGBA для прозрачности
    if generated_image.mode != 'RGBA':
        generated_image = generated_image.convert('RGBA')

    # Масштабируем overlay под размер изображения
    if overlay.size != generated_image.size:
        overlay = overlay.resize(generated_image.size, Image.Resampling.LANCZOS)

    # Накладываем overlay поверх через alpha composite
    generated_image = Image.alpha_composite(generated_image, overlay)
```

**Оверлей содержит**:
- #PRIDE2026 логотип сверху (золотой текст)
- Новогодний венок с логотипом PRIDE34 снизу

### Финальное сохранение

```python
# Сохраняем результат (конвертируем в RGB для JPEG)
output_path = settings.GENERATED_PHOTOS_DIR / f"{user_id}_christmas.jpg"
if generated_image.mode == 'RGBA':
    generated_image = generated_image.convert('RGB')
generated_image.save(output_path, "JPEG", quality=95)
```

## Пользовательский опыт

### Анимация ожидания

**Файл**: `handlers/photo.py`

Во время генерации (48-60 секунд) пользователь видит:

1. **Сообщение**: "⏳ Колдуем над твоим новогодним образом ✨"
2. **Telegram action**: `upload_photo` обновляется каждые 4 секунды
3. **Визуально**: Анимация загрузки фото в чате

```python
async def send_typing_periodically():
    """Send typing action every 4 seconds to keep animation alive"""
    while True:
        try:
            await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
            await asyncio.sleep(4)
        except:
            break

typing_task = asyncio.create_task(send_typing_periodically())
```

### Timeline генерации

Типичная генерация занимает **55-60 секунд**:

```
17:43:51 - Получено фото, запущена генерация
17:43:51 - Gemini анализирует лицо...
17:43:53 - ✅ Gemini вернул описание (2 сек)
17:43:53 - DALL-E 3 генерирует изображение...
17:44:41 - ✅ DALL-E 3 завершил генерацию (48 сек)
17:44:44 - ✅ Overlay наложен (3 сек)
17:44:45 - ✅ Результат отправлен пользователю
```

## Важные отключения

### Face Swap отключён

**Файл**: `services/image_processor.py`

Ранее система использовала face swap для улучшения лица. **Теперь отключено**:

```python
# AI генерирует готовую фигурку (face swap ОТКЛЮЧЕН)
final_image = await self.ai_generator.generate_figurine(
    user_photo_path, gender, user_id
)
return final_image
```

**Причина**: DALL-E 3 + Gemini создают достаточно качественный результат без дополнительной обработки.

### Шаблоны не используются

**Директория**: `images/new_templates/` (figure_male1-4.png, figure_female1-4.png)

Эти файлы **НЕ используются** в генерации. Они служили только **визуальным референсом** для описания 4 сюжетов в промпте.

DALL-E 3 генерирует изображения **полностью с нуля** на основе текстового промпта.

## Архитектура кода

### Основные файлы

```
services/
├── ai_generator.py          # Gemini + DALL-E 3 + Overlay
├── image_processor.py       # Координация генерации
└── face_swapper.py          # ОТКЛЮЧЕН (не используется)

handlers/
└── photo.py                 # Обработка фото от пользователя

images/
├── overlay.png              # Оверлей с брендингом
└── new_templates/           # Референсы (не используются в коде)
```

### Основной flow

```
handlers/photo.py:process_photo()
    ↓
services/image_processor.py:create_christmas_figure()
    ↓
services/ai_generator.py:generate_figurine()
    ├─→ _ask_gemini()           # Шаг 1: Анализ лица
    ├─→ _create_dalle_prompt()  # Шаг 2: Создание промпта
    ├─→ _generate_with_dalle()  # Шаг 3: Генерация DALL-E 3
    └─→ [overlay application]   # Шаг 4: Наложение оверлея
```

## Логирование

Все этапы логируются для отладки:

```python
logger.info(f"🤖 User {user_id}: Analyzing face with Gemini 2.0 Flash...")
logger.info(f"✅ Gemini description: {description}")
logger.info(f"🎲 Selected random scene variation: {scene_num}/4")
logger.info(f"📝 DALL-E prompt created for user {user_id}")
logger.info(f"🎨 User {user_id}: Generating image with DALL-E 3...")
logger.info(f"✅ Overlay applied for user {user_id}")
logger.info(f"✅ AI generation successful for user {user_id}")
```

## Обработка ошибок

### Gemini API ошибка

```python
if response.status != 200:
    error_text = await response.text()
    logger.error(f"Gemini API error: {error_text}")
    # ОБЯЗАТЕЛЬНО используем Gemini - без fallback
    raise Exception(f"Gemini API failed: {error_text}")
```

**Результат**: Пользователь видит "Произошла ошибка при обработке фото. Попробуйте отправить другое фото."

### DALL-E API ошибка

```python
if response.status != 200:
    error_text = await response.text()
    logger.error(f"DALL-E API error: {error_text}")
    raise Exception(f"DALL-E returned status {response.status}: {error_text}")
```

**Результат**: Аналогичное сообщение об ошибке пользователю.

### Overlay ошибка

```python
try:
    # ... overlay application
    logger.info(f"✅ Overlay applied for user {user_id}")
except Exception as e:
    logger.warning(f"⚠️ Failed to apply overlay: {e}")
    # Продолжаем без оверлея
```

**Результат**: Изображение сохраняется без оверлея, но генерация не прерывается.

## Производительность

### Среднее время генерации
- **Gemini анализ**: 2-3 секунды
- **DALL-E 3 генерация**: 45-55 секунд
- **Overlay наложение**: 2-3 секунды
- **Итого**: ~55-60 секунд

### Оптимизации
1. **Асинхронные запросы** - aiohttp вместо requests
2. **Timeout настройки** - 30 сек для Gemini, 60 сек для DALL-E
3. **Streaming отключен** - получаем готовое изображение
4. **Периодический typing** - улучшает UX во время ожидания

## Стоимость API

### Gemini 2.0 Flash Exp
- **С биллингом**: ~$0.10-0.15 за 1000 запросов
- **Лимиты**: нет (с подключенным биллингом)

### DALL-E 3 HD (1024x1792)
- **Стоимость**: $0.120 за изображение
- **При 100 пользователях**: $12.00
- **При 1000 пользователях**: $120.00

### Рекомендации
- Мониторить использование через OpenAI dashboard
- Установить billing alerts на $50, $100, $150
- Gemini практически бесплатен по сравнению с DALL-E

## Развёртывание

### На сервере (31.44.7.144)

**Расположение**: `/var/www/pride34_gift_bot/`

**Systemd сервис**: `pride34_bot.service`

**Команды**:
```bash
# Перезапуск бота
systemctl restart pride34_bot

# Просмотр логов
tail -f /var/www/pride34_gift_bot/logs/bot.log

# Проверка статуса
systemctl status pride34_bot
```

### Обновление кода

```bash
# Загрузка изменённых файлов
scp services/ai_generator.py root@31.44.7.144:/var/www/pride34_gift_bot/services/
scp handlers/photo.py root@31.44.7.144:/var/www/pride34_gift_bot/handlers/
scp overlay.png root@31.44.7.144:/var/www/pride34_gift_bot/

# Перезапуск
ssh root@31.44.7.144 "systemctl restart pride34_bot"
```

### Бэкапы

```bash
# Создание бэкапа
ssh root@31.44.7.144 "cd /var/www && tar -czf pride34_bot_backup_$(date +%Y%m%d_%H%M%S).tar.gz pride34_gift_bot/"

# Скачивание на локалку
scp root@31.44.7.144:/var/www/pride34_bot_backup_*.tar.gz d:/DevTools/Database/
```

## Тестирование

### Проверка Gemini

```bash
# Поиск в логах
ssh root@31.44.7.144 "grep 'Gemini description' /var/www/pride34_gift_bot/logs/bot.log | tail -5"
```

Ожидаемый результат:
```
✅ Gemini description: She has long, straight dark brown hair...
```

### Проверка DALL-E

```bash
# Поиск в логах
ssh root@31.44.7.144 "grep 'DALL-E' /var/www/pride34_gift_bot/logs/bot.log | tail -10"
```

Ожидаемый результат:
```
🎨 User 123: Generating image with DALL-E 3...
Downloading image from DALL-E: https://oaidalleapiprodscus...
✅ AI generation successful for user 123
```

### Проверка случайного сюжета

```bash
# Поиск в логах
ssh root@31.44.7.144 "grep 'Selected random scene' /var/www/pride34_gift_bot/logs/bot.log | tail -10"
```

Ожидаемый результат:
```
🎲 Selected random scene variation: 1/4
🎲 Selected random scene variation: 3/4
🎲 Selected random scene variation: 2/4
```

## Известные проблемы и решения

### Проблема: DALL-E генерирует горизонтальное изображение

**Решение**: Добавлен явный запрет в начале промпта:
```
IMPORTANT: VERTICAL portrait orientation image (tall, not wide).
```

И повторение в технических требованиях:
```
VERTICAL portrait orientation (1024x1792)
```

### Проблема: Gemini 404 error на v1 API

**Решение**: Использовать v1beta endpoint для gemini-2.0-flash-exp:
```python
self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
```

### Проблема: Overlay не накладывается

**Решение**: Проверить путь к файлу и конвертацию в RGBA:
```python
overlay_path = Path(__file__).parent.parent / "overlay.png"
# Должен указывать на корень проекта
```

## Мониторинг и аналитика

### Метрики для отслеживания

1. **Успешность генераций** - % успешных vs ошибок
2. **Среднее время** - от загрузки фото до результата
3. **Распределение сюжетов** - какие варианты чаще выпадают
4. **Использование API** - количество запросов и стоимость

### SQL запросы для аналитики

```sql
-- Количество успешных генераций
SELECT COUNT(*) FROM user_photos WHERE generated_photo_path IS NOT NULL;

-- Средняя дата генерации
SELECT AVG(created_at) FROM user_photos WHERE generated_photo_path IS NOT NULL;

-- Распределение по полу
SELECT gender, COUNT(*) FROM users GROUP BY gender;
```

## Roadmap и улучшения

### Возможные улучшения

1. **Кэширование Gemini ответов** - для повторных фото одного пользователя
2. **Retry механизм** - автоматический повтор при ошибках API
3. **Предпросмотр** - показать пользователю описание перед генерацией
4. **A/B тестирование промптов** - оптимизация качества результата
5. **Batch генерация** - для админа генерировать несколько открыток сразу

### Не рекомендуется

- ❌ Возвращать face swap (качество DALL-E достаточно)
- ❌ Использовать готовые шаблоны (теряется уникальность)
- ❌ Сокращать промпт (детали важны для качества)

## Контакты и поддержка

- **Разработчик**: @ircitdev
- **Telegram бот**: @PRIDE34_GIFT_BOT
- **Сервер**: 31.44.7.144
- **GitHub**: [репозиторий проекта]

---

**Последнее обновление**: 30 декабря 2024
**Версия**: 3.0.0 (AI Generation with Random Scenes)
