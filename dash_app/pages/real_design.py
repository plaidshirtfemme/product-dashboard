"""Design tab — Real project mode.

Documents actual design decisions made for this dashboard.
Source: the dashboard codebase itself (tokens, components, navigation choices).
"""

import reflex as rx
from ..components import section_header, real_page_header, real_page_wrapper
from ..tokens import SPACING, BORDER


_DECISIONS = [
    {
        "id": "DD-001",
        "title": "Reflex вместо Streamlit",
        "category": "Framework",
        "rationale": (
            "Streamlit ограничен в кастомизации CSS и даёт характерный "
            "'streamlit look'. Reflex компилирует Python в React, "
            "даёт полный контроль над версткой и компонентами."
        ),
        "tradeoff": "Steeper learning curve; hot-reload медленнее чем у Streamlit.",
        "status": "accepted",
    },
    {
        "id": "DD-002",
        "title": "Radix Themes как UI-система",
        "category": "UI Library",
        "rationale": (
            "Radix предоставляет семантические токены цвета (gray-1..12, teal-9), "
            "доступные компоненты (Badge, Callout, DropdownMenu) и "
            "автоматическую тёмную тему без написания CSS вручную."
        ),
        "tradeoff": "Меньше контроля над деталями чем при pure CSS; нет кастомных шрифтов.",
        "status": "accepted",
    },
    {
        "id": "DD-003",
        "title": "Teal как primary action color",
        "category": "Color System",
        "rationale": (
            "Teal достаточно нейтрален чтобы не ассоциироваться с конкретным "
            "продуктом (не GitHub-зелёный, не Jira-синий). "
            "Семантика: активная вкладка, 'good' тренд, real-project badge."
        ),
        "tradeoff": "Amber = warning/demo, Red = danger, Gray = нейтральное. "
                    "Цвет несёт смысл — нельзя использовать декоративно.",
        "status": "accepted",
    },
    {
        "id": "DD-004",
        "title": "Sidebar + tabs nav с бургером",
        "category": "Navigation",
        "rationale": (
            "15 вкладок не помещаются в горизонтальный таб-бар на стандартном экране. "
            "Sidebar даёт место для label + icon и переключатель проекта. "
            "Бургер позволяет переключиться на таб-режим при необходимости."
        ),
        "tradeoff": "Sidebar занимает 220px ширины; на узких экранах некомфортно.",
        "status": "accepted",
    },
    {
        "id": "DD-005",
        "title": "Project mode dropdown вместо глобального фильтра",
        "category": "UX Pattern",
        "rationale": (
            "Real/Demo — это смена контекста данных, не фильтр по атрибуту. "
            "Dropdown в шапке сайдбара (как workspace switcher в Notion/Linear) "
            "даёт понятный mental model: 'я смотрю на другой проект'."
        ),
        "tradeoff": "Два параллельных дерева компонентов (real + demo) увеличивают "
                    "время компиляции Reflex.",
        "status": "accepted",
    },
    {
        "id": "DD-006",
        "title": "empty_state компонент для честности",
        "category": "UX Pattern",
        "rationale": (
            "Вместо заглушек 'в разработке' — честный empty_state с иконкой, "
            "бейджем режима (demo_only / coming_soon) и объяснением ПОЧЕМУ "
            "данных нет. Рекрутер видит, что пробел осознан, а не случаен."
        ),
        "tradeoff": "Требует дисциплины писать настоящее объяснение, а не "
                    "'данные недоступны'.",
        "status": "accepted",
    },
]

_COLOR_PALETTE = [
    ("teal-9",  "#00927b", "Primary action, active state, 'real' badge"),
    ("amber-9", "#f59f00", "Warning, demo-only badge, IP-blocks"),
    ("red-9",   "#e5484d", "Danger, bad trend, security items"),
    ("blue-9",  "#0090ff", "Coming soon, info, neutral-positive"),
    ("gray-12", "#1c1c1c", "Primary text"),
    ("gray-9",  "#8d8d8d", "Secondary text, labels"),
    ("gray-4",  "#e8e8e8", "Borders, dividers"),
    ("gray-1",  "#fcfcfc", "Card backgrounds"),
]


def _decision_card(d: dict) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.flex(
                rx.text(d["id"], size="1", color=rx.color("gray", 8),
                        font_family="monospace"),
                rx.badge(d["category"], color_scheme="blue", variant="soft", size="1"),
                rx.badge("accepted", color_scheme="teal", variant="soft", size="1"),
                gap=SPACING["sm"],
                align="center",
            ),
            rx.text(d["title"], size="3", weight="medium",
                    color=rx.color("gray", 12), margin_top="4px"),
            direction="column",
            gap="2px",
            margin_bottom=SPACING["md"],
        ),
        rx.flex(
            _dd_section("Обоснование", d["rationale"], "circle-check", "teal"),
            _dd_section("Компромисс",  d["tradeoff"],  "scale",         "amber"),
            direction="column",
            gap=SPACING["sm"],
        ),
        padding=SPACING["lg"],
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        background=rx.color("gray", 1),
        margin_bottom=SPACING["md"],
    )


def _dd_section(label: str, text: str, icon: str, color: str) -> rx.Component:
    return rx.flex(
        rx.icon(icon, size=14, color=rx.color(color, 9), flex_shrink="0",
                margin_top="2px"),
        rx.flex(
            rx.text(label, size="1", weight="medium", color=rx.color("gray", 9),
                    text_transform="uppercase", letter_spacing="0.05em"),
            rx.text(text, size="2", color=rx.color("gray", 11), line_height="1.6"),
            direction="column",
            gap="2px",
        ),
        gap=SPACING["sm"],
        align="start",
    )


def _palette_row(token: str, hex_val: str, usage: str) -> rx.Component:
    return rx.flex(
        rx.box(
            width="32px", height="32px",
            border_radius="var(--radius-2)",
            background=hex_val,
            border=f"{BORDER} {rx.color('gray', 4)}",
            flex_shrink="0",
        ),
        rx.flex(
            rx.text(token, size="2", weight="medium", color=rx.color("gray", 12),
                    font_family="monospace"),
            rx.text(hex_val, size="1", color=rx.color("gray", 8),
                    font_family="monospace"),
            direction="column",
            gap="0",
            min_width="120px",
        ),
        rx.text(usage, size="2", color=rx.color("gray", 9), flex="1"),
        gap=SPACING["md"],
        align="center",
        padding="8px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


def real_design_tab() -> rx.Component:
    return real_page_wrapper(
        real_page_header("Дизайн-решения этого дашборда · tokens/ + components/"),

        # Design decisions
        section_header(
            f"Design Decisions · {len(_DECISIONS)} решений",
            "pen-tool",
        ),
        rx.box(height=SPACING["sm"]),
        *[_decision_card(d) for d in _DECISIONS],

        rx.box(height=SPACING["xl"]),

        # Color palette
        section_header("Color Palette · Radix Themes", "palette"),
        rx.box(
            *[_palette_row(t, h, u) for t, h, u in _COLOR_PALETTE],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # Stack note
        section_header("Стек дашборда", "layers"),
        rx.box(
            *[
                rx.flex(
                    rx.text(tech, size="2", weight="medium",
                            color=rx.color("gray", 12), min_width="180px"),
                    rx.text(note, size="2", color=rx.color("gray", 9)),
                    gap=SPACING["md"],
                    padding="8px 0",
                    border_bottom=f"{BORDER} {rx.color('gray', 3)}",
                )
                for tech, note in [
                    ("Reflex 0.9.6",         "Python → React компиляция"),
                    ("Radix Themes",         "Design system, семантические токены"),
                    ("Lucide icons",         "Иконки (hyphen-separated names)"),
                    ("granian (ASGI)",       "Сервер приложений"),
                    ("Python 3.13",          "Бэкенд + data layer"),
                ]
            ],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

    )
