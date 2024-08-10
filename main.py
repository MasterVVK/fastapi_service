from fastapi import FastAPI, Request
import os
import subprocess
import hmac
import hashlib
import json
import aiofiles
import base64

app = FastAPI()

# Чтение конфигурации из config.json
with open('/srv/fastapi_app/config.json', 'r') as f:
    config = json.load(f)
root_directory = config["root_directory"]
exclusions = config["exclusions"]
github_webhook_secret = config["github_webhook_secret"]

async def get_directory_structure(rootdir, exclusions):
    """
    Creates a nested dictionary that represents the folder structure of rootdir,
    excluding specified directories and files.
    """
    dir_structure = {}
    for dirpath, dirnames, filenames in os.walk(rootdir):
        folder = os.path.relpath(dirpath, rootdir)
        if any(excl in folder for excl in exclusions):
            continue
        subdir = dir_structure
        if folder != ".":
            for sub in folder.split(os.sep):
                subdir = subdir.setdefault(sub, {})
        for filename in filenames:
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
            subdir[filename] = content
    return dir_structure

@app.get("/api/get_structure")
async def get_structure():
    directory_structure = await get_directory_structure(root_directory, exclusions)
    return directory_structure

@app.post("/api/webhook")
async def github_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get('X-Hub-Signature-256')
    secret = github_webhook_secret.encode()
    computed_signature = 'sha256=' + hmac.new(secret, payload, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, computed_signature):
        return {"status": "unauthorized"}

    # Обработка Webhook события push
    event = request.headers.get('X-GitHub-Event')
    if event == "push" and json.loads(payload).get('ref') == 'refs/heads/main':
        subprocess.run(["/srv/fastapi_app/sync_repo.sh"])

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
