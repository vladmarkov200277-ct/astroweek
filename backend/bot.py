"""
Telegram-бот на aiogram 3.x.
Отвечает на /start и открывает Mini App по кнопке.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    BotCommand,
)

from config import BOT_TOKEN, WEBAPP_URL

logger = logging.getLogger(__name__)

router = Router()


# ─── /start ──────────────────────────────────────────────────────────────────

WELCOME_TEXT = (
    "✨ <b>Добро пожаловать в AstroWeek</b> от <a href='https://t.me/BLONDY_club'>@BLONDY_club</a>\n\n"
    "Получите персональный астрологический прогноз на неделю "
    "на основе вашей натальной карты.\n\n"
    "Для этого нажмите кнопку ниже 👇"
)


def make_webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔮 Открыть AstroWeek",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}/app"),
        )
    ]])


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=make_webapp_keyboard(),
        disable_web_page_preview=True,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Как пользоваться AstroWeek:</b>\n\n"
        "1. Нажмите /start\n"
        "2. Откройте приложение через кнопку\n"
        "3. Введите дату, время рождения и город\n"
        "4. Получите прогноз на текущую неделю\n\n"
        "Прогноз строится на основе вашей натальной карты "
        "и текущего положения планет.",
        parse_mode="HTML",
    )


# ─── Запуск бота ─────────────────────────────────────────────────────────────

async def setup_bot_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить AstroWeek"),
        BotCommand(command="help", description="Помощь"),
    ])


async def run_bot():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в .env")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await setup_bot_commands(bot)
    logger.info("Bot started")

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_bot())
