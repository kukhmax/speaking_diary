from pathlib import Path
from aiogram import Bot, Dispatcher

from bot.main import load_bot_token, create_bot_and_dp


def test_create_bot_and_dp():
    token = "123456:ABCDEF"
    bot, dp = create_bot_and_dp(token)
    assert isinstance(bot, Bot)
    assert isinstance(dp, Dispatcher)


def test_load_bot_token_from_custom_env(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text("BOT_TOKEN=TEST_TOKEN\n", encoding="utf-8")
    token = load_bot_token(dotenv_path=str(env_path))
    assert token == "TEST_TOKEN"