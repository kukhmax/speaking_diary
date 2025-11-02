import os
import json
import time
import hmac
import hashlib
import threading
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

import requests


SESSIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'telegram_sessions.json')


def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


class SessionStore:
    """File-based session store keyed by Telegram user id."""

    def __init__(self, path: str = SESSIONS_PATH):
        self.path = os.path.abspath(path)
        _ensure_dir(self.path)
        self._lock = threading.Lock()
        if not os.path.exists(self.path):
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _load(self) -> Dict[str, Any]:
        with open(self.path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return {}

    def _save(self, data: Dict[str, Any]):
        tmp_path = self.path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self.path)

    def _gen_token(self, user_id: int) -> str:
        # HMAC-based token using secret if present
        secret = os.getenv('TELEGRAM_WEBHOOK_SECRET', 'dev-secret')
        payload = f"{user_id}:{int(time.time())}:{os.getpid()}".encode('utf-8')
        return hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()

    def get_or_create(self, user_id: int) -> Dict[str, Any]:
        uid = str(user_id)
        with self._lock:
            data = self._load()
            sess = data.get(uid)
            if not sess:
                sess = {
                    'user_id': user_id,
                    'session_token': self._gen_token(user_id),
                    'created_at': int(time.time()),
                    'last_seen': int(time.time()),
                    'notes': []  # simple per-user records example
                }
                data[uid] = sess
                self._save(data)
                return sess
            # Update last_seen
            sess['last_seen'] = int(time.time())
            data[uid] = sess
            self._save(data)
            return sess

    def add_note(self, session_token: str, text: str) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            for uid, sess in data.items():
                if sess.get('session_token') == session_token:
                    note = {
                        'id': int(time.time() * 1000),
                        'text': text,
                        'timestamp': int(time.time())
                    }
                    sess.setdefault('notes', []).append(note)
                    sess['last_seen'] = int(time.time())
                    data[uid] = sess
                    self._save(data)
                    return note
        raise ValueError('Invalid session token')

    def list_notes(self, session_token: str) -> Dict[str, Any]:
        with self._lock:
            data = self._load()
            for sess in data.values():
                if sess.get('session_token') == session_token:
                    return {
                        'user_id': sess.get('user_id'),
                        'notes': list(sess.get('notes') or [])
                    }
        raise ValueError('Invalid session token')


class TelegramBotService:
    """
    Minimal Telegram bot webhook handler using direct HTTP calls to Telegram API.
    - Handles /start
    - Sends an inline button that opens the WebApp (Mini App)
    - Manages per-user sessions stored in a JSON file
    """

    def __init__(self, bot_token: str, public_webapp_url: str):
        if not bot_token:
            raise RuntimeError('TELEGRAM_BOT_TOKEN is not set')
        if not public_webapp_url:
            raise RuntimeError('PUBLIC_WEBAPP_URL is not set')
        self.token = bot_token.strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.webapp_url = public_webapp_url.rstrip('/')
        # Версия фронтенда для кеш-бастинга Telegram WebView
        # Можно задать через переменную окружения WEBAPP_VERSION/FRONTEND_VERSION
        # Если не задано, используем номер дня (обновляется раз в сутки)
        self.version = (os.getenv('WEBAPP_VERSION') or os.getenv('FRONTEND_VERSION') or str(int(time.time() // 86400)))
        self.sessions = SessionStore()

    def _post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{method}"
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None):
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        return self._post('sendMessage', payload)

    def _webapp_keyboard(self, url: str) -> Dict[str, Any]:
        return {
            'inline_keyboard': [[
                {
                    'text': 'Открыть приложение',
                    'web_app': {'url': url}
                }
            ]]
        }

    def process_update(self, update: Dict[str, Any]):
        message = update.get('message') or update.get('edited_message')
        if not message:
            # ignore non-message updates for now
            return
        chat = message.get('chat') or {}
        text = (message.get('text') or '').strip()
        from_user = message.get('from') or {}
        chat_id = chat.get('id')
        user_id = from_user.get('id')

        if not chat_id or not user_id:
            return

        if text.startswith('/start'):
            sess = self.sessions.get_or_create(user_id)
            sess_token = sess['session_token']
            url = f"{self.webapp_url}?session={sess_token}&v={self.version}"
            greeting = (
                "👋 Привет! Я — Voice Diary.\n\n"
                "Со мной ты можешь записывать свои мысли на иностранном языке.\nПрактиковать свою речь на иностранном языке.\n\n"
                "✨ Что умею:\n"
                "• 📝 Быстрые заметки голосом на изучаемом языке.\n"
                "• ❌ Предоставяю отчет об ошибках в ваших фразах.\n"
                "• 📢 Можешь прослушать свое произношение и как корректно должна звучать фраза.\n"
                "• 🌐 Возможность перевода корректной фразы.\n"
                "• 📈 Всё сохраняется и доступно из мини‑приложения.\n\n"
                "▶️ Нажмите «Открыть приложение» ниже, чтобы начать!"
            )
            self.send_message(chat_id, greeting, reply_markup=self._webapp_keyboard(url))
        else:
            # Optional: simple echo or ignore
            self.send_message(chat_id, "Отправь /start, чтобы открыть мини‑приложение.")


def validate_webhook_secret(provided: Optional[str]) -> bool:
    """Validate an optional webhook secret to protect the endpoint."""
    expected = (os.getenv('TELEGRAM_WEBHOOK_SECRET') or '').strip()
    if not expected:
        return True  # no secret enforced
    return hmac.compare_digest(expected, (provided or '').strip())