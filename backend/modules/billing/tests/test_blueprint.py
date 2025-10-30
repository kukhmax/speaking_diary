from flask.testing import FlaskClient
from backend.modules.billing.run_module_app import create_app


def test_health_endpoint():
    """Эндпоинт /health должен возвращать ok: true."""
    app = create_app()
    client: FlaskClient = app.test_client()
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json()['ok'] is True


def test_activate_trial_and_status():
    """Активация триала и чтение статуса по user_id должны работать корректно."""
    app = create_app()
    client: FlaskClient = app.test_client()
    # Активируем триал для пользователя 42
    r = client.post('/activate-trial', json={'user_id': 42})
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert j['subscription']['status'] == 'active'
    # Проверяем статус подписки
    r2 = client.get('/status?user_id=42')
    assert r2.status_code == 200
    j2 = r2.get_json()
    assert j2['status'] == 'active'