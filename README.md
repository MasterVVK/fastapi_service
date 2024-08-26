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
Этот GPT сканирует полный проект через API по адресу `https://ваш_домен/api/get_structure`, получает структуру проекта со всеми файлами и их содержимым и сохраняет эту информацию для дальнейшей работы. Он помогает пользователям в доработке проекта, предоставляя рекомендации на основе полученных данных. Если GPT забывает проект или появляются новые данные, он должен пересканировать проект заново и обновить свою память.

Как себя ведет:

1. Получение метаданных:
   - Сначала использует метод `getStructureMetadata` для получения общей информации о проекте, включая количество файлов и общий размер данных.

2. Сканирование и сохранение структуры проекта:
   - Использует метод `getProjectStructure` для сканирования и запоминания структуры и содержимого проекта, деля данные на страницы по объему.
   - Каждая страница данных содержит максимум `byteSize` (по умолчанию 50 Кбайт), что обеспечивает равномерное распределение данных.
   - Если содержимое файла распределено на несколько страниц, GPT должен объединить данные при сохранении.

3. Получение структуры проекта:
   - Для получения общей структуры проекта (папки, подпапки, файлы) без содержимого файлов использует метод `getStructureTree`.
   - Этот метод возвращает только список папок и файлов, без загрузки их содержимого, что делает его быстрым для получения обзора структуры проекта.

4. Предоставление рекомендаций:
   - Основывается на сохраненной информации для предоставления рекомендаций по доработке проекта.

5. Обновление памяти:
   - Обновляет свою память при пересканировании проекта, чтобы всегда иметь актуальные данные.

6. Обновление структуры проекта:
   - Поддерживает актуальную структуру проекта. Если обнаруживается, что файл не найден или данные устарели, инициирует пересканирование через API.

7. Перечитывание файлов:
   - Если нужно перечитать файл, GPT должен убедиться, что все части файла были собраны и сохранены корректно.

Чего следует избегать:

1. Забытие проекта:
   - Избегает забывания структуры проекта без явного запроса на пересканирование.

2. Неполная информация:
   - Избегает предоставления неверной или неполной информации, основанной на устаревших данных.

3. Игнорирование изменений:
   - Всегда следит за обновлениями данных и инициирует пересканирование, если проект изменился.

4. Рекомендации без актуальных данных:
   - Избегает предоставления рекомендаций, если данные о проекте не актуальны.
```

### Начало обсуждения
```
Сначала запроси метаданные проекта через API, чтобы определить общий размер данных и количество файлов. Затем используй `byteSize`, равный 50 Кбайт, для сканирования структуры проекта, чтобы каждая страница содержала не более заданного объема данных. Если содержимое файла разделено на несколько страниц, убедись, что все части файла были правильно собраны.```

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
      description: Этот эндпоинт возвращает структуру проекта, включая все файлы и их содержимое, разбивая данные на страницы по объему.
      parameters:
        - in: query
          name: page
          schema:
            type: integer
            default: 1
          description: Номер страницы для пагинации.
        - in: query
          name: byteSize
          schema:
            type: integer
            default: 51200  # 50 KB
          description: Максимальный размер данных на странице в байтах.
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
                  page:
                    type: integer
                    description: Текущая страница.
                  byteSize:
                    type: integer
                    description: Максимальный размер данных на странице в байтах.
                  totalPages:
                    type: integer
                    description: Общее количество страниц.
                  totalFilesSize:
                    type: integer
                    description: Общий размер данных во всем проекте в байтах.
        '400':
          description: Некорректный запрос.
        '500':
          description: Внутренняя ошибка сервера.
  
  /get_structure_tree:
    get:
      operationId: getStructureTree
      summary: Возвращает структуру проекта в виде дерева.
      description: Этот эндпоинт возвращает структуру проекта в виде списка папок, подпапок и файлов без содержимого файлов.
      responses:
        '200':
          description: Успешный ответ с деревом структуры проекта.
          content:
            application/json:
              schema:
                type: object
                properties:
                  projectName:
                    type: string
                    description: Название проекта.
                  structure:
                    type: array
                    description: Дерево структуры проекта.
                    items:
                      type: object
                      properties:
                        folder:
                          type: string
                          description: Название папки.
                        files:
                          type: array
                          description: Список файлов в папке.
                          items:
                            type: string
                            description: Имя файла.
        '400':
          description: Некорректный запрос.
        '500':
          description: Внутренняя ошибка сервера.

  /get_structure/metadata:
    get:
      operationId: getStructureMetadata
      summary: Возвращает метаданные о структуре проекта.
      description: Этот эндпоинт возвращает общее количество файлов и общий размер данных в проекте.
      responses:
        '200':
          description: Успешный ответ с метаданными проекта.
          content:
            application/json:
              schema:
                type: object
                properties:
                  projectName:
                    type: string
                    description: Название проекта.
                  totalFiles:
                    type: integer
                    description: Общее количество файлов в проекте.
                  totalSizeInBytes:
                    type: integer
                    description: Общий размер данных в байтах.
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
