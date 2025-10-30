# app.py - Синхронная версия с Flask
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, text, BigInteger
from sqlalchemy import exc as sa_exc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from groq import Groq
import threading
import tempfile
import subprocess
import re
import json
import base64
import io
import asyncio
import jwt
import hmac
import hashlib
import urllib.parse as urlparse
try:
    import google.generativeai as genai
except Exception:
    genai = None
try:
    from gtts import gTTS
except Exception:
    gTTS = None
try:
    import edge_tts
except Exception:
    edge_tts = None

# Gemini API key configuration
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or os.getenv('GENAI_API_KEY')
if genai and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("[REVIEW] Gemini configured")
    except Exception as _cfg_err:
        print(f"[REVIEW] Gemini configure error: {_cfg_err}")
else:
    print("[REVIEW] WARNING: Gemini API key not found or library unavailable. /api/review will operate in fallback mode.")

# Flask - создаем приложение
app = Flask(__name__)

# Настраиваем CORS
# В проде разрешаем только HTTPS-оригины, в деве добавляем HTTP и localhost
env_mode = (os.getenv('ENV', '') or os.getenv('FLASK_ENV', '')).lower()
allowed_origins = [
    "https://diary.pw-new.club",
    "https://app.diary.pw-new.club",
]
if env_mode != 'prod' and env_mode != 'production':
    allowed_origins += [
        "http://diary.pw-new.club",
        "http://app.diary.pw-new.club",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

CORS(
    app,
    resources={r"/api/*": {"origins": allowed_origins}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    always_send=False,
)

# Устанавливаем конфигурацию
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Register Telegram routes (webhook, sessions)
try:
    from .routers.telegram import register_telegram_routes  # type: ignore
except Exception:
    # Fallback for running as script (python backend/app.py)
    from routers.telegram import register_telegram_routes  # type: ignore

try:
    register_telegram_routes(app)
    print("[TELEGRAM] Routes registered under /api/telegram")
except Exception as e:
    # Don't crash app if Telegram bot is not configured; it's optional
    print(f"[TELEGRAM] Skipping Telegram routes: {e}")

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///diary.db')
# PostgreSQL: postgresql://user:pass@host/db

# SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Register Billing module (subscriptions, trial, payments)
try:
    from backend.modules.billing import create_billing_blueprint  # type: ignore
    from backend.modules.billing.service import BillingService  # type: ignore
except Exception:
    # Fallback for running as script (python backend/app.py)
    from modules.billing import create_billing_blueprint  # type: ignore
    from modules.billing.service import BillingService  # type: ignore

try:
    billing_bp = create_billing_blueprint(engine)
    app.register_blueprint(billing_bp, url_prefix='/api/billing')
    billing_service = BillingService(engine)
    print("[BILLING] Module registered under /api/billing")
except Exception as e:
    billing_service = None
    print(f"[BILLING] Skipping billing module: {e}")

# Groq client
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# SQLAlchemy Models
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    photo_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'photo_url': self.photo_url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Entry(Base):
    __tablename__ = 'entry'
    
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    audio_duration = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'language': self.language,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'audio_duration': self.audio_duration
        }

def _ensure_schema():
    # Create tables if needed; guard against rare pg composite type name clashes
    try:
        Base.metadata.create_all(bind=engine)
    except sa_exc.IntegrityError as e:
        msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        if 'pg_type_typname_nsp_index' in msg:
            print('[DB] WARNING: Skipping create_all due to existing composite type name clash; schema likely present')
        else:
            raise
    # Add column entry.user_id if not exists (simple migration)
    inspector = inspect(engine)
    try:
        cols = [c['name'] for c in inspector.get_columns('entry')]
        if 'user_id' not in cols:
            with engine.connect() as conn:
                try:
                    conn.execute(text('ALTER TABLE entry ADD COLUMN user_id INTEGER'))
                    conn.commit()
                    print('[DB] Added column entry.user_id')
                except Exception as e:
                    print(f'[DB] Could not add entry.user_id: {e}')
    except Exception as e:
        print(f'[DB] Inspector error: {e}')

    # Ensure user.telegram_id uses BIGINT in PostgreSQL to fit large Telegram IDs
    try:
        ucols = inspector.get_columns('user')
        tele_col = next((c for c in ucols if c.get('name') == 'telegram_id'), None)
        if tele_col:
            col_type = str(tele_col.get('type')).lower()
            if 'bigint' not in col_type and engine.dialect.name in ['postgresql', 'postgres']:
                with engine.connect() as conn:
                    try:
                        conn.execute(text('ALTER TABLE "user" ALTER COLUMN telegram_id TYPE BIGINT USING telegram_id::bigint'))
                        conn.commit()
                        print('[DB] Migrated user.telegram_id to BIGINT')
                    except Exception as e:
                        print(f'[DB] Could not alter user.telegram_id to BIGINT: {e}')
    except Exception as e:
        print(f'[DB] telegram_id type check error: {e}')

_ensure_schema()

# --- Auth helpers (JWT + Telegram WebApp) ---
def _jwt_secret() -> str:
    return os.getenv('JWT_SECRET', 'dev-secret')

def create_access_token(payload: dict, expires_minutes: int = 60 * 24 * 30) -> str:
    to_encode = payload.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({
        'exp': expire,
        'iat': datetime.utcnow(),
    })
    return jwt.encode(to_encode, _jwt_secret(), algorithm='HS256')

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, _jwt_secret(), algorithms=['HS256'])

def get_current_user(db, req: request):
    auth_header = req.headers.get('Authorization') or ''
    token = None
    if auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1].strip()
    if not token:
        token = req.cookies.get('access_token')
    if not token:
        token = req.args.get('token')  # fallback for debug
    if not token:
        return None
    try:
        data = decode_access_token(token)
        uid = data.get('sub')
        if not uid:
            return None
        user = db.query(User).filter(User.id == int(uid)).first()
        return user
    except Exception:
        return None

def require_user():
    db = SessionLocal()
    try:
        user = get_current_user(db, request)
        if not user:
            return None, (jsonify({'error': 'Unauthorized'}), 401)
        return user, None
    finally:
        db.close()

def _verify_telegram_init_data(init_data: str) -> dict:
    """Verify Telegram WebApp initData and return parsed fields if valid, else {}."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    if not bot_token:
        return {}
    try:
        # Parse query-string like data
        # Example: query_id=...&user=%7B...%7D&auth_date=...&hash=...
        pairs = [p for p in init_data.split('&') if '=' in p]
        data = {}
        for p in pairs:
            k, v = p.split('=', 1)
            data[k] = v
        received_hash = data.pop('hash', None)
        if not received_hash:
            return {}
        # Build data_check_string
        check_arr = []
        for k in sorted(data.keys()):
            check_arr.append(f"{k}={data[k]}")
        data_check_string = '\n'.join(check_arr)
        secret_key = hashlib.sha256(('WebAppData' + bot_token).encode()).digest()
        hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(hmac_hash, received_hash):
            return {}
        # Extract user json
        user_json = data.get('user')
        if user_json:
            try:
                user_str = urlparse.unquote(user_json)
                user_obj = json.loads(user_str)
            except Exception:
                user_obj = json.loads(user_json)
        else:
            user_obj = {}
        return {
            'user': user_obj,
            'auth_date': data.get('auth_date')
        }
    except Exception as e:
        print(f"[AUTH] Telegram init_data verify error: {e}")
        return {}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# --- Auth routes ---
try:
    from .services.telegram_bot import SessionStore  # type: ignore
except Exception:
    from services.telegram_bot import SessionStore  # type: ignore

def _set_auth_cookie(resp, token: str):
    secure = (os.getenv('ENV', '').lower() in ['prod', 'production']) or (os.getenv('ENABLE_SECURE_COOKIE', 'false').lower() == 'true')
    # В Telegram WebView cookie иногда рассматриваются как кросс-сайтовые.
    # Если secure включен (прод), используем SameSite=None для совместимости.
    samesite_mode = 'None' if secure else 'Lax'
    resp.set_cookie(
        'access_token',
        token,
        httponly=True,
        secure=secure,
        samesite=samesite_mode,
        max_age=60*60*24*30
    )
    return resp

def _get_or_create_user(db, tg_user: dict):
    tg_id = tg_user.get('id') if isinstance(tg_user, dict) else None
    user = None
    if tg_id:
        user = db.query(User).filter(User.telegram_id == int(tg_id)).first()
    if not user:
        user = User(
            telegram_id=int(tg_id) if tg_id else None,
            username=(tg_user.get('username') if isinstance(tg_user, dict) else None),
            first_name=(tg_user.get('first_name') if isinstance(tg_user, dict) else None),
            last_name=(tg_user.get('last_name') if isinstance(tg_user, dict) else None),
            photo_url=(tg_user.get('photo_url') if isinstance(tg_user, dict) else None),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # update basic fields
        changed = False
        if isinstance(tg_user, dict):
            if user.username != tg_user.get('username'):
                user.username = tg_user.get('username'); changed = True
            if user.first_name != tg_user.get('first_name'):
                user.first_name = tg_user.get('first_name'); changed = True
            if user.last_name != tg_user.get('last_name'):
                user.last_name = tg_user.get('last_name'); changed = True
            if user.photo_url != tg_user.get('photo_url'):
                user.photo_url = tg_user.get('photo_url'); changed = True
        if changed:
            db.commit()
            db.refresh(user)
    return user

@app.route('/api/auth/telegram', methods=['POST'])
def auth_telegram():
    payload = request.get_json(silent=True) or {}
    init_data = payload.get('init_data') or payload.get('initData') or ''
    if not init_data:
        return jsonify({'error': 'init_data is required'}), 400
    verified = _verify_telegram_init_data(init_data)
    if not verified:
        return jsonify({'error': 'invalid init_data'}), 401
    db = SessionLocal()
    try:
        user = _get_or_create_user(db, verified.get('user') or {})
        token = create_access_token({'sub': str(user.id), 'tg_id': user.telegram_id, 'username': user.username})
        resp = make_response(jsonify({'access_token': token, 'token_type': 'bearer', 'user': user.to_dict()}))
        return _set_auth_cookie(resp, token)
    finally:
        db.close()

@app.route('/api/auth/telegram/session', methods=['POST'])
def auth_telegram_session():
    payload = request.get_json(silent=True) or {}
    sess_token = payload.get('session') or payload.get('session_token')
    if not sess_token:
        return jsonify({'error': 'session_token is required'}), 400
    store = SessionStore()
    tg_user_id = None
    try:
        # reuse list_notes to derive user_id for given session
        info = store.list_notes(sess_token)
        tg_user_id = info.get('user_id')
    except Exception:
        tg_user_id = None
    if not tg_user_id:
        return jsonify({'error': 'invalid session token'}), 401
    db = SessionLocal()
    try:
        tg_user = {'id': int(tg_user_id)}
        user = _get_or_create_user(db, tg_user)
        token = create_access_token({'sub': str(user.id), 'tg_id': user.telegram_id, 'username': user.username})
        resp = make_response(jsonify({'access_token': token, 'token_type': 'bearer', 'user': user.to_dict()}))
        return _set_auth_cookie(resp, token)
    finally:
        db.close()

@app.route('/api/auth/select', methods=['POST'])
def auth_select():
    payload = request.get_json(silent=True) or {}
    token = payload.get('access_token')
    if not token:
        return jsonify({'error': 'access_token is required'}), 400
    try:
        decode_access_token(token)
    except Exception:
        return jsonify({'error': 'invalid token'}), 400
    resp = make_response(jsonify({'status': 'ok'}))
    return _set_auth_cookie(resp, token)

@app.route('/api/auth/me', methods=['GET'])
def auth_me():
    db = SessionLocal()
    try:
        user = get_current_user(db, request)
        if not user:
            return jsonify({'authenticated': False}), 401
        return jsonify({'authenticated': True, 'user': user.to_dict()})
    finally:
        db.close()

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    resp = make_response(jsonify({'status': 'ok'}))
    resp.delete_cookie('access_token')
    return resp

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        print(f"[TRANSCRIBE] Request received - Files: {list(request.files.keys())}")
        print(f"[TRANSCRIBE] Form data: {dict(request.form)}")
        
        if 'audio' not in request.files:
            print("[TRANSCRIBE] ERROR: No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language', 'auto')
        
        # Read size for logging and reset pointer on underlying stream
        raw_preview = audio_file.stream.read()
        print(f"[TRANSCRIBE] Audio file: {audio_file.filename}, size: {len(raw_preview)} bytes, content_type: {audio_file.content_type}")
        audio_file.stream.seek(0)
        
        if audio_file.filename == '':
            print("[TRANSCRIBE] ERROR: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        # Ensure GROQ_API_KEY is present
        api_key_present = bool(os.getenv('GROQ_API_KEY'))
        print(f"[TRANSCRIBE] GROQ_API_KEY present: {api_key_present}")
        
        print(f"[TRANSCRIBE] Starting Groq transcription with language: {language}")
        
        # Write to a temporary file with correct extension for Groq
        ext = os.path.splitext(audio_file.filename)[1] or '.webm'
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(raw_preview)
            tmp_path = tmp.name
        print(f"[TRANSCRIBE] Temp file created: {tmp_path}")
        
        # Convert webm/opus to wav 16k mono if needed
        use_path = tmp_path
        converted_path = None
        try:
            if (ext.lower() == '.webm') or (audio_file.content_type and 'webm' in audio_file.content_type):
                converted_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
                cmd = ['ffmpeg', '-y', '-i', tmp_path, '-ac', '1', '-ar', '16000', converted_path]
                print(f"[TRANSCRIBE] Converting webm→wav: {' '.join(cmd)}")
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode != 0:
                    print(f"[TRANSCRIBE] ffmpeg error: {res.stderr}")
                else:
                    use_path = converted_path
                    print(f"[TRANSCRIBE] Conversion OK: {converted_path}")
        except Exception as conv_err:
            print(f"[TRANSCRIBE] ffmpeg exception: {conv_err}")
        
        try:
            with open(use_path, 'rb') as f:
                transcription = groq_client.audio.transcriptions.create(
                    file=f,
                    model="whisper-large-v3",
                    language=language if language != 'auto' else None
                )
        finally:
            # Clean temp files
            for p in [tmp_path, converted_path]:
                if p:
                    try:
                        os.remove(p)
                        print(f"[TRANSCRIBE] Temp file removed: {p}")
                    except Exception as cleanup_err:
                        print(f"[TRANSCRIBE] Temp file cleanup error: {cleanup_err}")
        
        print(f"[TRANSCRIBE] Success! Text length: {len(transcription.text)} chars")
        
        return jsonify({
            'text': transcription.text,
            'language': language
        })
        
    except Exception as e:
        print(f"[TRANSCRIBE] ERROR: {str(e)}")
        import traceback
        print(f"[TRANSCRIBE] Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['GET'])
def get_entries():
    try:
        db = SessionLocal()
        # Требуем аутентификацию и фильтруем по текущему пользователю
        user = get_current_user(db, request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        language = request.args.get('language')
        
        query = db.query(Entry).filter(Entry.user_id == user.id)
        
        if language:
            query = query.filter(Entry.language == language)
        
        # Pagination
        offset = (page - 1) * per_page
        entries = query.order_by(Entry.timestamp.desc()).offset(offset).limit(per_page).all()
        total = query.count()
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries', methods=['POST'])
def create_entry():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        db = SessionLocal()
        # Требуем аутентификацию и привязываем запись к пользователю
        user = get_current_user(db, request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        entry = Entry(
            text=data['text'],
            language=data.get('language', 'unknown'),
            audio_duration=data.get('audio_duration'),
            user_id=user.id
        )
        
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        return jsonify(entry.to_dict()), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries/<int:entry_id>', methods=['GET'])
def get_entry(entry_id):
    try:
        db = SessionLocal()
        # Требуем аутентификацию и проверяем владение записью
        user = get_current_user(db, request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        # Дополнительная проверка: требуем активную подписку для доступа к записи
        if billing_service and not billing_service.has_active_access(user.id):
            return jsonify({'error': 'Subscription required', 'code': 'subscription_required'}), 402
        entry = db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user.id).first()

        if not entry:
            return jsonify({'error': 'Entry not found'}), 404

        return jsonify(entry.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries/<int:entry_id>', methods=['PUT'])
def update_entry(entry_id):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        db = SessionLocal()
        # Требуем аутентификацию и проверяем владение записью
        user = get_current_user(db, request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        entry = db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user.id).first()
        
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        if 'text' in data:
            entry.text = data['text']
        if 'language' in data:
            entry.language = data['language']
        if 'audio_duration' in data:
            entry.audio_duration = data['audio_duration']
        
        db.commit()
        db.refresh(entry)
        
        return jsonify(entry.to_dict())
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    try:
        db = SessionLocal()
        # Требуем аутентификацию и проверяем владение записью
        user = get_current_user(db, request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        entry = db.query(Entry).filter(Entry.id == entry_id, Entry.user_id == user.id).first()
        
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        db.delete(entry)
        db.commit()
        
        return jsonify({'message': 'Entry deleted successfully'})
        
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/search', methods=['GET'])
def search_entries():
    try:
        query_text = request.args.get('q', '').strip()
        
        if not query_text:
            return jsonify({'error': 'Search query is required'}), 400
        
        db = SessionLocal()
        # Требуем аутентификацию и фильтруем по текущему пользователю
        user = get_current_user(db, request)
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        entries = db.query(Entry).filter(
            Entry.user_id == user.id,
            Entry.text.contains(query_text)
        ).order_by(Entry.timestamp.desc()).limit(50).all()
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries],
            'query': query_text,
            'count': len(entries)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/review', methods=['POST'])
def review_entry():
    try:
        payload = request.get_json(silent=True) or {}
        if not payload or 'text' not in payload:
            return jsonify({'error': 'Text is required'}), 400
        text = payload['text']
        language = payload.get('language', 'unknown')
        ui_language = payload.get('ui_language', 'ru')

        result = review_with_gemini(text, language, ui_language)
        corrected = result.get('corrected_text', text)
        is_changed = bool(result.get('changed', corrected.strip() != text.strip()))
        corrected_html = _highlight_diff(text, corrected) if is_changed else corrected
        explanations = result.get('explanations', [])
        explanations_html = '<br>'.join(explanations) if explanations else ''
        # Server-side TTS for corrected phrase
        tts_data_url = synthesize_tts(corrected, result.get('language', language))

        return jsonify({
            'original_text': text,
            'corrected_text': corrected,
            'corrected_html': corrected_html,
            'explanations': explanations,
            'explanations_html': explanations_html,
            'is_changed': is_changed,
            'language': result.get('language', language),
            'tts_audio_data_url': tts_data_url
        })
    except Exception as e:
        print(f"[REVIEW] ERROR: {e}")
        return jsonify({'error': str(e)}), 500

# Helper functions for diff/highlight
import difflib

def _tokenize(text: str):
    return re.findall(r"\w+|[^\w\s]", text, re.UNICODE)


def _rebuild_with_spaces(tokens):
    res = []
    for i, t in enumerate(tokens):
        res.append(t)
        if i < len(tokens) - 1:
            curr_is_word = bool(re.match(r"\w", t, re.UNICODE))
            next_is_word = bool(re.match(r"\w", tokens[i + 1], re.UNICODE))
            if curr_is_word and next_is_word:
                res.append(' ')
            elif t in ['"', "'"] and next_is_word:
                res.append(' ')
            elif curr_is_word and tokens[i + 1] in ['"', "'"]:
                res.append(' ')
    return ''.join(res)


def _highlight_diff(original: str, corrected: str) -> str:
    orig_tokens = _tokenize(original)
    corr_tokens = _tokenize(corrected)
    sm = difflib.SequenceMatcher(a=orig_tokens, b=corr_tokens)
    parts = []
    prev_last_token = None

    def _needs_space(prev_tok, next_tok):
        if not prev_tok or not next_tok:
            return False
        prev_is_word = bool(re.match(r"\w", prev_tok, re.UNICODE))
        next_is_word = bool(re.match(r"\w", next_tok, re.UNICODE))
        if prev_is_word and next_is_word:
            return True
        if prev_tok in ['"', "'"] and next_is_word:
            return True
        if prev_is_word and next_tok in ['"', "'"]:
            return True
        return False

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        segment = corr_tokens[j1:j2]
        first_tok = segment[0] if segment else None
        if _needs_space(prev_last_token, first_tok):
            parts.append(' ')
        if tag == 'equal':
            parts.append(_rebuild_with_spaces(segment))
        elif tag in ('replace', 'insert'):
            if segment:
                parts.append('<mark>' + _rebuild_with_spaces(segment) + '</mark>')
        if segment:
            prev_last_token = segment[-1]
    return ''.join(parts)


def _map_tts_lang(language: str) -> str:
    l = (language or '').lower()
    if l.startswith('ru'):
        return 'ru'
    if l.startswith('en'):
        return 'en'
    if l.startswith('pt'):
        return 'pt'
    if l.startswith('es'):
        return 'es'
    if l.startswith('pl'):
        return 'pl'
    return 'en'


def synthesize_tts(text: str, language: str):
    """Return data URL (audio/mpeg) synthesized from text or None if unavailable."""
    if not text:
        return None

    # --- Edge TTS mapping for Portuguese (prefer pt-PT) ---
    def _edge_pt_config(lang_id: str):
        l = (lang_id or '').lower()
        mapping = {
            'pt': {
                'voice': 'pt-PT-RaquelNeural',
                'backup': ['pt-PT-DuarteNeural']
            },
            'pt-pt': {
                'voice': 'pt-PT-RaquelNeural',
                'backup': ['pt-PT-DuarteNeural']
            },
            'pt-br': {
                'voice': 'pt-BR-FranciscaNeural',
                'backup': ['pt-BR-AntonioNeural']
            },
        }
        if l in mapping:
            return mapping[l]
        base = l.split('-')[0]
        if base in mapping:
            return mapping[base]
        return mapping['pt']

    # --- Generic Edge TTS mapping for other languages ---
    def _edge_voice_config(lang_id: str):
        l = (lang_id or '').lower()
        mapping = {
            # Russian
            'ru': {
                'voice': 'ru-RU-DmitryNeural',
                'backup': ['ru-RU-SvetlanaNeural']
            },
            'ru-ru': {
                'voice': 'ru-RU-DmitryNeural',
                'backup': ['ru-RU-SvetlanaNeural']
            },
            # English (US/GB)
            'en': {
                'voice': 'en-US-GuyNeural',
                'backup': ['en-US-JennyNeural', 'en-GB-RyanNeural']
            },
            'en-us': {
                'voice': 'en-US-GuyNeural',
                'backup': ['en-US-JennyNeural']
            },
            'en-gb': {
                'voice': 'en-GB-RyanNeural',
                'backup': ['en-GB-LibbyNeural']
            },
            # Spanish (Spain)
            'es': {
                'voice': 'es-ES-AlvaroNeural',
                'backup': ['es-ES-ElviraNeural']
            },
            'es-es': {
                'voice': 'es-ES-AlvaroNeural',
                'backup': ['es-ES-ElviraNeural']
            },
            # Polish
            'pl': {
                'voice': 'pl-PL-MarekNeural',
                'backup': ['pl-PL-ZofiaNeural']
            },
            'pl-pl': {
                'voice': 'pl-PL-MarekNeural',
                'backup': ['pl-PL-ZofiaNeural']
            },
        }
        if l in mapping:
            return mapping[l]
        base = l.split('-')[0]
        if base in mapping:
            return mapping[base]
        return None

    # Prefer Edge TTS for Portuguese to ensure European accent
    lang_lower = (language or '').lower()
    if edge_tts is not None and lang_lower.startswith('pt'):
        try:
            cfg = _edge_pt_config(lang_lower)
            primary_voice = os.getenv('EDGE_TTS_PT_VOICE', cfg['voice'])

            async def _stream_voice(v):
                communicate = edge_tts.Communicate(text, voice=v)
                audio_bytes = b''
                async for chunk in communicate.stream():
                    if chunk.get('type') == 'audio':
                        audio_bytes += chunk.get('data', b'')
                return audio_bytes

            # Try primary voice
            try:
                data = asyncio.run(_stream_voice(primary_voice))
                b64 = base64.b64encode(data).decode('ascii')
                return f"data:audio/mpeg;base64,{b64}"
            except Exception as e1:
                print(f"[TTS] EDGE-TTS primary voice failed: {e1}")

            # Try backups
            for bv in (cfg.get('backup') or []):
                try:
                    data = asyncio.run(_stream_voice(bv))
                    b64 = base64.b64encode(data).decode('ascii')
                    return f"data:audio/mpeg;base64,{b64}"
                except Exception as e2:
                    print(f"[TTS] EDGE-TTS backup voice '{bv}' failed: {e2}")

            # If we reached here, Edge TTS failed for Portuguese
            _allow_pt_fallback = (os.getenv('ALLOW_PT_GTTs_FALLBACK', 'false').strip().lower() in ('1','true','yes','on'))
            if _allow_pt_fallback:
                print("[TTS] EDGE-TTS failed for Portuguese; ALLOW_PT_GTTs_FALLBACK=true → falling back to gTTS (pt)")
                # Do not return here; continue to generic gTTS fallback section below
            else:
                print("[TTS] EDGE-TTS failed for Portuguese; skipping gTTS to avoid wrong accent")
                return None
        except Exception as e:
            print(f"[TTS] EDGE-TTS ERROR (Portuguese branch): {e}")

    # Try Edge TTS for other languages using mapping; if fails, continue to gTTS fallback
    if edge_tts is not None and not lang_lower.startswith('pt'):
        try:
            cfg_other = _edge_voice_config(lang_lower)
            if cfg_other:
                primary_voice_other = os.getenv('EDGE_TTS_VOICE', cfg_other['voice'])

                async def _stream_voice_other(v):
                    communicate = edge_tts.Communicate(text, voice=v)
                    audio_bytes = b''
                    async for chunk in communicate.stream():
                        if chunk.get('type') == 'audio':
                            audio_bytes += chunk.get('data', b'')
                    return audio_bytes

                # Try primary voice
                try:
                    data = asyncio.run(_stream_voice_other(primary_voice_other))
                    b64 = base64.b64encode(data).decode('ascii')
                    return f"data:audio/mpeg;base64,{b64}"
                except Exception as e1:
                    print(f"[TTS] EDGE-TTS primary voice failed (generic): {e1}")

                # Try backups
                for bv in (cfg_other.get('backup') or []):
                    try:
                        data = asyncio.run(_stream_voice_other(bv))
                        b64 = base64.b64encode(data).decode('ascii')
                        return f"data:audio/mpeg;base64,{b64}"
                    except Exception as e2:
                        print(f"[TTS] EDGE-TTS backup voice '{bv}' failed (generic): {e2}")
        except Exception as e:
            print(f"[TTS] EDGE-TTS ERROR (generic branch): {e}")

    # Fallback: gTTS for other languages (and optionally for pt-PT if ALLOW_PT_GTTs_FALLBACK enabled)
    if gTTS is None:
        print("[TTS] WARNING: gTTS library unavailable, skipping synthesis")
        return None
    try:
        _allow_pt_fallback = (os.getenv('ALLOW_PT_GTTs_FALLBACK', 'false').strip().lower() in ('1','true','yes','on'))
        # Avoid using gTTS for Portuguese unless explicitly allowed
        if (language or '').lower().startswith('pt') and not _allow_pt_fallback:
            return None
        # gTTS поддерживает только общий 'pt', без акцентных различий
        if (language or '').lower().startswith('pt') and _allow_pt_fallback:
            lang_code = 'pt'
        else:
            lang_code = _map_tts_lang(language)
        buf = io.BytesIO()
        gTTS(text=text, lang=lang_code).write_to_fp(buf)
        data = buf.getvalue()
        b64 = base64.b64encode(data).decode('ascii')
        return f"data:audio/mpeg;base64,{b64}"
    except Exception as e:
        print(f"[TTS] ERROR: {e}")
        return None


def _build_review_prompt(text: str, language: str, ui_language: str = 'ru'):
    lang_label = language or 'auto'
    ui_label = (ui_language or 'ru').lower()
    return (
        "Ты опытный преподаватель иностранного языка. Проверь фразу на грамматическую и смысловую корректность, сохраняя исходный смысл. "
        "Если нужны исправления — предоставь исправленный вариант. Ответь строго одним JSON-объектом без Markdown и без пояснений вне JSON. "
        "Используй ключи: corrected_text (string), explanations (array of strings — пиши пояснения на языке интерфейса), language (string — код языка исходного текста), changed (boolean). "
        "Если исправлений нет, верни corrected_text равным исходному тексту и changed=false. "
        f"Язык интерфейса: {ui_label}. Язык фразы: {lang_label}. Фраза: \"\"\"{text}\"\"\""
    )


def review_with_gemini(text: str, language: str, ui_language: str = 'ru'):
    if not (genai and GEMINI_API_KEY):
        return {
            'corrected_text': text,
            'explanations': ['Проверка недоступна: отсутствует ключ Gemini или библиотека.'],
            'language': language,
            'changed': False
        }
    try:
        model_candidates = ['gemini-1.5-pro-latest', 'gemini-1.5-pro', 'gemini-2.5-flash-latest', 'gemini-2.5-flash']
        last_err = None
        for model_name in model_candidates:
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(_build_review_prompt(text, language, ui_language))
                raw = (getattr(resp, 'text', '') or '').strip()
                # Try to extract JSON
                start = raw.find('{')
                end = raw.rfind('}')
                if start != -1 and end != -1:
                    raw = raw[start:end + 1]
                data = json.loads(raw)
                corrected = data.get('corrected_text') or text
                explanations = data.get('explanations') or []
                changed = data.get('changed')
                if changed is None:
                    changed = corrected.strip() != text.strip()
                return {
                    'corrected_text': corrected,
                    'explanations': explanations,
                    'language': data.get('language') or language,
                    'changed': bool(changed)
                }
            except Exception as e:
                last_err = e
                print(f"[REVIEW] Gemini model {model_name} error: {e}")
                continue
        # If all candidates failed, raise last error to hit the outer fallback
        raise last_err or Exception("Gemini failed for all candidate models")
    except Exception as e:
        print(f"[REVIEW] Gemini error: {e}")
        return {
            'corrected_text': text,
            'explanations': ['Не удалось выполнить проверку, используем исходный текст.'],
            'language': language,
            'changed': False
        }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)