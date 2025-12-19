from __future__ import annotations

from aiogram.types import Message

from bot.keyboards.main import main_menu_kb
from bot.texts.common import LEAD_SUCCESS_TEXT


async def send_lead_success(message: Message) -> None:
    # Единая точка финального ответа после успешной отправки заявки (для всех сценариев).
    await message.answer(LEAD_SUCCESS_TEXT)
    await message.answer("Главное меню 👇", reply_markup=main_menu_kb())
