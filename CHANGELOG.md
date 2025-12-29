# Changelog

Все изменения проекта Pride34 Gift Bot.

## [2.0.0] - 2025-12-28

### Добавлено

#### Редактор текстов бота
- Админ-панель для редактирования всех текстов бота через Telegram
- 6 категорий текстов: приветствие, вопросы квиза, выбор пола, запрос фото, предсказания, кнопки
- Показ текущего текста перед редактированием
- Навигация с кнопкой "Назад" на всех уровнях
- Хранение текстов в JSON-файле ([bot/texts.json](bot/texts.json))
- TextManager для централизованного управления текстами
- Документация: [TEXT_EDITOR_GUIDE.md](TEXT_EDITOR_GUIDE.md)

#### Система случайных шаблонов
- Случайный выбор шаблонов из папки `images/new_templates/`
- Отдельные шаблоны для мужчин и женщин
- 8 профессиональных 3D-шаблонов (4 мужских + 4 женских)
- Fallback на старые шаблоны при отсутствии новых
- Логирование выбора шаблонов
- Тест случайного выбора ([test_random_templates.py](test_random_templates.py))
- Документация: [RANDOM_TEMPLATES_GUIDE.md](RANDOM_TEMPLATES_GUIDE.md)

#### Улучшения генерации изображений
- Исправлены пропорции головы (круглая вместо вытянутой)
- Оптимизация размера и положения головы на фигурке
- Улучшено наложение лица с color matching
- Качество на уровне конкурентов

### Изменено

#### Интерфейс
- Текст приветствия обновлен на новогодний фитнес-квиз
- Индикатор прогресса: звездочки ⭐️ и кружочки ⚪️ вместо квадратов
- Кнопка старта квиза: "Я готов!" вместо "Начать квиз /start"

#### Архитектура
- Все тексты вынесены в [bot/texts.json](bot/texts.json)
- Динамическая загрузка вопросов квиза через `get_quiz_questions()`
- Централизованное управление текстами через TextManager

### Технические детали

#### Новые файлы
- `bot/texts.json` - JSON-хранилище всех текстов
- `bot/texts.py` - TextManager класс
- `handlers/text_editor.py` - обработчики редактора текстов (393 строки)
- `test_random_templates.py` - тест случайных шаблонов
- `TEXT_EDITOR_GUIDE.md` - руководство по редактору
- `RANDOM_TEMPLATES_GUIDE.md` - руководство по шаблонам

#### Измененные файлы
- `services/template_generator.py` - добавлен `_get_random_template()`
- `handlers/start.py` - использует TextManager
- `handlers/quiz.py` - динамическая загрузка вопросов, новый индикатор
- `bot/keyboards.py` - кнопка "Редактировать тексты", новые клавиатуры
- `bot/states.py` - добавлены состояния text_edit
- `bot/quiz_data.py` - функция `get_quiz_questions()`
- `main.py` - регистрация text_editor router

#### Шаблоны
- `images/new_templates/figure_male1.png` (1.1 MB)
- `images/new_templates/figure_male2.png` (895 KB)
- `images/new_templates/figure_male3.png` (1.2 MB)
- `images/new_templates/figure_male4.png` (1.2 MB)
- `images/new_templates/figure_female1.png` (978 KB)
- `images/new_templates/figure_female2.png` (884 KB)
- `images/new_templates/figure_female3.png` (1.2 MB)
- `images/new_templates/figure_female4.png` (1.4 MB)

### Деплой
- ✅ Развернуто на сервере 31.44.7.144
- ✅ Systemd сервис настроен
- ✅ Все файлы синхронизированы (проверено MD5)
- ✅ Бот работает стабильно

---

## [1.0.0] - 2025-12-20

### Начальная версия

- Квиз из 5 вопросов
- Сбор фото пользователей
- Генерация персонализированных изображений (DALL-E 3 + шаблоны)
- Админ-панель с розыгрышем
- База данных SQLite
- Экспорт данных в CSV
- Система рассылок
- Форум для общения с пользователями
