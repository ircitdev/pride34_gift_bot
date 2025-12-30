# Обновление системы сертификатов - v2.2.1

**Дата:** 2025-12-29
**Статус:** ✅ Завершено и развернуто

---

## Что изменилось

### Шрифт и стиль
- ✅ **Шрифт:** Roboto Regular 30px (было: Arial 48px)
- ✅ **Цвет:** белый RGB(255,255,255) (было: черный)
- ✅ **Формат даты:** "DD / DDD / YYYY" вместо "DD.MM.YYYY"
  - Пример: `31 / 365 / 2025`

### Координаты на шаблоне 572x1024
- ✅ **Имя:** X=286 (центр), Y=755
- ✅ **Дата:** X=286 (центр), Y=825

### Образец
Все настройки теперь соответствуют образцу из [sertificate_demo.jpg](images/sertificate_demo.jpg)

---

## Технические изменения

### 1. config.py
```python
# Certificate Settings
CERTIFICATE_NAME_X: int = 286      # X координата имени (центр: 572/2)
CERTIFICATE_NAME_Y: int = 755      # Y координата имени
CERTIFICATE_DATE_X: int = 286      # X координата даты (центр: 572/2)
CERTIFICATE_DATE_Y: int = 825      # Y координата даты
CERTIFICATE_FONT_SIZE: int = 30    # Размер шрифта (Roboto Regular 30px)
CERTIFICATE_FONT_COLOR: str = "255,255,255"  # Цвет текста RGB (белый)
```

### 2. services/certificate_generator.py

**Загрузка шрифта:**
```python
font_paths = [
    # Roboto Regular (preferred)
    "C:/Windows/Fonts/Roboto-Regular.ttf",
    "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf",
    "/usr/share/fonts/roboto/Roboto-Regular.ttf",
    # Fallbacks...
]
```

**Формат даты:**
```python
# Format: DD / DDD / YYYY (day / day_of_year / year)
formatted_date = f"{date_obj.strftime('%d')} / {date_obj.strftime('%j')} / {date_obj.strftime('%Y')}"
```

---

## Тестирование

### Локальный тест
```bash
$ python test_certificate.py

[OK] Generator initialized
[TEST] Test parameters:
   User ID: 999999
   User Name: Иван Петров
   Expiry Date: 2025-12-31

[CONFIG] Certificate settings:
   Name position: (286, 755)
   Date position: (286, 825)
   Font size: 30
   Font color: 255,255,255

[SUCCESS] Certificate generated successfully!
   File size: 222.9 KB

[PASSED] Test PASSED!
```

### Пример результата
- **Имя:** "Иван Петров" - белым шрифтом, центрировано
- **Дата:** "31 / 365 / 2025" - белым шрифтом, центрировано
- **Размер:** 222.9 KB

---

## Деплой

### Загруженные файлы
```bash
✅ config.py                      -> /var/www/pride34_gift_bot/
✅ services/certificate_generator.py -> /var/www/pride34_gift_bot/services/
```

### Статус сервера
```
✅ Сервер: root@31.44.7.144
✅ Сервис: pride34-gift-bot.service
✅ Статус: Active (running)
✅ PID: 2210201
✅ Memory: 153.5M
```

### Логи
```
Dec 29 05:35:13 - INFO - Database initialized
Dec 29 05:35:13 - INFO - Bot started
Dec 29 05:35:14 - INFO - Run polling for bot @PRIDE34_GIFT_BOT
```

---

## Сравнение: до и после

### Было (v2.2.0)
- Шрифт: Arial 48px, черный
- Координаты: (400, 350) и (400, 450)
- Формат даты: "31.12.2025"
- Центрирование: базовое

### Стало (v2.2.1)
- Шрифт: Roboto Regular 30px, белый
- Координаты: (286, 755) и (286, 825) - точное центрирование
- Формат даты: "31 / 365 / 2025"
- Центрирование: идеальное на шаблоне 572x1024

---

## Как использовать

### Админ-панель
1. Войти в админ-панель: `/admin`
2. Нажать **"Выдать сертификат"**
3. Выбрать пользователя из списка
4. Подтвердить отправку
5. Сертификат автоматически генерируется и отправляется

### Результат
- Пользователь получает в ЛС красивый сертификат с его именем
- Сертификат также отправляется в топик форума
- Дата действия: до 2025-12-31

---

## Настройка координат (если нужно)

Если требуется скорректировать позицию текста:

1. Отредактировать [config.py](config.py):
```python
CERTIFICATE_NAME_Y: int = 755  # увеличить = ниже, уменьшить = выше
CERTIFICATE_DATE_Y: int = 825  # аналогично
```

2. Перезапустить бот на сервере:
```bash
ssh root@31.44.7.144 "systemctl restart pride34-gift-bot"
```

---

## Размеры шаблона

- **Ширина:** 572 пикселей
- **Высота:** 1024 пикселей
- **Центр по X:** 286 пикселей (572/2)
- **Формат:** JPG

---

## Документация

- [CERTIFICATE_SYSTEM_IMPLEMENTATION.md](CERTIFICATE_SYSTEM_IMPLEMENTATION.md) - полная документация
- [CHANGELOG.md](CHANGELOG.md) - история изменений
- [test_certificate.py](test_certificate.py) - скрипт тестирования

---

## Итог

✅ Система сертификатов полностью настроена
✅ Соответствует образцу sertificate_demo.jpg
✅ Развернута на production сервере
✅ Протестирована и работает

**Версия:** 2.2.1
**Готовность:** 100%
