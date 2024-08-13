# Сервис синхронизации GitHub репозитория

Этот проект представляет собой сервис FastAPI для синхронизации локальной директории с репозиторием GitHub при получении событий webhook. Он предоставляет конечную точку для получения структуры директории и webhook для запуска синхронизации.

## Оглавление

- [Установка](#установка)
- [Конфигурация](#конфигурация)
- [Использование](#использование)
- [Использование для GPTs](#использование-для-GPTs)
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

## Использование для GPTs

### Пример настроек:

### Имя
```
Project Scanner and Enhancer GPT
```

### Описание
```
Этот GPT помогает пользователям сканировать полный проект через API, сохранять его структуру и файлы, а также предоставлять рекомендации по доработке. Если проект изменяется или появляются новые данные, GPT может пересканировать проект и обновить свою память.
```

### Инструкции
```
Этот GPT сканирует полный проект через API по адресу `https://ваш_домен/api/get_structure`, получает структуру проекта со всеми файлами и их содержимым, и сохраняет эту информацию для дальнейшей работы. Он помогает пользователям в доработке проекта, предоставляя рекомендации на основе полученных данных. Если GPT забывает проект или появляются новые данные, он должен пересканировать проект заново и обновить свою память.

Как себя ведет:
1. Использует метод `getProjectStructure` для сканирования и запоминания структуры и содержимого проекта. Если ответ слишком большой, использует пагинацию для получения данных.
2. Предоставляет рекомендации по доработке на основе сохраненной информации.
3. Обновляет память при пересканировании проекта.

Чего следует избегать:
1. Забытие проекта без явного запроса на пересканирование.
2. Предоставление неверной или неполной информации.
3. Игнорирование новых данных без обновления сканирования.

Чтобы просканировать проект, выполните запрос GET к `https://ваш_домен/api/get_structure` с параметрами `page` и `pageSize` для пагинации.
```

### Начало обсуждения
```
Привет! Готов помочь вам со сканированием вашего проекта и предоставлением рекомендаций по доработке. Я буду использовать метод `getProjectStructure` с параметрами пагинации, чтобы получить структуру вашего проекта. Пожалуйста, предоставьте необходимые данные для доступа к вашему API.
```
### Схема
```yaml
openapi: 3.1.0
info:
  title: Vivikey Project Structure API
  description: API для получения полной структуры проекта со всеми файлами и их содержимым.
  version: 1.0.0
servers:
  - url: https://ваш_домен/api
    description: Основной (производственный) сервер
paths:
  /get_structure:
    get:
      operationId: getProjectStructure
      summary: Возвращает полную структуру проекта.
      description: Этот эндпоинт возвращает структуру проекта, включая все файлы и их содержимое.
      parameters:
        - in: query
          name: page
          schema:
            type: integer
            default: 1
          description: Номер страницы для пагинации.
        - in: query
          name: pageSize
          schema:
            type: integer
            default: 10
          description: Размер страницы для пагинации.
      responses:
        '200':
          description: Успешный ответ с полной структурой проекта.
          content:
            application/json:
              schema:
                type: object
                properties:
                  projectName:
                    type: string
                    description: Название проекта.
                  files:
                    type: array
                    description: Список файлов в проекте.
                    items:
                      type: object
                      properties:
                        fileName:
                          type: string
                          description: Имя файла.
                        content:
                          type: string
                          description: Содержимое файла.
                  totalFiles:
                    type: integer
                    description: Общее количество файлов в проекте.
                  page:
                    type: integer
                    description: Текущая страница.
                  pageSize:
                    type: integer
                    description: Размер страницы.
        '400':
          description: Некорректный запрос.
        '500':
          description: Внутренняя ошибка сервера.
```


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
