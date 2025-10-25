from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import init_db, DEFAULT_DB_PATH, add_entry, list_entries

APP_TITLE = "AI Voice Diary"
DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"

app = FastAPI(title=f"{APP_TITLE} API")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")


def get_db_path() -> Path:
    url = os.getenv("DATABASE_URL")
    return Path(url) if url else DEFAULT_DB_PATH


@app.on_event("startup")
def startup() -> None:
    init_db(get_db_path())
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_title": APP_TITLE})


@app.get("/api/entries")
def api_list_entries(limit: int = 100):
    rows = list_entries(get_db_path(), limit=limit)
    return {"items": rows}


@app.post("/api/entries")
def api_add_entry(payload: dict):
    text = (payload or {}).get("text")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Field 'text' is required")
    created_at = datetime.utcnow().replace(microsecond=0).isoformat()
    entry_id = add_entry(get_db_path(), created_at, text)
    return {"id": entry_id, "created_at": created_at, "text": text}


@app.post("/api/transcribe")
def api_transcribe(audio: UploadFile = File(...)):
    # Dummy transcription: save file and return synthetic text
    filename = audio.filename or f"audio_{int(datetime.utcnow().timestamp())}.webm"
    save_path = UPLOADS_DIR / filename
    with save_path.open("wb") as f:
        f.write(audio.file.read())
    text = f"[распознанный текст для {filename}]"
    return {"text": text}