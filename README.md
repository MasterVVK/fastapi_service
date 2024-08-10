# Сервис синхронизации GitHub репозитория

Этот проект представляет собой сервис FastAPI для синхронизации локальной директории с репозиторием GitHub при получении событий webhook. Он предоставляет конечную точку для получения структуры директории и webhook для запуска синхронизации.

## Оглавление

- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
- [Конечные точки](#конечные-точки)
- [Логирование](#логирование)
- [Лицензия](#лицензия)

## Установка

1. **Клонируйте репозиторий**:

    ```sh
    git clone <repository_url>
    cd <repository_name>
    ```

2. **Создайте виртуальное окружение и активируйте его**:

    ```sh
    python -m venv venv
    source venv/bin/activate  # Для Windows используйте `venv\Scripts\activate`
    ```

3. **Установите зависимости**:

    ```sh
    pip install -r requirements.txt
    ```

4. **Настройте Nginx** (пример конфигурации):
    ```nginx
    server {
        listen 80;
        server_name <your_server_domain>;

        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name <your_server_domain>;

        ssl_certificate /etc/letsencrypt/live/<your_server_domain>/fullchain.pem; # управляется Certbot
        ssl_certificate_key /etc/letsencrypt/live/<your_server_domain>/privkey.pem; # управляется Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # управляется Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # управляется Certbot

        add_header Strict-Transport-Security "max-age=31536000" always;
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";

        location / {
            include proxy_params;
            proxy_pass http://unix:/srv/fastapi_service/fastapi_service.sock;
        }
    }
    ```

5. **Настройте и запустите FastAPI сервис**:

    Создайте systemd сервисный файл `/etc/systemd/system/fastapi_service.service`:

    ```ini
    [Unit]
    Description=FastAPI Service
    After=network.target

    [Service]
    User=www-data
    Group=www-data
    WorkingDirectory=/srv/fastapi_service
    ExecStart=/srv/fastapi_service/venv/bin/uvicorn main:app --uds /srv/fastapi_service/fastapi_service.sock

    [Install]
    WantedBy=multi-user.target
    ```

    Затем включите и запустите сервис:

    ```sh
    sudo systemctl enable fastapi_service
    sudo systemctl start fastapi_service
    ```

## Конфигурация

Создайте файл `config.json` в корневой директории проекта:

```json
{
  "root_directory": "/srv/fastapi_service/repository",
  "exclusions": [
    "node_modules",
    ".git",
    "venv",
    "__pycache__"
  ],
  "github_webhook_secret": "your_secret_key",
  "repo_url": "https://github.com/yourusername/yourrepository.git",
  "branch": "main"
}

```
## Описание файлов

### main.py

`main.py` - основной файл приложения FastAPI, который обрабатывает запросы API и события Webhook от GitHub. Основные функции включают:

- Чтение конфигурации из `config.json`
- Предоставление конечной точки для получения структуры директории (`/api/get_structure`)
- Обработка событий Webhook (`/api/webhook`) и запуск скрипта синхронизации

### sync_repo.sh

`sync_repo.sh` - скрипт для синхронизации локальной директории с удалённым репозиторием GitHub. Основные функции включают:

- Чтение конфигурации из `config.json`
- Клонирование репозитория, если локальная директория не существует
- Сброс локальных изменений и обновление локального репозитория, если директория существует

## Использование

1. **Запустите FastAPI сервер**:

    ```sh
    sudo systemctl start fastapi_service
    ```

2. **Настройте GitHub Webhook**:

    - Перейдите в настройки вашего репозитория на GitHub.
    - Перейдите в раздел **Webhooks** и нажмите **Add webhook**.
    - Установите **Payload URL** на `https://<your_server_domain>/api/webhook`.
    - Выберите `application/json` для **Content type**.
    - Установите **Secret** на ваш `github_webhook_secret`.
    - Выберите **Just the push event**.
    - Нажмите **Add webhook**.
## Конечные точки

- **GET /api/get_structure**

    Возвращает структуру указанной корневой директории, исключая указанные директории и файлы.

    **Пример**:

    ```sh
    curl http://localhost/api/get_structure
    ```

- **POST /api/webhook**

    Конечная точка для получения событий Webhook от GitHub и запуска синхронизации.

    **Пример**:

    ```sh
    curl -X POST -H "Content-Type: application/json" -H "X-Hub-Signature-256: sha256=<your_signature>" -d '{"ref":"refs/heads/main"}' http://localhost/api/webhook
    ```

## Логирование

Логи выполнения скрипта синхронизации хранятся в файле `sync_repo.log` в корневой директории проекта.

## Лицензия

Этот проект лицензирован по лицензии MIT. Смотрите файл [LICENSE](LICENSE) для подробностей.
