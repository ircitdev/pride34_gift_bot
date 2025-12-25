# Инструкция по установке и запуску Pride34 Gift Bot

## Требования

- Python 3.10 или выше
- pip (менеджер пакетов Python)
- Git (опционально)

## Шаги установки

### 1. Клонирование репозитория (или распаковка архива)

```bash
cd /path/to/your/directory
```

### 2. Создание виртуального окружения

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка конфигурации

Файл `.env` уже создан с вашим токеном бота. Проверьте и при необходимости измените настройки:

```bash
# Откройте .env в текстовом редакторе
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Важные параметры:**

- `BOT_TOKEN` - токен вашего бота (уже установлен)
- `ADMIN_IDS` - ID администраторов через запятую (например: 123456789,987654321)
- `QUIZ_END_DATE` - дата окончания розыгрыша (формат: YYYY-MM-DD)
- `WINNERS_COUNT` - количество победителей в розыгрыше

### 5. Подготовка изображений

**ОБЯЗАТЕЛЬНО:** Добавьте следующие изображения:

1. **logo.png** - поместите в корень проекта (рядом с main.py)
   - Это логотип PRIDE34, который будет накладываться на все сгенерированные фото

2. **welcome.jpg** - поместите в папку `images/`
   - Приветственное изображение для команды /start

```bash
# Windows
mkdir images
# Поместите файл welcome.jpg в папку images/

# Linux/Mac
mkdir -p images
# Поместите файл welcome.jpg в папку images/
```

**Структура файлов:**
```
pride34_gift_bot/
├── logo.png              ← ОБЯЗАТЕЛЬНО
├── main.py
└── images/
    └── welcome.jpg       ← ОБЯЗАТЕЛЬНО
```

**Опционально:** Создайте шаблоны фигурок для мужчин и женщин:
- `images/templates/figure_male.png`
- `images/templates/figure_female.png`

Если шаблоны не предоставлены, бот будет использовать базовый генератор с наложением logo.png.

### 6. Запуск бота

```bash
python main.py
```

Бот запустится и начнёт обрабатывать сообщения.

## Проверка работы

1. Найдите вашего бота в Telegram: `@PRIDE34_GIFT_BOT`
2. Отправьте команду `/start`
3. Пройдите квиз
4. Загрузите фото
5. Получите персонализированное изображение

## Админ-панель

Для доступа к админ-панели:

1. Добавьте свой Telegram ID в параметр `ADMIN_IDS` в файле `.env`
2. Перезапустите бота
3. Отправьте команду `/admin`

**Доступные функции:**
- **Статистика** - просмотр количества участников
- **Розыгрыш** - провести розыгрыш и выбрать победителей
- **Победители** - список победителей
- **Экспорт данных** - скачать CSV файл с данными участников

## Узнать свой Telegram ID

Отправьте сообщение боту [@userinfobot](https://t.me/userinfobot) в Telegram.

## Остановка бота

Нажмите `Ctrl+C` в терминале, где запущен бот.

## Автозапуск (опционально)

### Windows (создать bat-файл)

Создайте файл `start_bot.bat`:

```batch
@echo off
cd /d %~dp0
call venv\Scripts\activate
python main.py
pause
```

### Linux (systemd service)

Создайте файл `/etc/systemd/system/pride34bot.service`:

```ini
[Unit]
Description=Pride34 Gift Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/pride34_gift_bot
Environment="PATH=/path/to/pride34_gift_bot/venv/bin"
ExecStart=/path/to/pride34_gift_bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pride34bot
sudo systemctl start pride34bot
sudo systemctl status pride34bot
```

## Troubleshooting

### Ошибка "ModuleNotFoundError"
Убедитесь, что виртуальное окружение активировано и все зависимости установлены:
```bash
pip install -r requirements.txt
```

### Ошибка "Unauthorized"
Проверьте правильность токена бота в файле `.env`.

### Бот не отвечает
- Проверьте, что бот запущен
- Проверьте интернет-соединение
- Убедитесь, что токен действителен

### Ошибки при обработке фото
Убедитесь, что установлен OpenCV:
```bash
pip install opencv-python
```

## Логи

Логи выводятся в консоль. Для сохранения в файл измените `main.py`:

```python
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

## Поддержка

При возникновении проблем создайте issue в репозитории проекта или свяжитесь с разработчиком.
