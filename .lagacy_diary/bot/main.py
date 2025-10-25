import os
from typing import Optional, Tuple

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Это AI Voice Diary. Отправь голосовое сообщение, чтобы начать."
    )


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    await message.answer("pong")


def load_bot_token(dotenv_path: Optional[str] = None) -> Optional[str]:
    """Загружает BOT_TOKEN из .env или окружения.

    Если dotenv_path указан, загружает переменные из указанного файла.
    """
    load_dotenv(dotenv_path=dotenv_path)
    return os.getenv("BOT_TOKEN")


def create_bot_and_dp(token: str) -> Tuple[Bot, Dispatcher]:
    """Создаёт экземпляры Bot и Dispatcher и подключает router."""
    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)
    return bot, dp


async def main():
    token = load_bot_token()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN не найден. Укажи его в .env или переменных окружения."
        )
    bot, dp = create_bot_and_dp(token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())