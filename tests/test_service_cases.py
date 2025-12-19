from __future__ import annotations

import json

import aiosqlite
import pytest

from bot.db.repository import save_files, save_lead
from bot.services.leads import format_admin_message, prepare_lead_data


@pytest.mark.asyncio
async def test_model3d_lead_with_required_file_and_description(inited_db):
    db_path = inited_db

    lead = prepare_lead_data(
        tg_user_id=100,
        tg_username="artist",
        tg_full_name="3D Художник",
        service="🎨 3D-модели по рисункам",
        task="Робот по эскизу",
        deadline_key="week",
        deadline_custom_text=None,
        budget=None,
        contact="@artist",
        extra={"caption": "эскиз в приложении"},
    )

    lead_id = await save_lead(
        db_path,
        tg_user_id=lead["tg_user_id"],
        tg_username=lead["tg_username"],
        tg_full_name=lead["tg_full_name"],
        service=lead["service"],
        task=lead["task"],
        deadline=lead["deadline"],
        budget=lead["budget"],
        contact=lead["contact"],
        extra_json=lead["extra_json"],
    )

    files = [{"file_type": "document", "file_id": "FILE123"}]
    await save_files(db_path, lead_id=lead_id, files=files)

    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute(
            "SELECT service, deadline, extra_json FROM leads WHERE id=?", (lead_id,)
        ) as cur:
            lead_row = await cur.fetchone()
        async with db.execute(
            "SELECT lead_id, file_type, file_id FROM lead_files WHERE lead_id=?", (lead_id,)
        ) as cur:
            file_rows = await cur.fetchall()

    assert lead_row[0] == "🎨 3D-модели по рисункам"
    assert lead_row[1] == "В течение недели"
    assert json.loads(lead_row[2])["caption"] == "эскиз в приложении"
    assert file_rows == [(lead_id, "document", "FILE123")]

    admin_text = format_admin_message(lead, files)
    assert "Файлы:" in admin_text
    assert "- document: FILE123" in admin_text


@pytest.mark.asyncio
async def test_restoration_lead_without_files_keeps_rest_type(inited_db):
    db_path = inited_db

    lead = prepare_lead_data(
        tg_user_id=101,
        tg_username="restorer",
        tg_full_name="Реставратор",
        service="Реставрация фото/видео",
        task="Цветокор и шумоподавление",
        deadline_key="not_urgent",
        deadline_custom_text=None,
        budget=None,
        contact="@restorer",
        extra={"rest_type": "Фото"},
    )

    lead_id = await save_lead(
        db_path,
        tg_user_id=lead["tg_user_id"],
        tg_username=lead["tg_username"],
        tg_full_name=lead["tg_full_name"],
        service=lead["service"],
        task=lead["task"],
        deadline=lead["deadline"],
        budget=lead["budget"],
        contact=lead["contact"],
        extra_json=lead["extra_json"],
    )

    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute(
            "SELECT service, deadline, extra_json FROM leads WHERE id=?", (lead_id,)
        ) as cur:
            lead_row = await cur.fetchone()
        async with db.execute(
            "SELECT COUNT(*) FROM lead_files WHERE lead_id=?", (lead_id,)
        ) as cur:
            files_count = await cur.fetchone()

    assert lead_row[0] == "Реставрация фото/видео"
    assert lead_row[1] == "Не срочно"
    assert json.loads(lead_row[2])["rest_type"] == "Фото"
    assert files_count[0] == 0

    admin_text = format_admin_message(lead, files=None)
    assert "Файлы:" not in admin_text


@pytest.mark.asyncio
async def test_neuro_lead_fixed_budget_and_admin_fields(inited_db):
    db_path = inited_db

    lead = prepare_lead_data(
        tg_user_id=102,
        tg_username="neurofan",
        tg_full_name="Нейро Клиент",
        service="Нейрофотосессия",
        task="Деловой стиль, тёплый свет",
        deadline_key="urgent",
        deadline_custom_text=None,
        budget="2500 ₽",
        contact="@neurofan",
        extra={"wishes": "Деловой стиль, тёплый свет"},
    )

    lead_id = await save_lead(
        db_path,
        tg_user_id=lead["tg_user_id"],
        tg_username=lead["tg_username"],
        tg_full_name=lead["tg_full_name"],
        service=lead["service"],
        task=lead["task"],
        deadline=lead["deadline"],
        budget=lead["budget"],
        contact=lead["contact"],
        extra_json=lead["extra_json"],
    )

    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute(
            "SELECT service, deadline, budget, extra_json FROM leads WHERE id=?",
            (lead_id,),
        ) as cur:
            lead_row = await cur.fetchone()

    assert lead_row[0] == "Нейрофотосессия"
    assert lead_row[1] == "Срочно"
    assert lead_row[2] == "2500 ₽"
    assert json.loads(lead_row[3])["wishes"] == "Деловой стиль, тёплый свет"

    admin_text = format_admin_message(lead, files=None)
    assert "Бюджет: 2500 ₽" in admin_text
    assert "Файлы:" not in admin_text
