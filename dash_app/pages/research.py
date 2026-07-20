"""
Research tab — UX Researcher view (этапы 2 и 8 MVP).

Sections:
1. Research Velocity  — stat cards from Jira mock (research-spike issues)
2. Research Journal   — hypothesis → method → metric → insight → decision table
3. Vault Coverage     — real note count per folder; gaps highlighted (real data)
4. Usability Testing  — TSR + SUS simulated placeholders (⚠️ no real test data)
"""

import reflex as rx

from ..tokens import SPACING, BORDER
from ..components import (
    table_container,
    stat_card,
    stat_card_row,
    status_badge,
    section_header,
    vault_coverage_chart,
)
from ..data.adapter import load_issues
from ..data.metrics import research_stats, research_journal
from ..data.vault_snapshot import FOLDER_COUNTS, SNAPSHOT_DATE
from .utils import jira_status_key as _jira_status_key

# Simulated usability test results (⚠️ no real test data exists yet)
_USABILITY_SESSIONS = [
    {"session": "Alpha-1", "date": "2026-05-12", "participants": 4,
     "tsr_pct": 68, "sus": 66, "issues": 3},
    {"session": "Alpha-2", "date": "2026-05-26", "participants": 4,
     "tsr_pct": 74, "sus": 70, "issues": 3},
    {"session": "Alpha-3", "date": "2026-06-09", "participants": 3,
     "tsr_pct": 77, "sus": 77, "issues": 2},
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vault_folder_counts() -> list[tuple[str, int]]:
    """Folder note counts from frozen snapshot — sorted ascending (gaps first)."""
    return sorted(FOLDER_COUNTS, key=lambda x: x[1])


def _decision_badge(decision: str | None) -> rx.Component:
    if decision == "Применено":
        return rx.badge("Применено", color_scheme="teal", variant="soft", size="1")
    if decision == "В беклог":
        return rx.badge("В беклог", color_scheme="amber", variant="soft", size="1")
    return rx.text("—", size="2", color=rx.color("gray", 8))


def _insight_indicator(insight: str | None) -> rx.Component:
    if insight:
        return rx.tooltip(
            rx.icon("circle_check", size=15, color=rx.color("teal", 10)),
            content=insight,
        )
    return rx.text("—", size="2", color=rx.color("gray", 8))


def _method_badge(method: str | None) -> rx.Component:
    colors = {
        "Task-based usability test": "iris",
        "A/B тест": "violet",
        "Опрос": "cyan",
    }
    color = colors.get(method or "", "gray")
    return rx.badge(method or "—", color_scheme=color, variant="outline", size="1")


# ---------------------------------------------------------------------------
# Research Journal table
# ---------------------------------------------------------------------------

def _journal_table(spikes) -> rx.Component:
    header = rx.grid(
        rx.text("Статус", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Гипотеза", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Метод", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Метрика", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Инсайт", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Решение", size="1", weight="medium", color=rx.color("gray", 9)),
        columns="90px 1fr 170px 150px 60px 110px",
        gap=SPACING["md"],
        padding=f"8px {SPACING['md']}",
        background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )

    rows = []
    for i, spike in enumerate(spikes):
        hyp = (spike.hypothesis or "—")
        hyp_short = hyp[:72] + "…" if len(hyp) > 72 else hyp

        row = rx.grid(
            status_badge(_jira_status_key(spike.status)),
            rx.tooltip(
                rx.text(hyp_short, size="2", color=rx.color("gray", 12)),
                content=hyp,
            ) if len(hyp) > 72 else rx.text(hyp, size="2", color=rx.color("gray", 12)),
            _method_badge(spike.research_method),
            rx.text(spike.research_metric or "—", size="2", color=rx.color("gray", 11)),
            _insight_indicator(spike.insight),
            _decision_badge(spike.decision),
            columns="90px 1fr 170px 150px 60px 110px",
            gap=SPACING["md"],
            align="center",
            padding=f"10px {SPACING['md']}",
            background="white" if i % 2 == 0 else rx.color("gray", 1),
            border_top=f"{BORDER} {rx.color('gray', 3)}",
        )
        rows.append(row)

    return table_container(
        header,
        *rows
    )


# ---------------------------------------------------------------------------
# Vault Coverage bars
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# Usability Testing placeholders
# ---------------------------------------------------------------------------

def _usability_table() -> rx.Component:
    header = rx.grid(
        rx.text("Сессия", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Дата", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Участников", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Task Success Rate", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("SUS score", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Найдено проблем", size="1", weight="medium", color=rx.color("gray", 9)),
        columns="repeat(6, 1fr)",
        gap=SPACING["md"],
        padding=f"8px {SPACING['md']}",
        background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )
    rows = []
    for i, s in enumerate(_USABILITY_SESSIONS):
        tsr_color = "teal" if s["tsr_pct"] >= 75 else "amber"
        sus_color = "teal" if s["sus"] >= 70 else "amber"
        rows.append(
            rx.grid(
                rx.text(s["session"], size="2", weight="medium"),
                rx.text(s["date"], size="2", color=rx.color("gray", 11)),
                rx.text(str(s["participants"]), size="2"),
                rx.badge(f'{s["tsr_pct"]}%', color_scheme=tsr_color, variant="soft", size="1"),
                rx.badge(str(s["sus"]), color_scheme=sus_color, variant="soft", size="1"),
                rx.text(str(s["issues"]), size="2"),
                columns="repeat(6, 1fr)",
                gap=SPACING["md"],
                align="center",
                padding=f"10px {SPACING['md']}",
                background="white" if i % 2 == 0 else rx.color("gray", 1),
                border_top=f"{BORDER} {rx.color('gray', 3)}",
            )
        )

    # Aggregate row
    avg_tsr = round(sum(s["tsr_pct"] for s in _USABILITY_SESSIONS) / len(_USABILITY_SESSIONS))
    avg_sus = round(sum(s["sus"] for s in _USABILITY_SESSIONS) / len(_USABILITY_SESSIONS))
    total_issues = sum(s["issues"] for s in _USABILITY_SESSIONS)

    rows.append(
        rx.grid(
            rx.text("Итого / ср.", size="2", weight="bold"),
            rx.text("", size="2"),
            rx.text(
                str(sum(s["participants"] for s in _USABILITY_SESSIONS)),
                size="2", weight="bold",
            ),
            rx.badge(f"{avg_tsr}%", color_scheme="teal" if avg_tsr >= 75 else "amber",
                     variant="solid", size="1"),
            rx.badge(str(avg_sus), color_scheme="teal" if avg_sus >= 70 else "amber",
                     variant="solid", size="1"),
            rx.text(str(total_issues), size="2", weight="bold"),
            columns="repeat(6, 1fr)",
            gap=SPACING["md"],
            align="center",
            padding=f"10px {SPACING['md']}",
            background=rx.color("teal", 2),
            border_top=f"2px solid {rx.color('teal', 5)}",
        )
    )

    return table_container(
        header,
        *rows
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def research_tab() -> rx.Component:
    issues = load_issues()
    rs = research_stats(issues)
    spikes = research_journal(issues)
    folders = _vault_folder_counts()

    insight_pct = round(100 * rs.with_insight / rs.total_spikes) if rs.total_spikes else 0
    applied_pct = round(100 * rs.applied / rs.total_spikes) if rs.total_spikes else 0

    return rx.box(

        # ── Research Velocity ──────────────────────────────────────────────
        section_header(
            "Research Velocity",
            subtitle="Спайки по исследованиям — от гипотезы до применённого решения",
        ),
        stat_card_row(
            stat_card(
                "Research spikes",
                str(rs.total_spikes),
                tooltip="Всего задач типа research-spike в Jira-моке.",
            ),
            stat_card(
                "В работе",
                str(rs.in_progress),
                tooltip="Спайки со статусом In Progress или In Review прямо сейчас.",
            ),
            stat_card(
                "С инсайтом",
                f"{rs.with_insight} ({insight_pct}%)",
                tooltip="Спайки, у которых заполнено поле Insight — реальный вывод из исследования.",
            ),
            stat_card(
                "Решение применено",
                f"{rs.applied} ({applied_pct}%)",
                tooltip='Спайки с decision = "Применено" — инсайт превратился в изменение продукта.',
            ),
        ),

        rx.box(height=SPACING["xl"]),

        # ── Research Journal ───────────────────────────────────────────────
        section_header(
            "Research Journal",
            subtitle="Гипотеза → метод → метрика → инсайт → решение",
        ),
        _journal_table(spikes),

        rx.box(height=SPACING["xl"]),

        # ── Vault Coverage ─────────────────────────────────────────────────
        section_header(
            "Vault Content Coverage",
            subtitle="Количество заметок по папкам · красные = пробелы (< 5 заметок)",
        ),
        vault_coverage_chart(folders),

        rx.box(height=SPACING["xl"]),

        # ── Usability Testing ──────────────────────────────────────────────
        section_header(
            "Usability Testing",
            subtitle="Alpha-сессии · TSR ≥ 75% и SUS ≥ 70 — целевые пороги ⚠️ симуляция",
        ),
        rx.callout(
            "Данные симулированы — реальных usability-тестов пока не проводилось. "
            "Заменить на результаты реальных сессий когда появятся.",
            icon="triangle-alert",
            color_scheme="amber",
            variant="soft",
            size="1",
            margin_bottom=SPACING["md"],
        ),
        _usability_table(),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
