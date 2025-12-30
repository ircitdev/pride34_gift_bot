# Настройка Nano Banana (Gemini) API для генерации фигурок

## Что изменилось

Бот теперь использует **Nano Banana API** (на базе Google Gemini) вместо шаблонов для генерации новогодних фигурок. Это позволяет:

- ✅ Сохранять лицо пользователя на фигурке
- ✅ Генерировать уникальные 3D-персонажи в стиле Pixar/Disney
- ✅ Использовать Image-to-Image трансформацию

## Требования

1. **Ключ API от Nano Banana**
   - Зарегистрируйтесь на сервисе Nano Banana
   - Получите API ключ для доступа к Gemini 1.5 Flash

2. **URL эндпоинта**
   - Уточните у провайдера правильный URL для генерации изображений
   - По умолчанию: `https://api.nanobanana.com/v1/models/gemini-1.5-flash:generateContent`

## Настройка

### 1. Локально (на вашем компьютере)

Добавьте в файл `.env`:

```env
# Nano Banana (Gemini) API
NANO_BANANA_API_KEY=ваш_ключ_от_nano_banana
NANO_BANANA_URL=https://api.nanobanana.com/v1/models/gemini-1.5-flash:generateContent
```

### 2. На сервере

Подключитесь к серверу и отредактируйте `.env`:

```bash
ssh root@31.44.7.144
cd /var/www/pride34_gift_bot
nano .env
```

Добавьте строки:

```env
NANO_BANANA_API_KEY=ваш_ключ_от_nano_banana
NANO_BANANA_URL=https://api.nanobanana.com/v1/models/gemini-1.5-flash:generateContent
```

Сохраните (Ctrl+O, Enter, Ctrl+X) и перезапустите бота:

```bash
systemctl restart pride34_bot
```

## Как это работает

1. **Пользователь загружает фото** → бот сохраняет в `user_photos/`
2. **Фото кодируется в Base64** → подготовка для API
3. **Промпт + фото отправляются в Gemini** → Image-to-Image трансформация
4. **API возвращает сгенерированную фигурку** → сохраняется в `generated_photos/`
5. **Бот отправляет результат пользователю** → с предсказанием и кнопками шеринга

## Промпт для генерации

Система использует детальный промпт:

- **Сохраняет**: черты лица, прическу пользователя
- **Добавляет**: спортивную одежду PRIDE34, глянцевую текстуру игрушки
- **Фон**: новогодняя елка, боке-эффект, снег
- **Стиль**: 3D-рендер как у Pixar, коллекционная фигурка

## Форматы ответа API

Код поддерживает несколько форматов:

1. **Base64 в JSON**: `{"image": "base64_data..."}`
2. **URL для скачивания**: `{"data": [{"url": "https://..."}]}`
3. **b64_json формат**: `{"data": [{"b64_json": "..."}]}`

Если ваш Nano Banana API использует другой формат - проверьте логи и адаптируйте код в `services/ai_generator.py`.

## Проверка работы

### Просмотр логов в реальном времени:

```bash
ssh root@31.44.7.144 "tail -f /var/www/pride34_gift_bot/logs/bot.log | grep -E 'AI generation|Nano Banana|API'"
```

### Что искать в логах:

```
Starting AI generation for user 123456, gender: female
Generated prompt: Transform the person in this photo...
Sending request to https://api.nanobanana.com/...
API Response received: {...}
AI generation successful for user 123456
```

### Если возникла ошибка:

```
Error in AI generation for user 123456: [описание ошибки]
```

Проверьте:
- ✅ Правильность API ключа
- ✅ Корректность URL эндпоинта
- ✅ Доступность API (не истек ли лимит запросов)

## Откат на шаблоны

Если Nano Banana API недоступен, можно временно вернуться к шаблонам:

В `services/image_processor.py` измените приоритет стратегий (закомментируйте Strategy 3 - AI Generation).

## Стоимость и лимиты

- Уточните у провайдера Nano Banana:
  - Стоимость за запрос
  - Лимиты (запросов в минуту/день)
  - Максимальный размер входящего изображения

## Поддержка

Если возникают проблемы:

1. Проверьте логи: `tail -100 /var/www/pride34_gift_bot/logs/bot.log`
2. Убедитесь что `.env` содержит правильные значения
3. Проверьте доступность API через curl:

```bash
curl -X POST "https://api.nanobanana.com/v1/models/gemini-1.5-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Test"}]}]}'
```
