from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    choosing_service = State()

    # общий поток
    task = State()
    deadline = State()
    deadline_custom = State()
    contact = State()
    confirm = State()

    # сценарий "Реставрация фото/видео" + файлы
    rest_type = State()
    files = State()
