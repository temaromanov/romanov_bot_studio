from __future__ import annotations

import json

import aiosqlite
import pytest

from bot.db.repository import save_files, save_lead
from bot.services.leads import format_admin_message, map_deadline, prepare_lead_data


@pytest.mark.asyncio
async def test_deadline_mapping():
    assert map_deadline("urgent") == "Срочно"
    assert map_deadline("week") == "В течение недели"
    assert map_deadline("not_urgent") == "Не срочно"
    assert map_deadline("custom", "к пятнице") == "к пятнице"
    # допускаем старый формат с префиксом
    assert map_deadline("deadline:urgent") == "Срочно"


@pytest.mark.asyncio
async def test_save_lead_and_files_and_format_message(inited_db):
    db_path = inited_db

    lead = prepare_lead_data(
        tg_user_id=123,
        tg_username="romanov",
        tg_full_name="Артём Романов",
        service="Нейрофотосессия",
        task="Стиль: бизнес, тёплый свет",
        deadline_key="urgent",
        deadline_custom_text=None,
        budget="Фикс",
        contact="@romanov",
        extra={"note": "test"},
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
    assert isinstance(lead_id, int) and lead_id > 0

    files = [
        {"file_type": "photo", "file_id": "AAA111"},
        {"file_type": "video", "file_id": "BBB222"},
    ]
    await save_files(db_path, lead_id=lead_id, files=files)

    # verify saved rows
    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute("SELECT service, deadline, extra_json FROM leads WHERE id=?", (lead_id,)) as cur:
            row = await cur.fetchone()
        assert row is not None
        assert row[0] == "Нейрофотосессия"
        assert row[1] == "Срочно"
        assert json.loads(row[2])["note"] == "test"

        async with db.execute("SELECT file_type, file_id FROM lead_files WHERE lead_id=? ORDER BY id", (lead_id,)) as cur:
            saved_files = await cur.fetchall()
        assert saved_files == [("photo", "AAA111"), ("video", "BBB222")]

    text = format_admin_message(lead, files)
    assert "🆕 Новая заявка" in text
    assert "От: Артём Романов (@romanov)" in text
    assert "Услуга: Нейрофотосессия" in text
    assert "Срок: Срочно" in text
    assert "Файлы:" in text
    assert "- photo: AAA111" in text
