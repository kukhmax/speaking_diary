from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
import asyncio
import httpx
from dotenv import load_dotenv

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import init_db, DEFAULT_DB_PATH, add_entry, list_entries

# Load environment variables
load_dotenv()

APP_TITLE = "AI Voice Diary"
DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"
HF_MODEL_URL = os.getenv("HF_MODEL_URL", "https://api-inference.huggingface.co/models/openai/whisper-base")

app = FastAPI(title=f"{APP_TITLE} API")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")


def get_db_path() -> Path:
    url = os.getenv("DATABASE_URL")
    return Path(url) if url else DEFAULT_DB_PATH


def get_hf_token() -> str | None:
    return (
        os.getenv("HF_API_TOKEN")
        or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        or os.getenv("HUGGINGFACE_API_TOKEN")
    )


async def transcribe_with_hf(audio_path: Path) -> str:
    """Transcribe audio using Hugging Face Inference API (Whisper)."""
    token = get_hf_token()
    if not token:
        # Fallback to dummy text when no token is configured
        return f"[распознанный текст для {audio_path.name}]"

    headers = {"Authorization": f"Bearer {token}"}
    # Best-effort content-type based on file extension
    ext = audio_path.suffix.lower()
    if ext == ".webm":
        headers["Content-Type"] = "audio/webm"
    elif ext in (".wav", ".wave"):
        headers["Content-Type"] = "audio/wav"
    elif ext == ".mp3":
        headers["Content-Type"] = "audio/mpeg"
    else:
        headers["Content-Type"] = "application/octet-stream"

    data_bytes = audio_path.read_bytes()

    # Retry on model loading (503)
    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        for attempt in range(3):
            resp = await client.post(HF_MODEL_URL, data=data_bytes, headers=headers)
            if resp.status_code == 200:
                payload = resp.json()
                if isinstance(payload, dict):
                    return payload.get("text") or ""
                if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                    return payload[0].get("text") or ""
                return str(payload)
            if resp.status_code == 503:
                # Model is loading, wait and retry
                await asyncio.sleep(4)
                continue
            # Propagate other errors
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

    raise HTTPException(status_code=503, detail="ASR модель загружается, попробуйте позже")


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
async def api_transcribe(audio: UploadFile = File(...)):
    # Save uploaded file
    filename = audio.filename or f"audio_{int(datetime.utcnow().timestamp())}.webm"
    save_path = UPLOADS_DIR / filename
    data = await audio.read()
    with save_path.open("wb") as f:
        f.write(data)

    # Real transcription via HF (falls back to dummy if token missing)
    text = await transcribe_with_hf(save_path)
    return {"text": text}