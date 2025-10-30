from backend.modules.billing.service import BillingService


def test_trial_activation_and_access():
    """Проверяет, что триал активируется и даёт активный доступ."""
    svc = BillingService()
    svc.activate_trial(user_id=1)
    assert svc.has_active_access(1) is True


def test_subscription_expiration():
    """Проверяет, что подписка с нулевой длительностью не даёт активного доступа."""
    svc = BillingService()
    svc.activate_subscription(user_id=2, plan_code='pro_monthly', provider='telegram', period_days=0)
    assert svc.has_active_access(2) is False