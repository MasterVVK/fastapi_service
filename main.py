from fastapi import FastAPI, Request, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import aiofiles
import base64
import json
import subprocess
import hmac
import hashlib
import logging
from uuid import uuid4

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

# Хранилище для результатов сканирования
scan_results = {}


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


def save_scan_result(task_id, directory_structure):
    """
    Сохранение результата сканирования в глобальное хранилище.
    """
    scan_results[task_id] = directory_structure


async def scan_project_background(task_id):
    """
    Фоновая задача для сканирования проекта.
    """
    directory_structure = await get_directory_structure(root_directory, exclusions)
    save_scan_result(task_id, directory_structure)


@app.get("/api/scan_project")
async def scan_project(background_tasks: BackgroundTasks):
    """
    Запуск сканирования проекта и возврат идентификатора задачи.
    """
    task_id = str(uuid4())
    background_tasks.add_task(scan_project_background, task_id)
    return {"task_id": task_id, "status": "started"}


@app.get("/api/get_scan_result")
async def get_scan_result(task_id: str, page: int = Query(1, alias='page'),
                          page_size: int = Query(10, alias='pageSize')):
    """
    Получение результата сканирования по идентификатору задачи.
    """
    if task_id not in scan_results:
        return JSONResponse(status_code=404, content={"message": "Task ID not found or scan not completed."})

    directory_structure = scan_results[task_id]
    # Пагинация
    start = (page - 1) * page_size
    end = start + page_size
    paginated_structure = directory_structure[start:end]

    return {
        'projectName': os.path.basename(root_directory),
        'files': paginated_structure,
        'totalFiles': len(directory_structure),
        'page': page,
        'pageSize': page_size
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
