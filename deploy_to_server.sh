#!/bin/bash
# Скрипт для быстрого деплоя бота на сервер

# НАСТРОЙКИ - замените на свои
SERVER_USER="root"
SERVER_HOST="31.44.7.144"
SERVER_PATH="/var/www/pride34_gift_bot"  # Путь на сервере

echo "========================================"
echo "Деплой Pride34 Gift Bot на сервер"
echo "========================================"

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}1. Копирование обновленных файлов...${NC}"

# Копируем только измененные файлы
scp handlers/photo.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/handlers/
scp main.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/

# Копируем новые скрипты
scp view_logs.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/
scp test_photo_handler.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/
scp check_bot_handlers.py ${SERVER_USER}@${SERVER_HOST}:${SERVER_PATH}/

echo -e "${GREEN}✓ Файлы скопированы${NC}"

echo ""
echo -e "${YELLOW}2. Перезапуск бота на сервере...${NC}"

# Перезапуск бота (замените на вашу команду)
ssh ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /var/www/pride34_gift_bot

# Остановить бота (попробуем разные варианты)
if systemctl is-active --quiet pride34_bot; then
    echo "Останавливаем через systemd..."
    sudo systemctl stop pride34_bot
    sleep 2
    sudo systemctl start pride34_bot
    echo "✓ Бот перезапущен через systemd"
else
    # Попробуем найти и убить процесс Python
    echo "Ищем процесс бота..."
    PID=$(pgrep -f "python.*main.py" | head -1)
    if [ ! -z "$PID" ]; then
        echo "Останавливаем процесс $PID..."
        kill $PID
        sleep 2
    fi

    # Запускаем бота в screen
    echo "Запускаем бота в screen..."
    screen -dmS pride34_bot python main.py
    echo "✓ Бот запущен в screen сессии 'pride34_bot'"
fi

# Проверяем что логи создаются
sleep 3
if [ -f logs/bot.log ]; then
    echo ""
    echo "Последние строки лога:"
    tail -5 logs/bot.log
fi
ENDSSH

echo ""
echo -e "${GREEN}========================================"
echo "✓ Деплой завершен!"
echo "========================================${NC}"
echo ""
echo "Для просмотра логов на сервере:"
echo "  ssh ${SERVER_USER}@${SERVER_HOST} 'tail -f ${SERVER_PATH}/logs/bot.log'"
echo ""
echo "Или подключитесь к серверу:"
echo "  ssh ${SERVER_USER}@${SERVER_HOST}"
echo "  cd ${SERVER_PATH}"
echo "  python view_logs.py 100"
echo ""
