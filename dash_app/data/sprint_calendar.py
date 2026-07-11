"""Календарь спринта 11-17.07.2026 (ПМ-краш: недели × Deliverables, здесь дни × эпики).

Источник правды по составу — CLAUDE.md «Календарь спринта до 17 июля».
Актуализируем ОБА при изменениях (договорённость установочной встречи).
Статусы задач НЕ дублируются здесь — подтягиваются из jira_mock_raw по ключу,
поэтому «обход» (зелёный/жёлтый/красный) частично автоматический:
Done → зелёный, In Progress → жёлтый, To Do в прошедшем дне → красный.
"""
from __future__ import annotations

from datetime import date

# Дни спринта: дата, подпись, этап продуктового процесса, фокус дня
SPRINT_DAYS: list[dict] = [
    {"date": date(2026, 7, 11), "label": "Сб 11", "stage": "Инфра + токены",
     "focus": "MCP + дизайн-система"},
    {"date": date(2026, 7, 12), "label": "Вс 12 🎵", "stage": "Define: легенда",
     "focus": "История команды + Goals + сценарий комикса"},
    {"date": date(2026, 7, 13), "label": "Пн 13", "stage": "Define: артефакты",
     "focus": "Персоны, Journey Map, HMW + деплой"},
    {"date": date(2026, 7, 14), "label": "Вт 14", "stage": "Develop: flows",
     "focus": "User Flow + wireframes + иерархия в коде"},
    {"date": date(2026, 7, 15), "label": "Ср 15", "stage": "Develop: hi-fi",
     "focus": "Figma-артефакты + комикс"},
    {"date": date(2026, 7, 16), "label": "Чт 16", "stage": "Deliver: сборка",
     "focus": "Design tab + Framer"},
    {"date": date(2026, 7, 17), "label": "Пт 17", "stage": "🚀 Публикация",
     "focus": "Публикация + отклик Muse"},
]

# Строки = бизнес-эпики, ячейки = ключи задач по дням (индекс = позиция в SPRINT_DAYS)
SPRINT_ROWS: list[dict] = [
    {"name": "1. Дизайн-процесс", "epic": "DASH-EPIC-9", "cells": [
        ["DASH-61", "DASH-92"], [], ["DASH-57", "DASH-58"],
        ["DASH-59", "DASH-62", "DASH-93"], ["DASH-63", "DASH-94"], ["DASH-60"], [],
    ]},
    {"name": "2. Живая команда", "epic": "DASH-EPIC-10", "cells": [
        ["DASH-95", "DASH-116"], ["DASH-96"], ["DASH-97", "DASH-98", "DASH-99"],
        [], [], [], [],
    ]},
    {"name": "3. Зритель понимает", "epic": "DASH-EPIC-11", "cells": [
        [], ["DASH-100"], [], [], ["DASH-101"], ["DASH-102"], [],
    ]},
    {"name": "4. Опубликован", "epic": "DASH-EPIC-12", "cells": [
        ["DASH-90"], [], ["DASH-103"], [], ["DASH-104"], ["DASH-105", "DASH-106"],
        ["DASH-107"],
    ]},
]

# Промежуточные дедлайны (⏰ на чипе задачи)
DEADLINE_KEYS: set[str] = {"DASH-63", "DASH-103", "DASH-102", "DASH-106", "DASH-107"}

# Инвариант: у каждой строки ровно столько ячеек, сколько дней — иначе zip()
# в _sprint_calendar молча обрежет и чипы задач исчезнут без ошибки.
for _row in SPRINT_ROWS:
    assert len(_row["cells"]) == len(SPRINT_DAYS), (
        f"SPRINT_ROWS[{_row['name']!r}] имеет {len(_row['cells'])} ячеек, "
        f"ожидалось {len(SPRINT_DAYS)} (по числу дней)"
    )
