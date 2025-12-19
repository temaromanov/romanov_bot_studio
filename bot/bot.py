from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, DB_PATH
from bot.db.repository import init_db
from bot.handlers import lead_flow, pages, portfolio, services, start
from bot.handlers.debug_file_id import router as debug_file_id_router


async def run_bot() -> None:
    # aiogram>=3.7: parse_mode через DefaultBotProperties
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # init DB before polling (SPEC)
    await init_db(DB_PATH)

    # routers
    dp.include_router(start.router)
    dp.include_router(pages.router)
    dp.include_router(services.router)
    dp.include_router(portfolio.router)
    dp.include_router(lead_flow.router)
    dp.include_router(debug_file_id_router)

    await dp.start_polling(bot)
