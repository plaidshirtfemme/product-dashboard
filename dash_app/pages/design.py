"""
Design tab — Product/UX Designer view (этапы 4 и 6 MVP).

Sections:
1. Design Health      — stat cards: issues, iterations avg, a11y coverage, rework
2. Accessibility Audit — a11y coverage callout + per-issue breakdown
3. Design Register    — table of design-type issues with iteration depth bars
4. Iteration Depth    — visual: iterations per issue (signals design complexity)
"""

import reflex as rx

from ..tokens import SPACING, BORDER
from ..components import (
    table_container,
    progress_bar,
    stat_card,
    stat_card_row,
    status_badge,
    mono_text,
    section_header,
)
from ..data.adapter import load_issues
from ..data.metrics import design_stats, design_issues


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

from .utils import jira_status_key as _design_status_key


def _iter_bar(count: int | None) -> rx.Component:
    if count is None:
        return rx.text("—", size="2", color=rx.color("gray", 8))
    color = "grass" if count <= 2 else "amber" if count == 3 else "tomato"
    label_color = "grass" if count <= 2 else "amber" if count == 3 else "tomato"
    dots = []
    for i in range(1, 5):
        dots.append(
            rx.box(
                width="14px",
                height="14px",
                border_radius="var(--radius-full)",
                background=rx.color(color, 7) if i <= count else rx.color("gray", 4),
            )
        )
    return rx.flex(
        *dots,
        rx.text(str(count), size="1", color=rx.color(label_color, 11), margin_left="4px"),
        align="center",
        gap="3px",
    )


def _a11y_icon(checked: bool | None) -> rx.Component:
    if checked is True:
        return rx.icon("circle_check", size=16, color=rx.color("grass", 10))
    if checked is False:
        return rx.tooltip(
            rx.icon("circle_x", size=16, color=rx.color("tomato", 9)),
            content="Accessibility не проверена — риск выпустить недоступный UI",
        )
    return rx.text("—", size="2", color=rx.color("gray", 8))


# ---------------------------------------------------------------------------
# Accessibility Audit block
# ---------------------------------------------------------------------------

def _a11y_audit(rows, a11y_checked: int, a11y_total: int) -> rx.Component:
    pct = round(100 * a11y_checked / a11y_total) if a11y_total else 0
    unchecked = a11y_total - a11y_checked
    color = "grass" if pct == 100 else "amber" if pct >= 50 else "tomato"

    callout = rx.callout(
        f"{unchecked} из {a11y_total} design-задач не прошли accessibility-проверку ({100 - pct}%). "
        "Доступность — базовый критерий качества UI; без проверки нельзя утверждать соответствие WCAG.",
        icon="triangle-alert",
        color_scheme="tomato" if unchecked > 0 else "grass",
        variant="soft",
        size="1",
        margin_bottom=SPACING["md"],
    ) if unchecked > 0 else rx.callout(
        "Все design-задачи прошли accessibility-проверку ✓",
        icon="circle_check",
        color_scheme="grass",
        variant="soft",
        size="1",
        margin_bottom=SPACING["md"],
    )

    # Progress bar
    bar = rx.box(
        rx.flex(
            rx.text(
                f"A11y coverage: {a11y_checked}/{a11y_total}",
                size="2",
                color=rx.color("gray", 11),
            ),
            rx.text(f"{pct}%", size="2", weight="medium", color=rx.color(color, 11)),
            justify="between",
            width="100%",
            margin_bottom="8px",
        ),
        rx.box(
            rx.box(
                height="10px",
                background=rx.color(color, 7),
                border_radius="var(--radius-full)",
                width=f"{pct}%",
            ),
            height="10px",
            background=rx.color("gray", 4),
            border_radius="var(--radius-full)",
            width="100%",
            overflow="hidden",
        ),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
        margin_bottom=SPACING["md"],
    )

    # Per-issue list
    items = []
    for r in rows:
        if r.accessibility_checked is None:
            continue
        icon = rx.icon("circle_check", size=14, color=rx.color("grass", 10)) if r.accessibility_checked \
            else rx.icon("circle_x", size=14, color=rx.color("tomato", 9))
        items.append(
            rx.flex(
                icon,
                mono_text(r.key),
                rx.text(
                    "Проверено" if r.accessibility_checked else "Не проверено",
                    size="1",
                    color=rx.color("grass", 11) if r.accessibility_checked else rx.color("tomato", 11),
                ),
                gap=SPACING["sm"],
                align="center",
            )
        )

    return rx.box(
        callout,
        bar,
        rx.flex(*items, direction="column", gap="8px"),
    )


# ---------------------------------------------------------------------------
# Design Register table
# ---------------------------------------------------------------------------

def _design_table(rows) -> rx.Component:
    header = rx.grid(
        rx.text("Ключ", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Статус", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Эпик", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Итерации", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("A11y", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("OKR", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("SP", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Cycle time", size="1", weight="medium", color=rx.color("gray", 9)),
        columns="90px 110px 110px 120px 50px 1fr 40px 90px",
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
                status_badge(_design_status_key(r.status)),
                rx.text(r.epic, size="2", color=rx.color("gray", 11)),
                _iter_bar(r.iteration_count),
                _a11y_icon(r.accessibility_checked),
                rx.text(r.okr_tag, size="2", color=rx.color("gray", 11)),
                rx.text(str(r.story_points), size="2"),
                rx.text(
                    f"{r.cycle_time_days} дн." if r.cycle_time_days is not None else "—",
                    size="2",
                    color=rx.color("gray", 11),
                ),
                columns="90px 110px 110px 120px 50px 1fr 40px 90px",
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
# Iteration Depth chart
# ---------------------------------------------------------------------------

def _iteration_depth(rows) -> rx.Component:
    """Horizontal bars: one per design issue, length = iteration count."""
    if not rows:
        return rx.text("Нет данных", size="2", color=rx.color("gray", 9))

    max_iter = max((r.iteration_count or 0) for r in rows) or 1
    bars = []
    for r in rows:
        count = r.iteration_count or 0
        if count == 0:
            continue
        color = "grass" if count <= 2 else "amber" if count == 3 else "tomato"
        bar_pct = round(100 * count / max_iter)
        bars.append(
            rx.flex(
                rx.text(r.key, style={"font_family": "monospace", "font_size": "13px", "width": "80px", "flex_shrink": "0"}),
                progress_bar(bar_pct, color, 6, height="22px"),
                rx.text(
                    f"{count} итер.",
                    size="1",
                    color=rx.color(color, 11),
                    style={"width": "60px", "text_align": "right", "flex_shrink": "0"},
                ),
                align="center",
                gap=SPACING["sm"],
                width="100%",
            )
        )

    legend = rx.flex(
        rx.flex(
            rx.box(width="12px", height="12px", background=rx.color("grass", 6),
                   border_radius="var(--radius-1)"),
            rx.text("1–2 (норма)", size="1", color=rx.color("gray", 9)),
            gap="4px", align="center",
        ),
        rx.flex(
            rx.box(width="12px", height="12px", background=rx.color("amber", 6),
                   border_radius="var(--radius-1)"),
            rx.text("3 (много)", size="1", color=rx.color("gray", 9)),
            gap="4px", align="center",
        ),
        rx.flex(
            rx.box(width="12px", height="12px", background=rx.color("tomato", 6),
                   border_radius="var(--radius-1)"),
            rx.text("4+ (сигнал)", size="1", color=rx.color("gray", 9)),
            gap="4px", align="center",
        ),
        gap=SPACING["lg"],
        margin_bottom=SPACING["md"],
    )

    return rx.box(
        legend,
        rx.flex(*bars, direction="column", gap="8px"),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def design_tab() -> rx.Component:
    issues = load_issues()
    s = design_stats(issues)
    rows = design_issues(issues)

    iter_pct_bad = (
        round(100 * sum(1 for r in rows if (r.iteration_count or 0) >= 4) / len(rows))
        if rows else 0
    )

    return rx.box(

        # ── Design Health ──────────────────────────────────────────────────
        section_header(
            "Design Health",
            subtitle="Метрики дизайн-процесса · итерации, accessibility, rework",
        ),
        stat_card_row(
            stat_card(
                "Design issues",
                f"{s.done}/{s.total_design_issues}",
                tooltip=f"Завершено / всего задач типа 'design' в DESIGN squad. В работе: {s.in_progress}.",
            ),
            stat_card(
                "Среднее итераций",
                str(s.avg_iterations) if s.avg_iterations is not None else "—",
                trend_direction="bad" if (s.avg_iterations or 0) > 3 else "neutral",
                tooltip="Среднее число итераций на design-задачу. > 3 — сигнал: либо brief был неполным, либо много правок от стейкхолдеров.",
            ),
            stat_card(
                "A11y проверено",
                f"{s.a11y_checked}/{s.a11y_total}",
                trend_direction="bad" if s.a11y_checked < s.a11y_total else "neutral",
                tooltip="Число design-задач, у которых accessibility_checked = True. Цель — 100% перед handoff в разработку.",
            ),
            stat_card(
                "Rework (DESIGN squad)",
                str(s.design_rework),
                trend_direction="bad" if s.design_rework > 3 else "neutral",
                tooltip="Суммарное число откатов статуса (rework_count) по всем задачам в DESIGN squad. Показывает нестабильность дизайн-процесса.",
            ),
        ),

        rx.box(height=SPACING["xl"]),

        # ── Accessibility Audit ────────────────────────────────────────────
        section_header(
            "Accessibility Audit",
            subtitle="Покрытие проверкой доступности перед handoff в разработку",
        ),
        _a11y_audit(rows, s.a11y_checked, s.a11y_total),

        rx.box(height=SPACING["xl"]),

        # ── Design Register ────────────────────────────────────────────────
        section_header(
            "Design Register",
            subtitle=f"Реестр design-задач · {s.total_design_issues} задач",
        ),
        _design_table(rows),

        rx.box(height=SPACING["xl"]),

        # ── Iteration Depth ────────────────────────────────────────────────
        section_header(
            "Iteration Depth",
            subtitle="Число итераций на задачу · 4+ = сигнал о сложности или нестабильном брифе",
        ),
        _iteration_depth(rows),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
