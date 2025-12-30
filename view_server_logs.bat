@echo off
chcp 65001 >nul
REM Просмотр логов бота на сервере

set SERVER_USER=root
set SERVER_HOST=31.44.7.144
set SERVER_PATH=/var/www/pride34_gift_bot

echo ========================================
echo Просмотр логов Pride34 Gift Bot
echo ========================================
echo.

REM Показать последние 100 строк
ssh %SERVER_USER%@%SERVER_HOST% "tail -100 %SERVER_PATH%/logs/bot.log"

echo.
echo ========================================
echo Конец логов
echo ========================================
echo.
echo Для просмотра в реальном времени используйте:
echo   ssh %SERVER_USER%@%SERVER_HOST% "tail -f %SERVER_PATH%/logs/bot.log"
echo.

pause
