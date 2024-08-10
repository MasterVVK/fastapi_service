#!/bin/bash

LOG_FILE="sync_repo.log"

# Чтение конфигурации из config.json
CONFIG_PATH="$(dirname "$0")/config.json"

# Использование команд Bash для извлечения значений из JSON
ROOT_DIRECTORY=$(grep -oP '(?<="root_directory": ")[^"]*' "$CONFIG_PATH")
REPO_URL=$(grep -oP '(?<="repo_url": ")[^"]*' "$CONFIG_PATH")
BRANCH=$(grep -oP '(?<="branch": ")[^"]*' "$CONFIG_PATH")

echo "Starting sync_repo.sh script" >> "$LOG_FILE"

# Переходим в родительскую директорию проекта
cd "$(dirname "$ROOT_DIRECTORY")" || exit

# Проверка наличия директории проекта
if [ ! -d "$(basename "$ROOT_DIRECTORY")" ]; then
    # Клонирование репозитория, если директория не существует
    echo "Cloning repository" >> "$LOG_FILE"
    git clone -b "$BRANCH" "$REPO_URL" "$(basename "$ROOT_DIRECTORY")" >> "$LOG_FILE" 2>&1
else
    # Переходим в директорию проекта
    cd "$ROOT_DIRECTORY" || exit
    # Сброс локальных изменений
    echo "Resetting local changes" >> "$LOG_FILE"
    git reset --hard >> "$LOG_FILE" 2>&1
    # Обновление локального репозитория
    echo "Pulling latest changes" >> "$LOG_FILE"
    git pull origin "$BRANCH" >> "$LOG_FILE" 2>&1
fi

echo "sync_repo.sh script completed" >> "$LOG_FILE"
