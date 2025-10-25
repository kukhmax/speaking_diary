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
import json
import subprocess
try:
    from imageio_ffmpeg import get_ffmpeg_exe
except Exception:
    get_ffmpeg_exe = None
try:
    from vosk import Model, KaldiRecognizer
except Exception:
    Model = None
    KaldiRecognizer = None

# Load environment variables
load_dotenv()

APP_TITLE = "AI Voice Diary"
DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"
HF_MODEL_URL = os.getenv("HF_MODEL_URL", "https://api-inference.huggingface.co/models/openai/whisper-base")
MAX_AUDIO_SIZE_BYTES = int(os.getenv("MAX_AUDIO_SIZE_BYTES", str(25 * 1024 * 1024)))
ASR_PROVIDER = os.getenv("ASR_PROVIDER", "hf").lower()
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH")
VOSK_MODEL = None

app = FastAPI(title=f"{APP_TITLE} API")
app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
templates = Jinja2Templates(directory="webapp/templates")


def get_db_path() -> Path:
    url = os.getenv("DATABASE_URL")
    if not url:
        return DEFAULT_DB_PATH
    u = url.strip()
    # Support sqlite://, sqlite:/// and file:// URIs, as well as plain paths
    if u.startswith("sqlite:"):
        u = u[len("sqlite:"):]
        # remove leading slashes or backslashes (handles sqlite:/// and windows-style)
        while u.startswith("/") or u.startswith("\\"):
            u = u[1:]
        return Path(u) if u else DEFAULT_DB_PATH
    if u.startswith("file://"):
        u = u[len("file://") :]
        while u.startswith("/") or u.startswith("\\"):
            u = u[1:]
        return Path(u) if u else DEFAULT_DB_PATH
    return Path(u)


def get_hf_token() -> str | None:
    return (
        os.getenv("HF_API_TOKEN")
        or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        or os.getenv("HUGGINGFACE_API_TOKEN")
    )


async def transcribe_with_hf(audio_path: Path, primary_url: str | None = None) -> str:
    """Transcribe audio using Hugging Face Inference API (Whisper).
    Falls back to other Whisper variants on 404, and finally to dummy text if all fail.
    """
    token = get_hf_token()
    if not token:
        # Fallback to dummy text when no token is configured
        return f"[распознанный текст для {audio_path.name}]"

    headers = {"Authorization": f"Bearer {token}", "x-wait-for-model": "true"}
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

    # Candidate model URLs: configured first, then safer fallbacks
    configured = (primary_url or HF_MODEL_URL).strip()
    candidates = [configured]
    # Add fallbacks only if configured isn't already one of them
    for fb in [
        "https://api-inference.huggingface.co/models/openai/whisper-small",
        "https://api-inference.huggingface.co/models/openai/whisper-tiny",
    ]:
        if fb != configured:
            candidates.append(fb)

    async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
        for model_url in candidates:
            # Retry on model loading (503)
            for attempt in range(3):
                resp = await client.post(model_url, data=data_bytes, headers=headers)
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
                if resp.status_code in (401, 403):
                    # Auth issues should be visible to user; surface them
                    detail = resp.text or "Unauthorized"
                    raise HTTPException(status_code=resp.status_code, detail=detail)
                if resp.status_code == 404:
                    # Try next candidate model
                    break
                # Other errors: try next candidate, then fallback
                break
        # If none succeeded, return safe dummy text to keep UI responsive
        return f"[распознанный текст для {audio_path.name}]"

# --- Offline ASR (Vosk) ---

def ensure_wav_16k_mono(src_path: Path) -> Path:
    """Convert audio to 16kHz mono WAV using ffmpeg; if conversion fails, return original path."""
    if get_ffmpeg_exe is None:
        return src_path
    out_path = src_path.with_name(src_path.stem + "_16k_mono.wav")
    ffmpeg = get_ffmpeg_exe()
    cmd = [ffmpeg, "-y", "-i", str(src_path), "-ac", "1", "-ar", "16000", "-f", "wav", str(out_path)]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return out_path
    except Exception:
        return src_path


def get_vosk_model():
    global VOSK_MODEL
    if VOSK_MODEL is None:
        if not VOSK_MODEL_PATH:
            raise HTTPException(status_code=500, detail="VOSK_MODEL_PATH is not configured")
        if Model is None:
            raise HTTPException(status_code=500, detail="Vosk is not installed")
        VOSK_MODEL = Model(VOSK_MODEL_PATH)
    return VOSK_MODEL


async def transcribe_with_vosk(audio_path: Path) -> str:
    wav_path = ensure_wav_16k_mono(audio_path)
    if KaldiRecognizer is None:
        raise HTTPException(status_code=500, detail="Vosk is not installed")
    import wave
    wf = wave.open(str(wav_path), "rb")
    rec = KaldiRecognizer(get_vosk_model(), 16000)
    rec.SetWords(True)
    try:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
        result = rec.FinalResult()
    finally:
        wf.close()
    try:
        payload = json.loads(result)
        return payload.get("text", "")
    except Exception:
        return result


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
    # Basic validation: extension and size
    filename = audio.filename or f"audio_{int(datetime.utcnow().timestamp())}.webm"
    ext = Path(filename).suffix.lower()
    if ext not in (".webm", ".wav", ".wave", ".mp3"):
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {ext}")

    data = await audio.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty audio payload")
    if len(data) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Audio too large")

    # Save uploaded file
    save_path = UPLOADS_DIR / filename
    with save_path.open("wb") as f:
        f.write(data)

    # Real transcription via HF (falls back to dummy on persistent errors)
    # Choose provider
    provider = ASR_PROVIDER
    if provider == "vosk":
        text = await transcribe_with_vosk(save_path)
    else:
        text = await transcribe_with_hf(save_path)
    return {"text": text}