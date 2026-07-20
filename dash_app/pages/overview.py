"""
Overview tab (PM). Metrics per handoff:
- North Star metric (реальные данные vault)
- Flow Metrics: cycle time, lead time, sprint predictability, rework rate,
  velocity, flow velocity, flow load
- MVP Timeline
- Squad Health (Spotify-светофор)
- OKR breakdown (visual bars)
- RICE-скоринг бэклога
"""

from datetime import date

import reflex as rx
from ..tokens import SPACING, TYPE_SCALE, BORDER
from ..components import (
    stat_card,
    stat_card_row,
    status_badge,
    data_table,
    mono_text,
    section_header,
)
from ..data.adapter import load_issues
from ..data.metrics import (
    rice_backlog,
    okr_breakdown,
    flow_stats,
    squad_health,
    velocity_stats,
    flow_velocity_total,
    flow_load,
)
from ..data.okr import load_okrs
from ..data.jira_mock_raw import MOTIF_DEMO_CONFIG
from ..data.vault_snapshot import TOTAL_NOTES, VAULT_NAME, SNAPSHOT_DATE

SQUAD_LABELS = {
    "RESEARCH": "Research",
    "ARCHITECTURE": "Architecture",
    "ANALYSIS": "Analysis",
    "DESIGN": "Design",
    "DEV": "Development & Pipeline",
    "QUALITY": "Quality",
    "RELEASE": "Instructions & Release",
    "MONITORING": "Monitoring & Support",
    "GROWTH": "Growth",
    "PM": "Product Management",
}

_MVP_START = MOTIF_DEMO_CONFIG.mvp_start.date()
_MVP_END = MOTIF_DEMO_CONFIG.mvp_deadline.date()
_TOTAL_DAYS = (_MVP_END - _MVP_START).days


def _pct_of_timeline(d: date) -> float:
    days = (d - _MVP_START).days
    return max(0.0, min(100.0, 100 * days / _TOTAL_DAYS))


def _today_pct() -> float:
    return _pct_of_timeline(date.today())


# ---------------------------------------------------------------------------
# North Star block
# ---------------------------------------------------------------------------

def _north_star(note_count: int) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.box(
                rx.flex(
                    rx.text(
                        "North Star Metric",
                        style={
                            "font_size": "11px",
                            "font_weight": "600",
                            "text_transform": "uppercase",
                            "letter_spacing": "0.08em",
                        },
                        color=rx.color("teal", 11),
                    ),
                    gap=SPACING["md"],
                    align="center",
                ),
                rx.text(
                    str(note_count),
                    style={"font_size": "48px", "font_weight": "700", "line_height": "1"},
                    color=rx.color("teal", 11),
                    margin_top=SPACING["xs"],
                ),
                rx.text(
                    "качественных заметок в vault",
                    size="3",
                    color=rx.color("gray", 11),
                    margin_top=SPACING["xs"],
                ),
                rx.text(
                    f"Obsidian vault · {VAULT_NAME} · снэпшот {SNAPSHOT_DATE}",
                    size="1",
                    color=rx.color("gray", 9),
                    margin_top="4px",
                ),
            ),
            rx.box(
                rx.text(
                    "Цель MVP",
                    size="1",
                    color=rx.color("gray", 9),
                    style={"text_transform": "uppercase", "letter_spacing": "0.05em"},
                ),
                rx.text(
                    f"{MOTIF_DEMO_CONFIG.total_scope:,}",
                    style={"font_size": "28px", "font_weight": "600"},
                    color=rx.color("gray", 11),
                ),
                rx.text(
                    "URL в scope",
                    size="1",
                    color=rx.color("gray", 9),
                ),
                rx.box(height=SPACING["sm"]),
                rx.text(
                    f"{round(100 * note_count / MOTIF_DEMO_CONFIG.total_scope, 1)}%",
                    style={"font_size": "20px", "font_weight": "500"},
                    color=rx.color("teal", 10),
                ),
                rx.text("от цели", size="1", color=rx.color("gray", 9)),
                text_align="right",
            ),
            justify="between",
            align="start",
            width="100%",
        ),
        background=rx.color("teal", 2),
        border=f"{BORDER} {rx.color('teal', 4)}",
        border_radius="var(--radius-3)",
        padding=SPACING["lg"],
    )


# ---------------------------------------------------------------------------
# MVP Timeline
# ---------------------------------------------------------------------------

def _mvp_timeline() -> rx.Component:
    squad_colors = [
        "teal", "iris", "violet", "cyan",
        "amber", "grass", "tomato", "plum", "orange",
    ]
    squads = MOTIF_DEMO_CONFIG.squads
    today_pct = _today_pct()

    rows = []
    for i, squad in enumerate(squads):
        start_d = _MVP_START.toordinal() + squad.stage_order * 7
        start_pct = _pct_of_timeline(date.fromordinal(start_d))
        end_pct = min(start_pct + 15, 100.0)
        color = squad_colors[i % len(squad_colors)]
        rows.append(
            rx.flex(
                rx.text(squad.name, size="1", color=rx.color("gray", 11),
                        width="160px", flex_shrink="0"),
                rx.box(
                    rx.box(
                        height="18px",
                        background=rx.color(color, 7),
                        border_radius="var(--radius-1)",
                        position="absolute",
                        left=f"{start_pct:.1f}%",
                        width=f"{end_pct - start_pct:.1f}%",
                    ),
                    position="relative",
                    height="18px",
                    flex="1",
                    background=rx.color("gray", 3),
                    border_radius="var(--radius-1)",
                ),
                align="center",
                gap=SPACING["sm"],
                width="100%",
            )
        )

    return rx.box(
        # "Сегодня" marker row
        rx.flex(
            rx.box(width="160px", flex_shrink="0"),
            rx.box(
                rx.box(
                    position="absolute",
                    left=f"{today_pct:.1f}%",
                    top="0", bottom="0",
                    width="2px",
                    background="var(--tomato-9)",
                ),
                rx.box(
                    rx.text("Сегодня", size="1", color=rx.color("tomato", 11)),
                    position="absolute",
                    left=f"{today_pct:.1f}%",
                    top="-18px",
                    transform="translateX(-50%)",
                ),
                position="relative",
                height="8px",
                flex="1",
            ),
            align="center",
            gap=SPACING["sm"],
            width="100%",
            margin_bottom="6px",
            margin_top="20px",
        ),
        *rows,
        rx.box(height=SPACING["xs"]),
        # date labels
        rx.flex(
            rx.box(width="160px", flex_shrink="0"),
            rx.flex(
                rx.text(str(_MVP_START), size="1", color=rx.color("gray", 9)),
                rx.text(str(_MVP_END), size="1", color=rx.color("gray", 9)),
                justify="between",
                flex="1",
            ),
            align="center",
            gap=SPACING["sm"],
            width="100%",
        ),
        display="flex",
        flex_direction="column",
        gap="6px",
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
        overflow="hidden",
    )


# ---------------------------------------------------------------------------
# OKR block (rich — Objective + Key Results)
# ---------------------------------------------------------------------------

_STATUS_COLORS = {"on_track": "grass", "at_risk": "amber", "off_track": "tomato"}
_STATUS_LABELS = {"on_track": "On Track", "at_risk": "At Risk", "off_track": "Off Track"}


def _kr_row(kr) -> rx.Component:
    pct = kr.progress_pct
    color = _STATUS_COLORS[kr.status]
    return rx.box(
        rx.flex(
            rx.text(kr.key, size="1", color=rx.color("gray", 9), width="52px", flex_shrink="0"),
            rx.text(kr.title, size="2", color=rx.color("gray", 12), flex="1"),
            rx.flex(
                rx.text(kr.formatted_current, size="2", weight="medium", color=rx.color(color, 11)),
                rx.text("→", size="1", color=rx.color("gray", 9)),
                rx.text(kr.formatted_target, size="1", color=rx.color("gray", 9)),
                align="center",
                gap="6px",
                flex_shrink="0",
            ),
            rx.badge(
                _STATUS_LABELS[kr.status],
                color_scheme=color,
                variant="soft",
                size="1",
                flex_shrink="0",
            ),
            align="center",
            gap=SPACING["sm"],
            width="100%",
        ),
        rx.box(
            rx.box(
                height="6px",
                background=rx.color(color, 7),
                border_radius="var(--radius-full)",
                width=f"{pct}%",
                min_width="2px",
            ),
            height="6px",
            background=rx.color("gray", 4),
            border_radius="var(--radius-full)",
            width="100%",
            margin_top="6px",
        ),
        padding=f"10px 0",
        border_top=f"{BORDER} {rx.color('gray', 3)}",
        width="100%",
    )


def _objective_card(obj, task_progress) -> rx.Component:
    color = _STATUS_COLORS[obj.status]
    return rx.box(
        # — header row
        rx.flex(
            rx.flex(
                rx.badge(
                    _STATUS_LABELS[obj.status],
                    color_scheme=color,
                    variant="solid",
                    size="1",
                ),
                rx.text(obj.quarter, size="1", color=rx.color("gray", 9)),
                align="center",
                gap=SPACING["sm"],
            ),
            rx.text(
                f"{obj.overall_progress_pct}% avg KR progress",
                size="1",
                color=rx.color(color, 11),
                weight="medium",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.box(height="8px"),
        # — title + description
        rx.text(obj.title, size="3", weight="medium", color=rx.color("gray", 12)),
        rx.text(obj.description, size="2", color=rx.color("gray", 10), margin_top="2px"),
        # — task progress (from okr_breakdown)
        rx.flex(
            rx.text(
                f"Задач в беклоге: {task_progress.done} / {task_progress.total} done ({task_progress.pct_done}%)",
                size="1",
                color=rx.color("gray", 9),
            ),
            rx.box(
                rx.box(
                    height="4px",
                    background=rx.color("gray", 7),
                    border_radius="var(--radius-full)",
                    width=f"{task_progress.pct_done}%",
                    min_width="2px",
                ),
                height="4px",
                background=rx.color("gray", 4),
                border_radius="var(--radius-full)",
                width="200px",
                flex_shrink="0",
            ),
            align="center",
            gap=SPACING["sm"],
            margin_top=SPACING["sm"],
        ),
        rx.box(height=SPACING["sm"]),
        # — Key Results
        *[_kr_row(kr) for kr in obj.key_results],
        padding=SPACING["lg"],
        border=f"{BORDER} {rx.color(color, 4)}",
        background=rx.color(color, 1),
        border_radius="var(--radius-3)",
        width="100%",
        margin_bottom=SPACING["md"],
    )


def _okr_section(objectives, task_rows) -> rx.Component:
    task_by_tag = {r.okr_tag: r for r in task_rows}
    cards = [_objective_card(obj, task_by_tag[obj.tag]) for obj in objectives if obj.tag in task_by_tag]
    return rx.box(*cards, width="100%")


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def overview_tab() -> rx.Component:
    issues = load_issues()
    fs = flow_stats(issues)
    vs = velocity_stats(issues)
    fv = flow_velocity_total(issues)
    fl = flow_load(issues)
    rice_rows = rice_backlog(issues)
    okr_rows = okr_breakdown(issues)
    okr_objectives = load_okrs()
    health_rows = squad_health(issues)
    note_count = TOTAL_NOTES

    return rx.box(

        # ── North Star ────────────────────────────────────────────────────
        section_header(
            "North Star",
            subtitle="Главная метрика продукта — создаёт ли пайплайн ценность",
        ),
        _north_star(note_count),

        rx.box(height=SPACING["xl"]),

        # ── Flow Metrics — ряд 1: время и предсказуемость ────────────────
        section_header(
            "Flow Metrics",
            subtitle="Скорость и предсказуемость поставки · Flow Metrics (Mik Kersten)",
        ),
        stat_card_row(
            stat_card(
                "Cycle time (среднее)",
                f"{fs.avg_cycle_time} дня" if fs.avg_cycle_time else "—",
                tooltip="Среднее время от первого 'In Progress' до 'Done'. Чем меньше — тем быстрее команда исполняет взятые задачи.",
            ),
            stat_card(
                "Lead time (среднее)",
                f"{fs.avg_lead_time} дня" if fs.avg_lead_time else "—",
                tooltip="Среднее время от создания задачи до 'Done', включая ожидание в беклоге. Показывает сквозную скорость поставки с точки зрения стейкхолдера.",
            ),
            stat_card(
                "Sprint predictability",
                f"{fs.sprint_predictability_pct}%" if fs.sprint_predictability_pct is not None else "—",
                tooltip="Доля задач из закрытых спринтов, завершённых в срок. 80%+ — хороший сигнал; ниже 70% — сигнал пересмотреть планирование.",
            ),
            stat_card(
                "Rework rate",
                f"{fs.rework_rate_pct}%",
                trend_direction="bad" if fs.rework_rate_pct > 30 else "neutral",
                tooltip="Доля задач с откатом статуса назад (например In Review → In Progress). Выше 30% — системные проблемы с качеством или требованиями.",
            ),
        ),

        rx.box(height=SPACING["md"]),

        # ── Flow Metrics — ряд 2: объём и нагрузка ───────────────────────
        stat_card_row(
            stat_card(
                "Velocity (ср. SP/спринт)",
                str(vs.avg_sp_per_sprint) if vs.avg_sp_per_sprint else "—",
                tooltip="Средняя сумма Story Points, закрытых командой за один спринт. Используется для прогнозирования, сколько работы помещается в следующий спринт.",
            ),
            stat_card(
                "Flow Velocity (всего SP)",
                str(fv),
                tooltip="Суммарные Story Points, завершённые по всему продукту с начала MVP. Показывает общий объём поставки — в отличие от Velocity, не привязан к спринту.",
            ),
            stat_card(
                "Flow Load (WIP)",
                str(fl),
                trend_direction="bad" if fl > 20 else "neutral",
                tooltip="Количество задач одновременно 'In Progress' или 'In Review' прямо сейчас. Слишком много = перегрузка и увеличение Lead Time (закон Литтла).",
            ),
            stat_card(
                "Flow Efficiency",
                f"{round(fs.avg_cycle_time / fs.avg_lead_time * 100)}%" if fs.avg_cycle_time and fs.avg_lead_time else "—",
                tooltip="Доля времени, когда над задачей реально работали, от общего Lead Time. Низкая — задача больше ждёт, чем исполняется. Формула: Cycle Time / Lead Time × 100%.",
            ),
        ),

        rx.box(height=SPACING["xl"]),

        # ── MVP Timeline ──────────────────────────────────────────────────
        section_header(
            "MVP Timeline",
            subtitle=f"Апр 2026 → Авг 2026 · {_TOTAL_DAYS} дней",
        ),
        _mvp_timeline(),

        rx.box(height=SPACING["xl"]),

        # ── Squad Health ──────────────────────────────────────────────────
        section_header(
            "Squad Health",
            subtitle="Spotify-светофор по 9 командам — Flow Efficiency и rework",
        ),
        data_table(
            columns=["Команда", "Готово", "Заблокировано", "Rework", "Статус"],
            rows=[
                [
                    SQUAD_LABELS.get(sh.squad_key, sh.squad_key),
                    f"{sh.done}/{sh.total} ({sh.done_pct}%)",
                    str(sh.blocked),
                    str(sh.rework),
                    status_badge(sh.status),
                ]
                for sh in health_rows
            ],
        ),

        rx.box(height=SPACING["xl"]),

        # ── OKR ───────────────────────────────────────────────────────────
        section_header(
            "OKR · Q2 2026",
            subtitle="Objectives + Key Results · статус на сегодня",
        ),
        _okr_section(okr_objectives, okr_rows),

        rx.box(height=SPACING["xl"]),

        # ── RICE backlog ──────────────────────────────────────────────────
        section_header(
            "RICE-скоринг бэклога",
            subtitle="По эпикам, отсортировано по score · RICE = (Reach × Impact × Confidence) / Effort",
        ),
        data_table(
            columns=["Эпик", "OKR", "Reach", "Impact", "Conf.", "Effort", "RICE", "Прогресс"],
            rows=[
                [
                    mono_text(row.epic),
                    row.okr_tag,
                    str(row.reach),
                    str(row.impact),
                    str(row.confidence),
                    str(row.effort),
                    rx.text(str(row.rice_score), weight="medium"),
                    f"{row.done_count}/{row.issue_count}",
                ]
                for row in rice_rows
            ],
        ),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
