"""
Architecture tab — System Architect view (этап 3 MVP).

Sections:
1. Architecture Health — stat cards: issues, ADRs status, SP, rework
2. ADR Register        — Architecture Decision Records with context/decision/consequences
3. Architecture Tasks  — non-ADR tasks in ARCHITECTURE squad
"""

import reflex as rx

from ..tokens import SPACING, BORDER
from ..components import (
    table_container,
    stat_card,
    stat_card_row,
    status_badge,
    data_source_badge,
    mono_text,
    section_header,
)
from ..data.adapter import load_issues
from ..data.metrics import arch_stats, arch_adrs, arch_tasks


# ---------------------------------------------------------------------------
# ADR status badge
# ---------------------------------------------------------------------------

def _adr_status_badge(adr_status: str) -> rx.Component:
    colors = {
        "Accepted": "teal",
        "Proposed": "amber",
        "Deprecated": "gray",
        "Superseded": "tomato",
    }
    color = colors.get(adr_status, "gray")
    return rx.badge(adr_status, color_scheme=color, variant="soft", size="1")


from .utils import jira_status_key as _issue_status_key


# ---------------------------------------------------------------------------
# ADR Register
# ---------------------------------------------------------------------------

def _adr_card(row) -> rx.Component:
    """Expandable card for one ADR — shows context / decision / consequences."""
    status_color = {
        "Done": "grass",
        "In Review": "teal",
        "In Progress": "amber",
    }.get(row.issue_status, "gray")

    return rx.box(
        # Header row
        rx.flex(
            rx.flex(
                mono_text(row.key),
                rx.badge(
                    row.issue_status,
                    color_scheme=status_color,
                    variant="soft",
                    size="1",
                ),
                _adr_status_badge(row.adr_status),
                gap=SPACING["sm"],
                align="center",
            ),
            rx.text(f"{row.story_points} SP", size="1", color=rx.color("gray", 9)),
            justify="between",
            align="center",
            width="100%",
        ),

        # Body: 3-column context / decision / consequences
        rx.grid(
            # Context
            rx.box(
                rx.text(
                    "Контекст",
                    size="1",
                    weight="medium",
                    color=rx.color("gray", 9),
                    style={"text_transform": "uppercase", "letter_spacing": "0.05em"},
                    margin_bottom="4px",
                ),
                rx.text(
                    row.context or "—",
                    size="2",
                    color=rx.color("gray", 11),
                ),
            ),
            # Decision
            rx.box(
                rx.text(
                    "Решение",
                    size="1",
                    weight="medium",
                    color=rx.color("teal", 10),
                    style={"text_transform": "uppercase", "letter_spacing": "0.05em"},
                    margin_bottom="4px",
                ),
                rx.text(
                    row.decision or "—",
                    size="2",
                    color=rx.color("gray", 12),
                    weight="medium",
                ),
            ),
            # Consequences
            rx.box(
                rx.text(
                    "Последствия",
                    size="1",
                    weight="medium",
                    color=rx.color("gray", 9),
                    style={"text_transform": "uppercase", "letter_spacing": "0.05em"},
                    margin_bottom="4px",
                ),
                rx.text(
                    row.consequences or "—",
                    size="2",
                    color=rx.color("gray", 11),
                ),
            ),
            columns="1fr 1fr 1fr",
            gap=SPACING["lg"],
            margin_top=SPACING["md"],
        ),

        background="white",
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_left=f"4px solid {rx.color('teal', 7) if row.adr_status == 'Accepted' else rx.color('amber', 7)}",
        border_radius="var(--radius-3)",
        padding=SPACING["md"],
        width="100%",
    )


# ---------------------------------------------------------------------------
# Architecture Tasks table
# ---------------------------------------------------------------------------

def _tasks_table(rows) -> rx.Component:
    if not rows:
        return rx.text("Нет задач", size="2", color=rx.color("gray", 9))

    header = rx.grid(
        rx.text("Ключ", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Статус", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Тип", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("SP", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Cycle time", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Rework", size="1", weight="medium", color=rx.color("gray", 9)),
        columns="90px 110px 100px 50px 100px 80px",
        gap=SPACING["md"],
        padding=f"8px {SPACING['md']}",
        background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )

    table_rows = []
    for idx, r in enumerate(rows):
        table_rows.append(
            rx.grid(
                mono_text(r.key),
                status_badge(_issue_status_key(r.status)),
                rx.badge(r.issue_type, color_scheme="gray", variant="outline", size="1"),
                rx.text(str(r.story_points), size="2"),
                rx.text(
                    f"{r.cycle_time_days} дн." if r.cycle_time_days else "—",
                    size="2",
                    color=rx.color("gray", 11),
                ),
                rx.badge(
                    str(r.rework_count),
                    color_scheme="tomato" if r.rework_count > 0 else "gray",
                    variant="soft",
                    size="1",
                ),
                columns="90px 110px 100px 50px 100px 80px",
                gap=SPACING["md"],
                align="center",
                padding=f"10px {SPACING['md']}",
                background="white" if idx % 2 == 0 else rx.color("gray", 1),
                border_top=f"{BORDER} {rx.color('gray', 3)}",
            )
        )

    return table_container(
        header,
        *table_rows
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def architecture_tab() -> rx.Component:
    issues = load_issues()
    s = arch_stats(issues)
    adrs = arch_adrs(issues)
    tasks = arch_tasks(issues)

    done_pct = round(100 * s.done / s.total) if s.total else 0

    return rx.box(

        # ── Architecture Health ────────────────────────────────────────────
        section_header(
            "Architecture Health",
            subtitle="Статус архитектурных решений и поставки · ARCHITECTURE squad",
            action=data_source_badge("mock"),
        ),
        stat_card_row(
            stat_card(
                "Задач выполнено",
                f"{s.done}/{s.total} ({done_pct}%)",
                tooltip="Доля завершённых задач в ARCHITECTURE squad. Включает ADR, tasks, stories.",
            ),
            stat_card(
                "ADR",
                f"{s.adr_done} принято / {s.adr_total} всего",
                tooltip=f"Architecture Decision Records: {s.adr_done} Done, {s.adr_in_review} In Review, {s.adr_in_progress} In Progress.",
            ),
            stat_card(
                "SP поставлено",
                str(s.sp_done),
                tooltip="Суммарные Story Points завершённых задач ARCHITECTURE squad.",
            ),
            stat_card(
                "Rework",
                str(s.rework),
                trend_direction="bad" if s.rework > 3 else "neutral",
                tooltip="Суммарное число откатов статуса (rework_count) в ARCHITECTURE squad. Высокий rework = нестабильная архитектура или неверные ожидания.",
            ),
        ),

        rx.box(height=SPACING["xl"]),

        # ── ADR Register ───────────────────────────────────────────────────
        section_header(
            "ADR Register",
            subtitle="Architecture Decision Records · контекст → решение → последствия",
            action=data_source_badge("mock"),
        ),
        rx.flex(
            *[_adr_card(r) for r in adrs],
            direction="column",
            gap=SPACING["md"],
            width="100%",
        ),

        rx.box(height=SPACING["xl"]),

        # ── Architecture Tasks ─────────────────────────────────────────────
        section_header(
            "Architecture Tasks",
            subtitle=f"Задачи ARCHITECTURE squad (без ADR) · {len(tasks)} записей",
            action=data_source_badge("mock"),
        ),
        _tasks_table(tasks),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
