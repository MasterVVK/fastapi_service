#!/bin/bash

# Чтение конфигурации из config.json
CONFIG_PATH="$(dirname "$0")/config.json"

# Использование команд Bash для извлечения значений из JSON
ROOT_DIRECTORY=$(grep -oP '(?<="root_directory": ")[^"]*' "$CONFIG_PATH")
REPO_URL=$(grep -oP '(?<="repo_url": ")[^"]*' "$CONFIG_PATH")
BRANCH=$(grep -oP '(?<="branch": ")[^"]*' "$CONFIG_PATH")

# Переходим в родительскую директорию проекта
cd "$(dirname "$ROOT_DIRECTORY")" || exit

# Проверка наличия директории проекта
if [ ! -d "$(basename "$ROOT_DIRECTORY")" ]; then
    # Клонирование репозитория, если директория не существует
    git clone -b "$BRANCH" "$REPO_URL" "$(basename "$ROOT_DIRECTORY")"
else
    # Переходим в директорию проекта
    cd "$ROOT_DIRECTORY" || exit
    # Сброс локальных изменений
    git reset --hard
    # Обновление локального репозитория
    git pull origin "$BRANCH"
fi
