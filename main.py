from fastapi import FastAPI, Request, Query
import os
import aiofiles
import base64
import json
import subprocess
import hmac
import hashlib
import logging

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Чтение конфигурации из config.json из корня проекта
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
root_directory = config["root_directory"]
exclusions = config["exclusions"]
github_webhook_secret = config["github_webhook_secret"]
branch = config["branch"]


async def get_directory_structure(rootdir, exclusions):
    """
    Creates a nested dictionary that represents the folder structure of rootdir,
    excluding specified directories and files.
    """
    dir_structure = []
    for dirpath, dirnames, filenames in os.walk(rootdir):
        folder = os.path.relpath(dirpath, rootdir)
        # Пропуск директорий, которые находятся в списке исключений
        if any(excl in folder for excl in exclusions):
            continue
        subdir = {'folder': folder, 'files': []}
        for filename in filenames:
            # Пропуск файлов, которые находятся в списке исключений
            if any(excl in filename for excl in exclusions):
                continue
            file_path = os.path.join(dirpath, filename)
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
            except UnicodeDecodeError:
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
                    content = base64.b64encode(content).decode('utf-8')
            subdir['files'].append({'fileName': filename, 'content': content})
        dir_structure.append(subdir)
    return dir_structure


@app.get("/api/get_structure")
async def get_structure(page: int = Query(1, alias='page'),
                        byte_size: int = Query(204800, alias='byteSize')):  # 200 KB by default
    directory_structure = await get_directory_structure(root_directory, exclusions)

    files = []
    total_size = 0
    current_size = 0
    start_index = (page - 1) * byte_size

    # Подсчет общего размера всех файлов
    total_files_size = sum(
        len(file['content'].encode('utf-8')) for folder in directory_structure for file in folder['files'])

    # Общее количество страниц
    total_pages = (total_files_size + byte_size - 1) // byte_size  # округление вверх

    # Сбор файлов для текущей страницы
    for folder in directory_structure:
        for file in folder['files']:
            file_size = len(file['content'].encode('utf-8'))
            if total_size + file_size <= start_index:
                total_size += file_size
                continue
            if current_size + file_size > byte_size:
                break
            files.append(file)
            current_size += file_size
            total_size += file_size

    return {
        'projectName': os.path.basename(root_directory),
        'files': files,
        'page': page,
        'byteSize': byte_size,
        'totalPages': total_pages,
        'totalFilesSize': total_files_size
    }


@app.get("/api/get_structure/metadata")
async def get_structure_metadata():
    """
    Возвращает метаданные о структуре проекта, включая общее количество файлов и папок,
    а также общий размер данных в байтах.
    """
    directory_structure = await get_directory_structure(root_directory, exclusions)

    total_files = 0
    total_size = 0

    for folder in directory_structure:
        for file in folder['files']:
            total_files += 1
            total_size += len(file['content'].encode('utf-8'))  # Размер в байтах

    return {
        'projectName': os.path.basename(root_directory),
        'totalFiles': total_files,
        'totalSizeInBytes': total_size
    }


@app.post("/api/webhook")
async def github_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get('X-Hub-Signature-256')
    secret = github_webhook_secret.encode()
    computed_signature = 'sha256=' + hmac.new(secret, payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, computed_signature):
        logging.warning("Unauthorized request")
        return {"status": "unauthorized"}

    # Обработка Webhook события push
    event = request.headers.get('X-GitHub-Event')
    logging.info(f"Received event: {event}")

    if event == "push" and json.loads(payload).get('ref') == f'refs/heads/{branch}':
        logging.info(f"Running sync_repo.sh script for branch {branch}")
        try:
            result = subprocess.run(["/usr/bin/sh", "sync_repo.sh"], capture_output=True, text=True)
            logging.info(f"Script output: {result.stdout}")
            logging.error(f"Script error: {result.stderr}")
            if result.returncode != 0:
                logging.error(f"sync_repo.sh script failed with return code {result.returncode}")
        except Exception as e:
            logging.error(f"Failed to run script: {e}")

    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
