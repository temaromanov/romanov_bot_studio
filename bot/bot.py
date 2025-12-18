from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, DB_PATH
from bot.db.repository import init_db
from bot.handlers.lead_flow import router as lead_flow_router
from bot.handlers.start import router as start_router


async def run_bot() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    # ВАЖНО: создать таблицы в SQLite (если их ещё нет)
    await init_db(DB_PATH)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(start_router)
    dp.include_router(lead_flow_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
