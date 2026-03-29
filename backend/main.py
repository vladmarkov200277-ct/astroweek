"""
Точка входа: запускает FastAPI-сервер и Telegram-бота одновременно.
"""

import asyncio
import logging
import uvicorn

from bot import run_bot
from server import app
from config import API_HOST, API_PORT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run_server():
    config = uvicorn.Config(
        app=app,
        host=API_HOST,
        port=API_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    logger.info(f"Starting AstroWeek on {API_HOST}:{API_PORT}")
    await asyncio.gather(
        run_server(),
        run_bot(),
    )


if __name__ == "__main__":
    asyncio.run(main())
