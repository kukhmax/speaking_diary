import os
from sqlalchemy import create_engine


def get_db_engine_from_env():
    """Создаёт SQLAlchemy Engine из переменных окружения.

    Использует `BILLING_DATABASE_URL`. Если переменная не задана,
    создаёт локальный файл SQLite (`billing.db`) для изолированных тестов.
    """
    url = os.getenv('BILLING_DATABASE_URL', '').strip()
    if not url:
        # По умолчанию — локальный SQLite файл для изолированных тестов
        url = 'sqlite:///./billing.db'
    return create_engine(url)


class BillingConfig:
    """Конфигурация провайдеров платежей и публичных URL.

    Считывает значения из переменных окружения для использования в модуле.
    """
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    PAYMENTS_PROVIDER_TOKEN = os.getenv('PAYMENTS_PROVIDER_TOKEN', '')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_PRICE_ID = os.getenv('STRIPE_PRICE_ID', '')
    PUBLIC_WEBAPP_URL = os.getenv('PUBLIC_WEBAPP_URL', 'http://localhost:3000')