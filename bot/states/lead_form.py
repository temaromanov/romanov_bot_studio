from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class LeadForm(StatesGroup):
    choosing_service = State()

    # общий поток
    task = State()

    deadline = State()
    deadline_custom = State()

    # контакт (UX)
    contact_choice = State()
    contact_phone = State()
    contact_other = State()

    confirm = State()

    # сценарий "Реставрация фото/видео" + файлы
    rest_type = State()
    files = State()

    # сценарий "Нейрофотосессия" (инструкции -> пожелания)
    neuro_step1 = State()
    neuro_step2 = State()
    neuro_wishes = State()

    # сценарии услуг
    content_task = State()
    video_task = State()

    model3d_intro = State()
    model3d_wait_file = State()
    # NEW: если пользователь прислал файл без caption — просим описание отдельным сообщением
    model3d_desc = State()
