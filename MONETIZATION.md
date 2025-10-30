# Монетизация Telegram‑приложения «Голосовой дневник»

Цель: ввести прозрачную модель монетизации с недельным бесплатным периодом, затем подписка $2–3/месяц, с технической реализацией через платежные провайдеры и строгим ограничением доступа на уровне бэкенда и клиента.

## Модель доступа
- Бесплатный период 7 дней для каждого пользователя (по `telegram_user_id`).
- После истечения — платная подписка «Pro» $2–3/мес.
- Ограничения без подписки (пример):
  - Ограничение на число записей/минут распознавания в день (например, 3 записи или 5 минут).
  - Запрет доступа к некоторым продвинутым функциям (расширенный разбор, TTS, поиск).

## Платёжные инструменты
- Telegram Payments (через провайдера, настраивается в @BotFather):
  - Поддерживаются Stripe, YooKassa, LiqPay и др. в зависимости от региона.
  - Бот создаёт счёт и высылает инвойс, либо генерирует ссылку через `createInvoiceLink`.
  - Веб‑апп открывает ссылку через `Telegram.WebApp.openTelegramLink(...)`.
  - Подтверждение оплаты приходит боту (update `successful_payment`).
- Stripe Checkout (прямо из WebApp):
  - Режим `subscription` для рекуррентных платежей.
  - Вебхуки Stripe на сервере подтверждают создание/продление подписки.
  - Фолбэк вне Telegram или для регионов/кейсов, где Telegram Payments не подходит.
- YooKassa / CloudPayments (альтернативы для РФ/CIS):
  - Интеграция по вебхукам, аналогично Stripe.

Рекомендация: начать с Telegram Payments (минимум трения в Telegram) + Stripe как фолбэк для веб‑версии вне Telegram.

## Архитектура данных
- Таблица `plans` (справочник тарифов):
  - `code`: `free`, `trial`, `pro_monthly`.
  - `price_cents`, `currency`, `quota_minutes`, `features`.
- Таблица `subscriptions`:
  - `user_id`, `plan_code`, `status` (`active`, `expired`, `canceled`),
  - `provider` (`telegram`, `stripe`, `yookassa`),
  - `started_at`, `current_period_end`,
  - `external_id` (ID у провайдера).
- Таблица `payments`:
  - `user_id`, `provider`, `external_id`, `amount_cents`, `currency`, `status`, `paid_at`.
- Таблица `usage` (учёт квот в периоде):
  - `user_id`, `period_start`, `period_end`, `minutes_used`, `entries_count`.

Пример SQLAlchemy (Flask):
```python
class Plan(Base):
    __tablename__ = 'plans'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    price_cents = Column(Integer)
    currency = Column(String)
    quota_minutes = Column(Integer)

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    plan_code = Column(String)
    status = Column(String)  # active, expired, canceled
    provider = Column(String)
    started_at = Column(DateTime)
    current_period_end = Column(DateTime)
    external_id = Column(String)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    provider = Column(String)
    external_id = Column(String)
    amount_cents = Column(Integer)
    currency = Column(String)
    status = Column(String)  # pending, paid, failed, refunded
    paid_at = Column(DateTime)
```

## Ограничение доступа (Backend)
- Вводим проверку активного доступа для защищённых эндпоинтов:
```python
from functools import wraps
from datetime import datetime

def has_active_access(user):
    sub = get_current_subscription(user.id)
    if not sub: return False
    if sub.status != 'active': return False
    return sub.current_period_end and sub.current_period_end > datetime.utcnow()

def require_active_subscription(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user_from_jwt()
        if not user:
            return make_response({'error': 'unauthorized'}, 401)
        if not has_active_access(user):
            return make_response({'error': 'payment_required'}, 402)
        return fn(*args, **kwargs)
    return wrapper

@app.route('/api/entries', methods=['GET'])
@require_active_subscription
def list_entries():
    ...
```
- Для «free/trial» допускаем доступ, но проверяем квоты в хендлерах (`/api/transcribe`, `/api/entries`).

## Логика бесплатного периода
- При первом входе через Telegram:
  - Создаём `Subscription` с `plan_code='trial'`, `status='active'`, `current_period_end=now+7d`.
  - Если подписка уже есть — не создаём заново.
- Ежедневный cron‑джоб:
  - Проверяет подписки, переводит `trial`/`pro_monthly` в `expired`, если `current_period_end < now`.

## Интеграция: Telegram Payments
1. Настроить провайдера платежей в @BotFather, получить `PAYMENTS_PROVIDER_TOKEN`.
2. Бэкенд: эндпоинт для создания инвойса:
```python
import requests, os

@app.route('/api/billing/telegram/create_invoice', methods=['POST'])
def tg_create_invoice():
    user = current_user_from_jwt()
    assert user
    payload = f"user:{user.id}:plan:pro_monthly"
    resp = requests.post(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/createInvoiceLink",
        json={
            'title': 'Diary Pro Monthly',
            'description': 'Безлимитная транскрибация, расширенные функции',
            'payload': payload,
            'provider_token': os.getenv('PAYMENTS_PROVIDER_TOKEN'),
            'currency': 'USD',
            'prices': [{'label': 'Diary Pro', 'amount': 300}],  # $3.00
        }
    )
    link = resp.json()['result']
    return {'invoice_link': link}
```
3. Frontend (WebApp):
```javascript
const buyPro = async () => {
  const r = await fetch(`${API_BASE}/billing/telegram/create_invoice`, { credentials: 'include' });
  const { invoice_link } = await r.json();
  window.Telegram?.WebApp?.openTelegramLink(invoice_link);
};
```
4. Бот: обработка `successful_payment`:
```python
@bot.message_handler(content_types=['successful_payment'])
def on_success_payment(msg):
    tg_user_id = msg.from_user.id
    # payload из счёта: user:<id>:plan:pro_monthly
    payload = msg.successful_payment.invoice_payload
    user_id = parse_user_id(payload)
    activate_subscription(user_id, plan_code='pro_monthly', provider='telegram',
                          external_id=msg.successful_payment.provider_payment_charge_id,
                          period_days=30)
    bot.send_message(tg_user_id, 'Подписка активирована! Спасибо за поддержку ❤️')
```

## Интеграция: Stripe Checkout (фолбэк)
1. Создать `price` для подписки в Stripe, получить `PRICE_ID`.
2. Бэкенд: эндпоинт для начала Checkout:
```python
import stripe, os
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.route('/api/billing/stripe/checkout', methods=['POST'])
def stripe_checkout():
    user = current_user_from_jwt()
    session = stripe.checkout.Session.create(
        mode='subscription',
        line_items=[{'price': os.getenv('STRIPE_PRICE_ID'), 'quantity': 1}],
        success_url=f"{os.getenv('PUBLIC_WEBAPP_URL')}?billing_success=1",
        cancel_url=f"{os.getenv('PUBLIC_WEBAPP_URL')}?billing_cancel=1",
        client_reference_id=str(user.id),
    )
    return {'url': session.url}

@app.route('/api/billing/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig = request.headers.get('Stripe-Signature')
    event = stripe.Webhook.construct_event(payload, sig, os.getenv('STRIPE_WEBHOOK_SECRET'))
    if event['type'] in ['checkout.session.completed', 'invoice.paid', 'customer.subscription.updated']:
        handle_stripe_event(event['data']['object'])
    return {'ok': True}
```
3. Frontend: если нет Telegram WebApp, открывать `url` Stripe.

## Клиентская логика (WebApp)
- При запуске:
  - Проверить `/api/auth/me` → получить `plan_code`, `expires_at`, квоты.
  - Если `expired` → показать paywall с кнопками «Купить в Telegram» и «Купить картой (Stripe)».
  - Включить счётчик квот: перед каждым `/api/transcribe` проверять остаток, показывать предупреждения.
- Заголовки:
  - `X-Client-Version` для диагностики.
  - `Cache-Control: no-cache` уже добавлен для избежания устаревшего состояния.

## Цепочки процессов
- Регистрация и триал:
  - Пользователь открывает WebApp → `/api/auth/telegram` → создаётся `trial` на 7 дней → доступ открыт.
- Покупка через Telegram:
  - Кнопка «Купить» → `/api/billing/telegram/create_invoice` → `openTelegramLink(invoice_link)` → успешная оплата → бот получает `successful_payment` → активирует `pro_monthly` → `auth/me` начинает возвращать активную подписку.
- Покупка через Stripe:
  - Кнопка «Купить картой» → `/api/billing/stripe/checkout` → редирект на Stripe → вебхук → обновление подписки → фронтенд видит активный статус.
- Автопродление:
  - Telegram: отправлять напоминание и новый инвойс ближе к окончанию периода.
  - Stripe: автосписание, состояние обновляется вебхуком.
- Истечение:
  - Cron проверяет `current_period_end`, переключает статус в `expired`, фронтенд показывает paywall.

## Переменные окружения
- `PAYMENTS_PROVIDER_TOKEN` — токен провайдера Telegram Payments.
- `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET` — для Stripe.
- `PUBLIC_WEBAPP_URL` — публичный URL веб‑приложения.

## План внедрения (итерации)
- Итерация 1: Бэк‑ограничения и триал
  - Миграции БД (`plans`, `subscriptions`, `payments`, `usage`).
  - Проверки доступа и квот на API.
  - `auth/me` возвращает статус подписки и лимиты.
- Итерация 2: Telegram Payments
  - Настройка провайдера, эндпоинт `create_invoice`, обработка `successful_payment` у бота.
  - Кнопка «Купить» в WebApp, обновление UI после оплаты.
- Итерация 3: Stripe (фолбэк)
  - Checkout, вебхуки, синхронизация статусов.
  - Документация и мониторинг.
- Итерация 4: Улучшения
  - Напоминания, реферальные коды, скидки, аналитика MRR/Churn.

## Безопасность и надёжность
- Webhooks: проверка подписей (Stripe), валидация payload.
- Идемпотентность активации подписки (по `external_id` + `user_id`).
- Логи и алерты на ошибки биллинга.
- Возможность ручной коррекции подписки в админке.

## UI‑заметки
- Paywall‑модалка с кратким описанием выгод.
- Статус подписки и дата окончания в настройках.
- Индикатор оставшихся минут/записей для `free/trial`.

## Примеры ответов API
```json
GET /api/auth/me → {
  "authenticated": true,
  "user": {"id": 123, "telegram_id": 456},
  "plan": {"code": "trial", "expires_at": "2025-11-07T00:00:00Z", "quota_minutes": 300},
  "usage": {"minutes_used": 42, "entries_count": 10}
}

GET /api/billing/subscription → {
  "status": "active",
  "plan_code": "pro_monthly",
  "current_period_end": "2025-12-01T00:00:00Z",
  "provider": "telegram"
}
```

---

Этот план охватывает стратегию, инструменты и реализацию для быстрой монетизации в Telegram с минимальным трением для пользователя и надёжной серверной проверкой доступа.