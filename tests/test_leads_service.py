from __future__ import annotations

import json

import aiosqlite
import pytest

from bot.db.repository import save_files, save_lead
from bot.services.leads import format_admin_message, map_deadline, prepare_lead_data


@pytest.mark.parametrize(
    "deadline_key, custom_text, expected",
    [
        ("urgent", None, "Срочно"),
        ("week", None, "В течение недели"),
        ("not_urgent", None, "Не срочно"),
        ("custom", "к пятнице", "к пятнице"),
    ],
)
def test_map_deadline_supported_keys(deadline_key, custom_text, expected):
    assert map_deadline(deadline_key, custom_text) == expected


def test_map_deadline_legacy_prefix_supported():
    assert map_deadline("deadline:urgent") == "Срочно"
    assert map_deadline("deadline:not_urgent") == "Не срочно"


def test_map_deadline_unknown_value_safe_fallback():
    assert map_deadline("unknown") == "—"
    assert map_deadline("", "") == "—"


def test_format_admin_message_without_files():
    lead = {
        "tg_full_name": "Тест Пользователь",
        "tg_username": "tester",
        "service": "Разработка",
        "task": "Нужен лендинг",
        "deadline": "Срочно",
        "budget": "до 100k",
        "contact": "@tester",
    }

    text = format_admin_message(lead, files=None)

    # ключевые поля присутствуют
    assert "Услуга: Разработка" in text
    assert "Задача: Нужен лендинг" in text
    assert "Срок: Срочно" in text
    assert "Бюджет: до 100k" in text
    assert "Контакт: @tester" in text

    # блока с файлами быть не должно
    assert "Файлы:" not in text


def test_format_admin_message_with_files_block():
    lead = {
        "tg_full_name": "Тест Пользователь",
        "tg_username": "tester",
        "service": "Разработка",
        "task": "Нужен лендинг",
        "deadline": "Срочно",
        "budget": None,
        "contact": "@tester",
    }
    files = [
        {"file_type": "photo", "file_id": "AAA111"},
        {"file_type": "video", "file_id": "BBB222"},
    ]

    text = format_admin_message(lead, files)

    assert "Файлы:" in text
    assert "- photo: AAA111" in text
    assert "- video: BBB222" in text
    # ключевые поля всё равно присутствуют
    assert "Услуга: Разработка" in text
    assert "Задача: Нужен лендинг" in text
    assert "Контакт: @tester" in text


@pytest.mark.asyncio
async def test_save_lead_and_files_linked(inited_db):
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

    async with aiosqlite.connect(str(db_path)) as db:
        async with db.execute(
            "SELECT service, deadline, extra_json FROM leads WHERE id=?", (lead_id,)
        ) as cur:
            row = await cur.fetchone()
        assert row is not None
        assert row[0] == "Нейрофотосессия"
        assert row[1] == "Срочно"
        assert json.loads(row[2])["note"] == "test"

        async with db.execute(
            "SELECT lead_id, file_type, file_id FROM lead_files WHERE lead_id=? ORDER BY id",
            (lead_id,),
        ) as cur:
            saved_files = await cur.fetchall()
        assert saved_files == [
            (lead_id, "photo", "AAA111"),
            (lead_id, "video", "BBB222"),
        ]

    text = format_admin_message(lead, files)
    assert "Файлы:" in text
    assert "- photo: AAA111" in text
