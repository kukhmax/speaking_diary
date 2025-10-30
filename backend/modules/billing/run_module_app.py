import os
from flask import Flask
from . import create_billing_blueprint
from .config import get_db_engine_from_env


def create_app():
    """Создаёт минимальное Flask-приложение для изолированного запуска модуля."""
    app = Flask(__name__)
    engine = get_db_engine_from_env()
    bp = create_billing_blueprint(engine)
    app.register_blueprint(bp)
    return app


if __name__ == '__main__':
    # Позволяет запускать модуль как самостоятельный сервис (локально или в Docker)
    app = create_app()
    port = int(os.getenv('PORT', '5080'))
    app.run(host='0.0.0.0', port=port)