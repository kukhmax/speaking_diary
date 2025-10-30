from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Plan(Base):
    """Тарифный план: цена, валюта и квота использования."""

    __tablename__ = 'plans'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)           # Уникальный код плана (trial, pro_monthly)
    price_cents = Column(Integer)                # Цена в центах
    currency = Column(String)                    # Валюта (например, USD)
    quota_minutes = Column(Integer)              # Квота минут транскрибации


class Subscription(Base):
    """Подписка пользователя на конкретный план и её состояние."""

    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)                    # Идентификатор пользователя
    plan_code = Column(String)                   # Код плана, на который подписан
    status = Column(String)                      # Статус (active, canceled, expired)
    provider = Column(String)                    # Провайдер оплаты (telegram, stripe, internal)
    started_at = Column(DateTime)                # Дата начала текущего периода
    current_period_end = Column(DateTime)        # Дата окончания текущего периода
    external_id = Column(String)                 # Внешний ID (invoice/subscription)


class Payment(Base):
    """Платёж по подписке, включая сумму, валюту и статус."""

    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)                    # Пользователь, совершивший платёж
    provider = Column(String)                    # Провайдер (telegram, stripe)
    external_id = Column(String)                 # Внешний ID транзакции
    amount_cents = Column(Integer)               # Сумма в центах
    currency = Column(String)                    # Валюта платежа
    status = Column(String)                      # Статус (pending, paid, failed)
    paid_at = Column(DateTime)                   # Время подтверждения оплаты


class Usage(Base):
    """Учёт использования сервиса за период (минуты и записи)."""

    __tablename__ = 'usage'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)                    # Пользователь
    period_start = Column(DateTime)              # Начало периода учёта
    period_end = Column(DateTime)                # Конец периода учёта
    minutes_used = Column(Integer)               # Минуты, израсходованные за период
    entries_count = Column(Integer)              # Количество записей/запросов