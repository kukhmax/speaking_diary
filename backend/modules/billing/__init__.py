from flask import Blueprint, jsonify, request
from .service import BillingService
from .providers.telegram import TelegramProvider
from .providers.stripe import StripeProvider


def create_billing_blueprint(engine=None):
    """Фабрика Flask Blueprint для эндпоинтов биллинга.

    Параметры:
    - engine: SQLAlchemy Engine для хранения состояния подписок/планов.

    Эндпоинты:
    - GET /health — проверка живости.
    - GET /status — статус подписки (по user_id в query).
    - POST /activate-trial — активация триала.
    - POST /telegram/invoice — получение ссылки инвойса Telegram (stub).
    - POST /stripe/checkout — создание сессии Stripe (stub).
    """
    bp = Blueprint('billing', __name__)
    svc = BillingService(engine)
    tg = TelegramProvider()
    stripe = StripeProvider()

    @bp.route('/health', methods=['GET'])
    def health():
        """Возвращает базовую проверку живости модуля."""
        return jsonify({'ok': True})

    @bp.route('/status', methods=['GET'])
    def status():
        """Возвращает статус подписки пользователя по `user_id` из query-параметров."""
        user_id = int(request.args.get('user_id', '0'))
        return jsonify(svc.get_subscription_status(user_id=user_id))

    @bp.route('/activate-trial', methods=['POST'])
    def activate_trial():
        """Активирует триал-подписку для пользователя, указанного в теле запроса."""
        payload = request.get_json(silent=True) or {}
        user_id = int(str(payload.get('user_id', '0')))
        svc.activate_trial(user_id)
        return jsonify({'ok': True, 'subscription': svc.get_subscription_status(user_id)})

    @bp.route('/telegram/invoice', methods=['POST'])
    def telegram_invoice():
        """Создаёт ссылку на оплату через Telegram (заглушка)."""
        payload = request.get_json(silent=True) or {}
        plan_code = payload.get('plan_code', 'pro_monthly')
        amount_cents = 300 if plan_code == 'pro_monthly' else 0
        stub = tg.create_invoice_link(
            title='Diary Pro',
            description='Подписка Diary Pro',
            payload=f"user:{payload.get('user_id', 0)}:plan:{plan_code}",
            amount_cents=amount_cents,
            currency='USD',
        )
        return jsonify(stub)

    @bp.route('/stripe/checkout', methods=['POST'])
    def stripe_checkout():
        """Создаёт сессию Stripe Checkout (заглушка) для указанного пользователя."""
        payload = request.get_json(silent=True) or {}
        user_id = int(str(payload.get('user_id', '0')))
        session = stripe.create_checkout_session(
            user_id=user_id,
            success_url=payload.get('success_url') or 'https://example.com/success',
            cancel_url=payload.get('cancel_url') or 'https://example.com/cancel',
        )
        return jsonify(session)

    return bp