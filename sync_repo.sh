#!/bin/bash

# Чтение конфигурации из config.json
CONFIG_PATH="$(dirname "$0")/config.json"
ROOT_DIRECTORY=$(jq -r '.root_directory' "$CONFIG_PATH")
REPO_URL=$(jq -r '.repo_url' "$CONFIG_PATH")

# Переходим в родительскую директорию проекта
cd "$(dirname "$ROOT_DIRECTORY")" || exit

# Проверка наличия директории проекта
if [ ! -d "$(basename "$ROOT_DIRECTORY")" ]; then
    # Клонирование репозитория, если директория не существует
    git clone "$REPO_URL" "$(basename "$ROOT_DIRECTORY")"
fi

# Переходим в директорию проекта
cd "$ROOT_DIRECTORY" || exit

# Сброс локальных изменений
git reset --hard

# Обновление локального репозитория
git pull origin main
