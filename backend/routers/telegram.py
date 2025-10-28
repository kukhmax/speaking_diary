import os
from flask import Blueprint, request, jsonify

from ..services.telegram_bot import TelegramBotService, validate_webhook_secret, SessionStore


def register_telegram_routes(app):
    """
    Register Telegram webhook and helper endpoints under /api/telegram/*.
    """
    bp = Blueprint('telegram', __name__, url_prefix='/api/telegram')

    # Lazy init service to avoid failing app startup without token in dev
    def _get_service() -> TelegramBotService:
        token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
        webapp_url = os.getenv('PUBLIC_WEBAPP_URL', '').strip()
        if not token or not webapp_url:
            raise RuntimeError('TELEGRAM_BOT_TOKEN or PUBLIC_WEBAPP_URL is not configured')
        return TelegramBotService(token, webapp_url)

    @bp.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok'}), 200

    @bp.route('/webhook', methods=['POST'])
    def webhook():
        # Optional secret to reduce abuse
        secret = request.args.get('secret')
        if not validate_webhook_secret(secret):
            return jsonify({'error': 'forbidden'}), 403
        try:
            update = request.get_json(force=True, silent=True) or {}
            service = _get_service()
            service.process_update(update)
            return jsonify({'ok': True})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500

    # Simple per-user records endpoints (using session token)
    @bp.route('/notes', methods=['GET'])
    def list_notes():
        token = request.headers.get('X-Session-Token') or request.args.get('session')
        if not token:
            return jsonify({'error': 'Session token required'}), 400
        try:
            store = SessionStore()
            data = store.list_notes(token)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @bp.route('/notes', methods=['POST'])
    def add_note():
        token = request.headers.get('X-Session-Token') or request.args.get('session')
        if not token:
            return jsonify({'error': 'Session token required'}), 400
        payload = request.get_json(silent=True) or {}
        text = (payload.get('text') or '').strip()
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        try:
            store = SessionStore()
            note = store.add_note(token, text)
            return jsonify({'note': note}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    app.register_blueprint(bp)