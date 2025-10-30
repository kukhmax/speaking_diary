from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, Plan, Subscription


class BillingService:
    """Сервис биллинга и подписок.

    Отвечает за:
    - Инициализацию базы и дефолтных планов.
    - Активацию триала и платной подписки.
    - Проверку активного доступа.
    - Получение статуса подписки.
    """

    def __init__(self, engine=None):
        """Инициализирует сервис.

        Параметры:
        - engine: SQLAlchemy Engine, если не передан — создаётся in-memory SQLite.
        """
        self.engine = engine or create_engine('sqlite:///:memory:')
        # Создаём таблицы по моделям модуля
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._ensure_default_plans()

    def _ensure_default_plans(self):
        """Гарантирует наличие базовых тарифов (trial, pro_monthly)."""
        s = self.Session()
        # Добавляем триал-план, если отсутствует
        if not s.query(Plan).filter_by(code='trial').first():
            s.add(Plan(code='trial', price_cents=0, currency='USD', quota_minutes=300))
        # Добавляем платный месячный план, если отсутствует
        if not s.query(Plan).filter_by(code='pro_monthly').first():
            s.add(Plan(code='pro_monthly', price_cents=300, currency='USD', quota_minutes=10000))
        s.commit()
        s.close()

    def activate_trial(self, user_id: int):
        """Активирует 7-дневный триал для пользователя.

        Возвращает: объект Subscription (после коммита).
        Если подписка уже существует — просто возвращает её.
        """
        s = self.Session()
        sub = s.query(Subscription).filter_by(user_id=user_id).first()
        if sub:
            s.close()
            return sub
        # Создаём новую активную подписку триала
        sub = Subscription(
            user_id=user_id,
            plan_code='trial',
            status='active',
            provider='internal',
            started_at=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=7),
        )
        s.add(sub)
        s.commit()
        s.refresh(sub)  # Получаем актуальные поля после коммита
        s.close()
        return sub

    def activate_subscription(
        self,
        user_id: int,
        plan_code: str,
        provider: str,
        external_id: str | None = None,
        period_days: int = 30,
    ):
        """Активирует платную подписку на указанный период.

        Параметры:
        - user_id: идентификатор пользователя
        - plan_code: код плана (например, 'pro_monthly')
        - provider: источник оплаты ('telegram', 'stripe', 'internal')
        - external_id: внешний идентификатор платежа/подписки
        - period_days: длительность периода в днях (по умолчанию 30)
        """
        s = self.Session()
        sub = s.query(Subscription).filter_by(user_id=user_id).first()
        if not sub:
            sub = Subscription(user_id=user_id)
            s.add(sub)
        # Обновляем параметры подписки
        sub.plan_code = plan_code
        sub.status = 'active'
        sub.provider = provider
        sub.started_at = datetime.utcnow()
        sub.current_period_end = datetime.utcnow() + timedelta(days=period_days)
        sub.external_id = external_id
        s.commit()
        s.refresh(sub)
        s.close()
        return sub

    def has_active_access(self, user_id: int) -> bool:
        """Проверяет, есть ли у пользователя активный доступ.

        Логика: активная подписка и дата окончания позже текущего момента.
        """
        s = self.Session()
        sub = s.query(Subscription).filter_by(user_id=user_id).first()
        s.close()
        if not sub:
            return False
        if sub.status != 'active':
            return False
        return bool(sub.current_period_end and sub.current_period_end > datetime.utcnow())

    def get_subscription_status(self, user_id: int) -> dict:
        """Возвращает статус подписки пользователя в виде словаря."""
        s = self.Session()
        sub = s.query(Subscription).filter_by(user_id=user_id).first()
        s.close()
        if not sub:
            return {'status': 'none'}
        return {
            'status': sub.status,
            'plan_code': sub.plan_code,
            'current_period_end': sub.current_period_end.isoformat() if sub.current_period_end else None,
            'provider': sub.provider,
        }