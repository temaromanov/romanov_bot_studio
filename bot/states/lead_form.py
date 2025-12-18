from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    choosing_service = State()
    task = State()
    deadline = State()
    deadline_custom = State()
    contact = State()
    confirm = State()
