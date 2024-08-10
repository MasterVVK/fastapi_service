#!/bin/bash

LOG_FILE="sync_repo.log"

# Чтение конфигурации из config.json
CONFIG_PATH="$(dirname "$0")/config.json"

# Проверка существования файла config.json
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Config file not found: $CONFIG_PATH" >> "$LOG_FILE"
    exit 1
fi

# Использование команд Bash для извлечения значений из JSON
ROOT_DIRECTORY=$(grep -oP '(?<="root_directory": ")[^"]*' "$CONFIG_PATH")
REPO_URL=$(grep -oP '(?<="repo_url": ")[^"]*' "$CONFIG_PATH")
BRANCH=$(grep -oP '(?<="branch": ")[^"]*' "$CONFIG_PATH")

echo "Starting sync_repo.sh script at $(date)" >> "$LOG_FILE"
echo "Root directory: $ROOT_DIRECTORY" >> "$LOG_FILE"
echo "Repo URL: $REPO_URL" >> "$LOG_FILE"
echo "Branch: $BRANCH" >> "$LOG_FILE"

# Переходим в родительскую директорию проекта
cd "$(dirname "$ROOT_DIRECTORY")" || { echo "Failed to cd to $(dirname "$ROOT_DIRECTORY")" >> "$LOG_FILE"; exit 1; }

# Проверка наличия директории проекта
if [ ! -d "$(basename "$ROOT_DIRECTORY")" ]; then
    # Клонирование репозитория, если директория не существует
    echo "Cloning repository" >> "$LOG_FILE"
    git clone -b "$BRANCH" "$REPO_URL" "$(basename "$ROOT_DIRECTORY")" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to clone repository" >> "$LOG_FILE"
        exit 1
    fi
else
    # Переходим в директорию проекта
    cd "$ROOT_DIRECTORY" || { echo "Failed to cd to $ROOT_DIRECTORY" >> "$LOG_FILE"; exit 1; }
    # Сброс локальных изменений
    echo "Resetting local changes" >> "$LOG_FILE"
    git reset --hard >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to reset local changes" >> "$LOG_FILE"
        exit 1
    fi
    # Обновление локального репозитория
    echo "Pulling latest changes" >> "$LOG_FILE"
    git pull origin "$BRANCH" >> "$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        echo "Failed to pull latest changes" >> "$LOG_FILE"
        exit 1
    fi
fi

echo "sync_repo.sh script completed at $(date)" >> "$LOG_FILE"
