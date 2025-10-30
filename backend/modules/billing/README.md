# Billing Module

- Самодостаточный модуль подписок и биллинга.
- Поддержка: триал, платные планы, квоты, провайдеры платежей.

## Структура
- `__init__.py` — инициалиация, фабрика Blueprint.
- `models.py` — SQLAlchemy модели: Plan, Subscription, Payment, Usage.
- `service.py` — бизнес-логика: триал, активация, проверка доступа, квоты.
- `providers/telegram.py` — заглушка Telegram Payments.
- `providers/stripe.py` — заглушка Stripe Checkout.
- `tests/` — pytest-тесты основных сценариев.
- `requirements.txt` — зависимости модуля.
- `Dockerfile` и `docker-compose.yml` — изолированный запуск.
- `.env.example` — пример конфигурации.

## Быстрая интеграция
```python
from backend.modules.billing import create_billing_blueprint

bp = create_billing_blueprint(engine=db_engine)
app.register_blueprint(bp, url_prefix='/api/billing')
```

## Запуск локально
```bash
cd backend/modules/billing
cp .env.example .env
docker-compose up --build -d
curl http://localhost:5080/health
```

## Тесты
```bash
cd backend/modules/billing
pip install -r requirements.txt
pytest -q
```