"""Discover tab (dash-mode only) — Double Diamond, этап 1.

Часть DASH-60. Отвечает на 3 вопроса Discovery про предметную область (как устроены
реальные продуктовые команды), а не про наш конкретный дашборд:
  Q1 — кто с кем взаимодействует (состав команды, desk research по источникам);
  Q2 — что передаётся и в какой последовательности (схема этапов + карта обмена артефактами);
  Q3 — где стыки, что теряется/тормозит (проблемы взаимодействия — в работе).
Функции-рендереры воркбенча/артефактов физически в motif_about.py (техдолг DASH-138).
"""

import reflex as rx

from ..tokens import SPACING, PAGE_MAX_WIDTH, BORDER
from ..components import section_header
from .motif_about import _artifacts_block, _placeholder
from ..data.discover_problems import AXIS_A_BLOCKS, GOAL_TYPE_COLOR

_MAX = PAGE_MAX_WIDTH


# ---------------------------------------------------------------------------
# Q3 — проблемы взаимодействия (таблицы с расслоением по этапам DD).
# Колонки помечены этапом (п2); «цель» тегнута типом design-intent (п3).
# Источник контента — wiki/interaction_problems_research.md. ⚠️ team/рекрутер на чекап.
# ---------------------------------------------------------------------------

def _goal_cell(goal: str, goal_type: str) -> rx.Component:
    return rx.table.cell(
        rx.badge(goal_type, color_scheme=GOAL_TYPE_COLOR.get(goal_type, "gray"),
                 variant="soft", size="1", margin_bottom="4px"),
        rx.text(goal, size="1", color=rx.color("gray", 11), line_height="1.5"),
        vertical_align="top",
    )


def _rec_cell(obs: str, self_: str) -> rx.Component:
    return rx.table.cell(
        rx.flex(
            rx.text("🔍 ", size="1"),
            rx.text(obs, size="1", color=rx.color("gray", 11), line_height="1.5"),
            gap="2px",
        ),
        rx.flex(
            rx.text("👤 ", size="1"),
            rx.text(self_, size="1",
                    color=rx.color("gray", 9) if self_ == "N/A" else rx.color("gray", 11),
                    line_height="1.5"),
            gap="2px", margin_top="2px",
        ),
        vertical_align="top",
    )


def _problem_block(block: dict) -> rx.Component:
    header = rx.table.row(
        rx.table.column_header_cell(
            rx.text("Проблема ", size="1", weight="bold"),
            rx.text("Discover", size="1", color=rx.color("gray", 8)),
            width="26%"),
        rx.table.column_header_cell(
            rx.text("Цель ", size="1", weight="bold"),
            rx.text("Define", size="1", color=rx.color("gray", 8)),
            width="26%"),
        rx.table.column_header_cell(
            rx.text("Как учтено (команда) ", size="1", weight="bold"),
            rx.text("Develop · ⚠️ чекап", size="1", color=rx.color("amber", 9)),
            width="26%"),
        rx.table.column_header_cell(
            rx.text("Рекрутер ", size="1", weight="bold"),
            rx.text("наблюдатель / сам", size="1", color=rx.color("gray", 8)),
            width="22%"),
    )
    rows = [
        rx.table.row(
            rx.table.cell(rx.text(r["label"], size="1", color=rx.color("gray", 12),
                                  line_height="1.5"), vertical_align="top"),
            _goal_cell(r["goal"], r["goal_type"]),
            rx.table.cell(rx.text(r["team"], size="1", color=rx.color("gray", 11),
                                  line_height="1.5"), vertical_align="top"),
            _rec_cell(r["rec_obs"], r["rec_self"]),
        )
        for r in block["rows"]
    ]
    return rx.box(
        rx.flex(
            rx.text(block["source"], size="2", weight="bold", color=rx.color("gray", 12)),
            rx.link("источник ↗", href=block["url"], is_external=True,
                    size="1", color=rx.color("teal", 10)),
            gap="8px", align="baseline", margin_bottom="4px",
        ),
        rx.text(block["problem"], size="1", color=rx.color("gray", 10),
                line_height="1.6", margin_bottom="4px", font_style="italic"),
        rx.text(block["note"], size="1", color=rx.color("gray", 9), margin_bottom="8px")
        if block["note"] else rx.fragment(),
        rx.table.root(
            rx.table.header(header),
            rx.table.body(*rows),
            variant="surface", size="1", width="100%",
        ),
        margin_bottom=SPACING["xl"],
    )


def _problems_section() -> rx.Component:
    return rx.box(
        rx.text("Проблемы взаимодействия (Q3)", size="4", weight="bold",
                color=rx.color("gray", 12), margin_bottom="4px"),
        rx.text("Расслоено по этапам DD: Проблема (Discover) · Цель+тип (Define) · "
                "Как учтено (Develop) · Рекрутер (meta). ⚠️ колонки «команда»/«рекрутер» — на чекап "
                "(писались по догадке); проблема-цитаты и цели выверены. Источники — verbatim, verified.",
                size="1", color=rx.color("gray", 9), margin_bottom=SPACING["md"], line_height="1.6"),
        rx.text("Ось A · дашборд как продукт", size="2", weight="bold",
                color=rx.color("teal", 11), margin_bottom="8px"),
        *[_problem_block(b) for b in AXIS_A_BLOCKS],
    )


# ---------------------------------------------------------------------------
# Q2 — последовательность этапов процесса + исполнители + что передаётся дальше.
# Grounded: stage_order сквадов (канонический порядок продукта) + привязка ролей
# к вкладкам из USER_STORIES. Синтез desk research (SDLC: Atlassian/Scrum + карта
# ролей), НЕ наблюдение за конкретной живой командой — подаём честно как модель.
# Порядок строго по stage_order (решение Guzel 20.07): Architecture перед Analysis.
# ---------------------------------------------------------------------------

_PROCESS_STAGES: list[dict] = [
    {"n": 1, "stage": "Discovery", "icon": "search", "accent": "teal",
     "roles": ["UX Researcher", "Product Analyst"],
     "hands_off": "инсайты, персоны, JTBD, метрики"},
    {"n": 2, "stage": "Architecture", "icon": "git-branch", "accent": "blue",
     "roles": ["Tech Lead", "DevOps Engineer"],
     "hands_off": "ADR, тех-ограничения, API-дизайн"},
    {"n": 3, "stage": "Definition", "icon": "file-text", "accent": "cyan",
     "roles": ["Business Analyst", "Systems Analyst"],
     "hands_off": "требования, use-cases, ERD/API-контракты"},
    {"n": 4, "stage": "Design", "icon": "pen-tool", "accent": "iris",
     "roles": ["Product Designer"],
     "hands_off": "user flows, wireframes, hi-fi, кликабельные прототипы, токены"},
    {"n": 5, "stage": "Development", "icon": "file-code-2", "accent": "violet",
     "roles": ["Developers (FE/BE)", "DevOps Engineer"],
     "hands_off": "рабочий софт, pull requests"},
    {"n": 6, "stage": "Quality", "icon": "shield-check", "accent": "grass",
     "roles": ["QA Engineer"],
     "hands_off": "верифицированная сборка, дефекты"},
    {"n": 7, "stage": "Release", "icon": "package", "accent": "amber",
     "roles": ["Technical Writer", "Release Manager"],
     "hands_off": "инструкции, доки, release notes, деплой"},
    {"n": 8, "stage": "Operate", "icon": "activity", "accent": "orange",
     "roles": ["Support Engineer"],
     "hands_off": "баги, обращения → петля обратно в Discovery"},
]

_GROWTH_STAGE: dict = {
    "stage": "Growth", "icon": "trending-up", "accent": "pink",
    "roles": ["Growth PM (Marketing + Sales)"],
    "note": "непрерывно и параллельно всему процессу: эксперименты, A/B, воронки",
}

_SPANNING_ROLES: list[dict] = [
    {"role": "PM · кросс-функциональный", "note": "координирует все этапы, держит ритм и приоритеты"},
    {"role": "Product Owner / Заказчик", "note": "даёт Goals/приоритеты на вход, принимает результат"},
]


def _role_badge(role: str, accent: str = "gray") -> rx.Component:
    return rx.badge(role, color_scheme=accent, variant="soft", size="1")


def _num_dot(n: int, accent: str) -> rx.Component:
    return rx.flex(
        rx.text(str(n), size="2", weight="bold", color="white"),
        width="28px", height="28px", flex_shrink="0",
        align="center", justify="center",
        background=rx.color(accent, 9),
        border_radius="var(--radius-full)",
    )


def _stage_card(s: dict) -> rx.Component:
    return rx.flex(
        _num_dot(s["n"], s["accent"]),
        rx.box(
            rx.flex(
                rx.icon(s["icon"], size=16, color=rx.color(s["accent"], 11)),
                rx.text(s["stage"], size="3", weight="bold", color=rx.color("gray", 12)),
                gap="6px", align="center", margin_bottom="6px",
            ),
            rx.flex(*[_role_badge(r, s["accent"]) for r in s["roles"]],
                    gap="4px", wrap="wrap", margin_bottom="6px"),
            rx.flex(
                rx.text("→ передаёт:", size="1", weight="medium", color=rx.color(s["accent"], 11)),
                rx.text(s["hands_off"], size="1", color=rx.color("gray", 11)),
                gap="4px", align="baseline", wrap="wrap",
            ),
            flex="1",
        ),
        gap=SPACING["md"], align="start",
        padding=SPACING["md"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color(s['accent'], 4)}",
        border_left=f"3px solid {rx.color(s['accent'], 8)}",
        border_radius="var(--radius-3)",
        width="100%",
    )


def _connector() -> rx.Component:
    return rx.flex(
        rx.icon("chevron-down", size=16, color=rx.color("gray", 7)),
        justify="center", width="100%", padding_y="2px",
    )


def _process_flow_block() -> rx.Component:
    steps = []
    for i, s in enumerate(_PROCESS_STAGES):
        steps.append(_stage_card(s))
        if i < len(_PROCESS_STAGES) - 1:
            steps.append(_connector())

    growth = rx.flex(
        rx.icon(_GROWTH_STAGE["icon"], size=16, color=rx.color(_GROWTH_STAGE["accent"], 11)),
        rx.box(
            rx.flex(
                rx.text(_GROWTH_STAGE["stage"], size="2", weight="bold", color=rx.color("gray", 12)),
                _role_badge(_GROWTH_STAGE["roles"][0], _GROWTH_STAGE["accent"]),
                gap="6px", align="center", wrap="wrap", margin_bottom="4px",
            ),
            rx.text(_GROWTH_STAGE["note"], size="1", color=rx.color("gray", 10)),
            flex="1",
        ),
        gap=SPACING["md"], align="center",
        padding=SPACING["md"],
        background=rx.color(_GROWTH_STAGE["accent"], 2),
        border=f"{BORDER} {rx.color(_GROWTH_STAGE['accent'], 5)}",
        border_radius="var(--radius-3)",
        border_style="dashed",
        width="100%",
    )

    spanning = rx.box(
        rx.text("Сквозные роли (над всеми этапами)", size="1", weight="bold",
                color=rx.color("gray", 11), margin_bottom="6px"),
        *[
            rx.flex(
                _role_badge(r["role"], "gray"),
                rx.text(r["note"], size="1", color=rx.color("gray", 10)),
                gap="8px", align="center", margin_bottom="4px", wrap="wrap",
            )
            for r in _SPANNING_ROLES
        ],
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
    )

    return rx.box(
        rx.text(
            "Последовательность этапов, исполнители и что передаётся дальше. "
            "Модель типового продуктового процесса (синтез desk research: SDLC-практики "
            "Atlassian/Scrum + карта ролей) — не наблюдение за конкретной командой.",
            size="1", color=rx.color("gray", 9), margin_bottom=SPACING["md"], line_height="1.6",
        ),
        rx.flex(*steps, direction="column", gap="0", width="100%"),
        rx.box(height=SPACING["md"]),
        growth,
        rx.box(height=SPACING["md"]),
        spanning,
    )


def dash_discover_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Discover",
            subtitle="Double Diamond · этап 1 — как устроено взаимодействие в продуктовой команде",
        ),

        # Q2 — последовательность этапов
        rx.text("Процесс: этапы и передачи", size="4", weight="bold",
                color=rx.color("gray", 12), margin_bottom="8px"),
        _process_flow_block(),
        rx.box(height=SPACING["xl"]),

        # Q2 — карта обмена артефактами (compact-вариант: роли без имён персонажей)
        _artifacts_block(compact=True),
        rx.box(height=SPACING["xl"]),

        # Q3 — проблемы взаимодействия (таблицы с расслоением по этапам DD)
        _problems_section(),
        rx.box(height=SPACING["xl"]),

        # Ещё в работе (Q1 состав команды с источниками, Ось B проблем, конкурентный анализ)
        _placeholder(
            "Ещё для Discover: состав команды по источникам (Q1), Ось B проблем (стыки ролей — "
            "Actuation/Figma/Miro/Uplevel/Figr), конкурентный анализ (DASH-94) — в работе.",
        ),

        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
