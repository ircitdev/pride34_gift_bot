@echo off
chcp 65001 >nul
REM Скрипт для быстрого деплоя бота на сервер (Windows)

REM НАСТРОЙКИ - замените на свои
set SERVER_USER=root
set SERVER_HOST=31.44.7.144
set SERVER_PATH=/var/www/pride34_gift_bot

echo ========================================
echo Деплой Pride34 Gift Bot на сервер
echo ========================================
echo.

echo 1. Копирование обновленных файлов...
echo.

REM Копируем обновленные файлы
scp handlers\photo.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/handlers/
scp main.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/

REM Копируем новые скрипты
scp view_logs.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp test_photo_handler.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/
scp check_bot_handlers.py %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/

echo.
echo ✓ Файлы скопированы
echo.

echo 2. Перезапуск бота на сервере...
echo.

REM Перезапуск бота через SSH
ssh %SERVER_USER%@%SERVER_HOST% "cd %SERVER_PATH% && pkill -f 'python.*main.py' ; sleep 2 ; screen -dmS pride34_bot python main.py ; sleep 3 ; echo 'Бот перезапущен' ; tail -10 logs/bot.log"

echo.
echo ========================================
echo ✓ Деплой завершен!
echo ========================================
echo.
echo Теперь отправьте фото в бота и проверьте логи:
echo   ssh %SERVER_USER%@%SERVER_HOST% "tail -50 %SERVER_PATH%/logs/bot.log"
echo.
echo Или для просмотра логов в реальном времени:
echo   ssh %SERVER_USER%@%SERVER_HOST% "tail -f %SERVER_PATH%/logs/bot.log"
echo.

pause
