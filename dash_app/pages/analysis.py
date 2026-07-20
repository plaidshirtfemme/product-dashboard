"""
Analysis BA+SA tab — Business Analyst / System Analyst view.

Sections:
1. Requirements Health — stat cards: spec completeness, ambiguity, churn, TTA
2. Requirements Table  — all requirement issues with BA fields
3. Requirements by Source — where requirements originate
4. Dependencies        — external deps, API contract changes
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
from ..data.metrics import (
    analysis_stats,
    analysis_requirements,
    analysis_dependencies,
    requirement_source_counts,
)


# ---------------------------------------------------------------------------
# Requirements Table
# ---------------------------------------------------------------------------

def _spec_bar(pct: int | None) -> rx.Component:
    if pct is None:
        return rx.text("—", size="2", color=rx.color("gray", 8))
    color = "teal" if pct >= 90 else "amber" if pct >= 70 else "tomato"
    return rx.flex(
        rx.box(
            rx.box(
                height="6px",
                background=rx.color(color, 7),
                border_radius="var(--radius-full)",
                width=f"{pct}%",
            ),
            width="60px",
            height="6px",
            background=rx.color("gray", 4),
            border_radius="var(--radius-full)",
            overflow="hidden",
        ),
        rx.text(f"{pct}%", size="1", color=rx.color(color, 11)),
        align="center",
        gap="6px",
    )


from .utils import jira_status_key as _req_status_key


def _requirements_table(rows) -> rx.Component:
    header = rx.grid(
        rx.text("Ключ", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Статус", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Источник", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Спецификация", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Неясности", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Изменений", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Согласовано", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Дней до апрув.", size="1", weight="medium", color=rx.color("gray", 9)),
        columns="90px 110px 1fr 110px 80px 80px 100px 110px",
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
                status_badge(_req_status_key(r.status)),
                rx.text(r.source or "—", size="2", color=rx.color("gray", 11)),
                _spec_bar(r.spec_completeness),
                rx.badge(
                    str(r.ambiguity_questions),
                    color_scheme="amber" if (r.ambiguity_questions or 0) > 0 else "gray",
                    variant="soft",
                    size="1",
                ) if r.ambiguity_questions is not None else rx.text("—", size="2", color=rx.color("gray", 8)),
                rx.badge(
                    str(r.change_count),
                    color_scheme="tomato" if r.change_count > 2 else "amber" if r.change_count > 0 else "gray",
                    variant="soft",
                    size="1",
                ),
                rx.icon(
                    "circle_check" if r.approved else "circle",
                    size=16,
                    color=rx.color("teal", 10) if r.approved else rx.color("gray", 7),
                ),
                rx.text(
                    f"{r.time_to_approval_days} дн." if r.time_to_approval_days is not None else "—",
                    size="2",
                    color=rx.color("gray", 11),
                ),
                columns="90px 110px 1fr 110px 80px 80px 100px 110px",
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
# Requirements by Source
# ---------------------------------------------------------------------------

def _source_bars(source_counts: list[tuple[str, int]]) -> rx.Component:
    if not source_counts:
        return rx.text("Нет данных", size="2", color=rx.color("gray", 9))

    total = sum(c for _, c in source_counts)
    max_count = max(c for _, c in source_counts)
    colors = ["teal", "iris", "violet", "amber", "cyan"]

    bars = []
    for i, (src, count) in enumerate(source_counts):
        pct_total = round(100 * count / total)
        bar_w = round(100 * count / max_count)
        color = colors[i % len(colors)]
        bars.append(
            rx.flex(
                rx.text(src, size="2", color=rx.color("gray", 12), width="160px", flex_shrink="0"),
                progress_bar(bar_w, color, 6, height="20px"),
                rx.text(
                    f"{count} ({pct_total}%)",
                    size="1",
                    color=rx.color("gray", 9),
                    width="70px",
                    text_align="right",
                    flex_shrink="0",
                ),
                align="center",
                gap=SPACING["sm"],
                width="100%",
            )
        )

    return rx.box(
        rx.flex(*bars, direction="column", gap="10px"),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
        width="100%",
    )


# ---------------------------------------------------------------------------
# Dependencies table
# ---------------------------------------------------------------------------

def _dependencies_table(dep_rows) -> rx.Component:
    if not dep_rows:
        return rx.text("Нет зависимостей в данных", size="2", color=rx.color("gray", 9))

    header = rx.grid(
        rx.text("Ключ", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Эпик", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Внешняя зависимость", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("API-контракт изменён", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Задокументировано", size="1", weight="medium", color=rx.color("gray", 9)),
        columns="100px 1fr 170px 170px 150px",
        gap=SPACING["md"],
        padding=f"8px {SPACING['md']}",
        background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )

    rows = []
    for i, d in enumerate(dep_rows):
        rows.append(
            rx.grid(
                mono_text(d.key),
                rx.text(d.epic, size="2", color=rx.color("gray", 11)),
                rx.badge(
                    "Да" if d.has_external else "Нет",
                    color_scheme="amber" if d.has_external else "gray",
                    variant="soft",
                    size="1",
                ),
                rx.badge(
                    str(d.api_contract_changes),
                    color_scheme="tomato" if d.api_contract_changes > 0 else "gray",
                    variant="soft",
                    size="1",
                ),
                rx.icon(
                    "circle_check" if d.documented else "circle_x",
                    size=16,
                    color=rx.color("teal", 10) if d.documented else rx.color("tomato", 9),
                ),
                columns="100px 1fr 170px 170px 150px",
                gap=SPACING["md"],
                align="center",
                padding=f"10px {SPACING['md']}",
                background="white" if i % 2 == 0 else rx.color("gray", 1),
                border_top=f"{BORDER} {rx.color('gray', 3)}",
            )
        )

    return table_container(
        header,
        *rows
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def analysis_tab() -> rx.Component:
    issues = load_issues()
    s = analysis_stats(issues)
    req_rows = analysis_requirements(issues)
    dep_rows = analysis_dependencies(issues)
    sources = requirement_source_counts(issues)

    churn_color = "bad" if s.total_churn > 5 else "neutral"
    ambi_color = "bad" if s.open_ambiguity_questions > 5 else "neutral"
    spec_value = f"{s.avg_spec_completeness}%" if s.avg_spec_completeness is not None else "—"

    return rx.box(

        # ── Requirements Health ────────────────────────────────────────────
        section_header(
            "Requirements Health",
            subtitle="Качество и стабильность требований · BA+SA метрики",
        ),
        stat_card_row(
            stat_card(
                "Средняя полнота спецификации",
                spec_value,
                tooltip="Среднее значение поля Spec Completeness (0–100%) по задачам, у которых оно заполнено. 90%+ — цель.",
            ),
            stat_card(
                "Открытых неясностей",
                str(s.open_ambiguity_questions),
                trend_direction=ambi_color,
                tooltip="Сумма поля Ambiguity Questions по всем задачам. Каждая неясность — риск переделки позже.",
            ),
            stat_card(
                "Изменений требований",
                str(s.total_churn),
                trend_direction=churn_color,
                tooltip="Суммарное число правок требований (requirement_change_count). Высокий churn — нестабильная предметная область или слабое discovery.",
            ),
            stat_card(
                "Среднее время до апрува",
                f"{s.avg_time_to_approval} дн." if s.avg_time_to_approval is not None else "—",
                tooltip="Среднее число дней от создания задачи-требования до approved_at. Долгий апрув — узкое место в review-процессе.",
            ),
        ),

        rx.box(height=SPACING["xl"]),

        # ── Requirements Table ─────────────────────────────────────────────
        section_header(
            "Requirements Register",
            subtitle=f"Реестр требований · {s.total_requirements} записей · {s.approved} согласовано",
        ),
        _requirements_table(req_rows),

        rx.box(height=SPACING["xl"]),

        # ── Source Breakdown ───────────────────────────────────────────────
        section_header(
            "Requirements by Source",
            subtitle="Откуда приходят требования",
        ),
        _source_bars(sources),

        rx.box(height=SPACING["xl"]),

        # ── Dependencies ───────────────────────────────────────────────────
        section_header(
            "Dependency Map",
            subtitle="Внешние зависимости и изменения API-контрактов",
        ),
        _dependencies_table(dep_rows),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
