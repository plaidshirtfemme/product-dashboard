"""Roadmap / Stakeholder tab — Goals, Timeline, Sprint Review."""

from datetime import date

import reflex as rx

from ..tokens import SPACING, BORDER, PAGE_MAX_WIDTH, STATUS_COLORS, EPIC_TYPE_COLORS
from ..components import (
    section_header,
    stat_card,
    stat_card_row,
    progress_bar,
)
from ..data.adapter import load_issues
from ..data.okr_dash import load_dash_okrs
from ..data.jira_mock_raw import (
    DASH_CONFIG, EPIC_NAMES, EPIC_TYPES, EPIC_UNLOCKS, epic_sort_key,
)

_PAD = f"0 {SPACING['xl']} {SPACING['xl']}"
_MAX = PAGE_MAX_WIDTH

_issues = load_issues(DASH_CONFIG)
_okrs   = load_dash_okrs()

_MVP_START  = DASH_CONFIG.mvp_start.date()
_MVP_END    = DASH_CONFIG.mvp_deadline.date()
_TODAY      = date.today()
_TOTAL_DAYS = (_MVP_END - _MVP_START).days or 1
_ELAPSED    = (_TODAY - _MVP_START).days
_TIME_PCT   = max(0, min(100, round(100 * _ELAPSED / _TOTAL_DAYS)))

_DONE_COUNT = sum(1 for i in _issues if i.status == "Done")
_WIP_COUNT  = sum(1 for i in _issues if i.status == "In Progress")
_TODO_COUNT = sum(1 for i in _issues if i.status == "To Do")
_TOTAL      = len(_issues)
_SCOPE_PCT  = round(100 * _DONE_COUNT / _TOTAL) if _TOTAL else 0


# ── Helpers ──────────────────────────────────────────────────────────────────

def _okr_status_color(status: str) -> str:
    return {"on_track": "grass", "at_risk": "amber", "off_track": "tomato"}.get(status, "gray")


def _status_dot(color: str) -> rx.Component:
    return rx.box(
        width="8px", height="8px",
        border_radius="50%",
        background=rx.color(color, 9),
        flex_shrink="0",
    )


# ── Section 1: Goals / OKR ───────────────────────────────────────────────────

def _kr_row(title: str, current: str, target: str, pct: int, status: str) -> rx.Component:
    color = _okr_status_color(status)
    return rx.flex(
        rx.flex(
            _status_dot(color),
            rx.text(title, size="2", color=rx.color("gray", 11), flex="1"),
            gap=SPACING["sm"],
            align="center",
            flex="1",
            min_width="0",
        ),
        rx.text(f"{current} / {target}", size="1", color=rx.color("gray", 9),
                white_space="nowrap", min_width="100px", text_align="right"),
        rx.box(
            rx.box(
                height="4px",
                background=rx.color(color, 7),
                border_radius="var(--radius-1)",
                width=f"{pct}%",
            ),
            width="80px",
            background=rx.color("gray", 3),
            border_radius="var(--radius-1)",
            height="4px",
            overflow="hidden",
            flex_shrink="0",
        ),
        rx.text(f"{pct}%", size="1", color=rx.color(color, 9),
                min_width="32px", text_align="right"),
        align="center",
        gap=SPACING["md"],
        padding=f"6px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
        width="100%",
    )


def _okr_card(obj) -> rx.Component:
    color = _okr_status_color(obj.status)
    return rx.box(
        rx.flex(
            rx.flex(
                rx.text(obj.tag, size="1", weight="medium",
                        color=rx.color(color, 9)),
                rx.badge(obj.status_label, color_scheme=color, variant="soft", size="1"),
                gap=SPACING["sm"],
                align="center",
            ),
            rx.text(f"{obj.overall_progress_pct}%", size="5", weight="bold",
                    color=rx.color("gray", 12)),
            justify="between",
            align="start",
            margin_bottom=SPACING["sm"],
        ),
        rx.text(obj.title, size="2", weight="medium",
                color=rx.color("gray", 12), margin_bottom=SPACING["sm"]),
        *[
            _kr_row(kr.title, kr.formatted_current, kr.formatted_target,
                    kr.progress_pct, kr.status)
            for kr in obj.key_results
        ],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_top=f"3px solid {rx.color(color, 7)}",
        border_radius="var(--radius-2)",
        padding=SPACING["md"],
        flex="1",
        min_width="280px",
    )


# North Star = первый Objective (O0) в okr_dash — единый источник, без хардкода.
_NORTH_STAR = next((o for o in _okrs if o.tag.startswith("O0")), None)


def _north_star_banner() -> rx.Component:
    """Единственная North Star проекта (установочная встреча 11.07, DASH-95).
    Заголовок и описание берём из Objective O0, чтобы не расходились с OKR-картой."""
    if _NORTH_STAR is None:
        return rx.fragment()
    return rx.box(
        rx.flex(
            rx.icon("star", size=18, color=rx.color("teal", 11)),
            rx.box(
                rx.text("NORTH STAR",
                        style={"font_size": "11px", "font_weight": "600",
                               "text_transform": "uppercase", "letter_spacing": "0.08em"},
                        color=rx.color("teal", 11)),
                rx.text(_NORTH_STAR.title,
                        size="4", weight="bold", color=rx.color("gray", 12)),
                rx.text(_NORTH_STAR.description,
                        size="1", color=rx.color("gray", 10)),
            ),
            gap=SPACING["md"],
            align="center",
        ),
        padding=SPACING["lg"],
        border=f"{BORDER} {rx.color('teal', 6)}",
        border_radius="var(--radius-3)",
        background=rx.color("teal", 2),
        margin_bottom=SPACING["md"],
    )


def _goals_section() -> rx.Component:
    return rx.box(
        section_header("Goals · OKR", "target"),
        _north_star_banner(),
        rx.flex(
            *[_okr_card(obj) for obj in _okrs],
            gap=SPACING["md"],
            flex_wrap="wrap",
        ),
    )


# ── Section 2: Timeline ───────────────────────────────────────────────────────

def _epic_row(epic_key: str, issues: list) -> rx.Component:
    total = len(issues)
    if total == 0:
        return rx.fragment()
    done      = sum(1 for i in issues if i.status == "Done")
    wip       = sum(1 for i in issues if i.status == "In Progress")
    sp_done   = sum(i.story_points for i in issues if i.status == "Done")
    sp_total  = sum(i.story_points for i in issues)
    pct       = round(100 * done / total) if total else 0

    if done == total:
        color, label = "grass", "Done"
    elif wip > 0:
        color, label = "amber", "In Progress"
    else:
        color, label = "gray", "To Do"

    short = epic_key.replace("DASH-EPIC-", "E").replace("KP-EPIC-", "E")
    epic_type = EPIC_TYPES.get(epic_key, "")
    type_color = EPIC_TYPE_COLORS.get(epic_type, "gray")
    unlocks_key = EPIC_UNLOCKS.get(epic_key, "")
    type_label = epic_type
    if unlocks_key:
        type_label = f"{epic_type} → {unlocks_key.replace('DASH-EPIC-', 'E')}"

    return rx.flex(
        rx.text(short, size="1", color=rx.color("gray", 9),
                min_width="40px", font_family="var(--font-mono)"),
        rx.tooltip(
            rx.badge(type_label, color_scheme=type_color, variant="soft", size="1",
                     min_width="86px", justify="center"),
            content=(f"{EPIC_NAMES.get(epic_key, epic_key)} — enabler, "
                     f"разблокирует «{EPIC_NAMES.get(unlocks_key, unlocks_key)}»") if unlocks_key
                    else f"{EPIC_NAMES.get(epic_key, epic_key)} — {epic_type or 'без типа'}",
        ) if epic_type else rx.box(min_width="86px"),
        rx.flex(
            rx.box(
                height="20px",
                background=rx.color(color, 7 if done < total else 8),
                border_radius="var(--radius-1)",
                width=f"{max(pct, 2)}%",
            ),
            flex="1",
            background=rx.color("gray", 3),
            border_radius="var(--radius-1)",
            height="20px",
            overflow="hidden",
        ),
        rx.badge(label, color_scheme=color, variant="soft", size="1",
                 min_width="90px", justify="center"),
        rx.text(f"{done}/{total} · {sp_done}/{sp_total} SP",
                size="1", color=rx.color("gray", 9), min_width="110px", text_align="right"),
        align="center",
        gap=SPACING["md"],
        padding=f"5px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
        width="100%",
    )


def _timeline_section() -> rx.Component:
    by_epic: dict[str, list] = {}
    for i in _issues:
        by_epic.setdefault(i.epic, []).append(i)

    return rx.box(
        section_header("Timeline · Epics", "gantt-chart"),
        stat_card_row(
            stat_card("Время", f"{_TIME_PCT}%",
                      trend=f"{_ELAPSED} из {_TOTAL_DAYS} дн.", icon="clock"),
            stat_card("Scope Done", f"{_SCOPE_PCT}%",
                      trend=f"{_DONE_COUNT} из {_TOTAL} задач", icon="circle-check"),
            stat_card("In Progress", str(_WIP_COUNT),
                      trend="активных задач", icon="loader-circle"),
            stat_card("To Do", str(_TODO_COUNT),
                      trend="в очереди", icon="list"),
        ),
        rx.box(height=SPACING["md"]),
        rx.flex(
            rx.text("Epic", size="1", color=rx.color("gray", 8), min_width="40px"),
            rx.text("Type", size="1", color=rx.color("gray", 8), min_width="86px"),
            rx.text("Progress", size="1", color=rx.color("gray", 8), flex="1"),
            rx.text("Status", size="1", color=rx.color("gray", 8), min_width="90px"),
            rx.text("Issues · SP", size="1", color=rx.color("gray", 8),
                    min_width="110px", text_align="right"),
            gap=SPACING["md"],
            padding=f"0 0 {SPACING['sm']}",
            border_bottom=f"1.5px solid {rx.color('gray', 4)}",
        ),
        *[_epic_row(epic, issues)
          for epic, issues in sorted(by_epic.items(), key=lambda kv: epic_sort_key(kv[0]))],
    )


# ── Section 3: Sprint Review ──────────────────────────────────────────────────

def _sprint_review_row(sprint_name: str, issues: list) -> rx.Component:
    total    = len(issues)
    done     = sum(1 for i in issues if i.status == "Done")
    sp_done  = sum(i.story_points for i in issues if i.status == "Done")
    sp_total = sum(i.story_points for i in issues)
    bugs     = sum(1 for i in issues if i.issue_type == "bug")
    velocity = sp_done

    is_done  = done == total and total > 0
    color    = "grass" if is_done else "amber"

    return rx.flex(
        rx.text(sprint_name, size="2", weight="medium",
                color=rx.color("gray", 12), min_width="160px"),
        rx.badge(
            "Closed" if is_done else "Active",
            color_scheme=color, variant="soft", size="1", min_width="64px",
        ),
        rx.text(f"{done}/{total}", size="2", color=rx.color("gray", 11),
                min_width="60px", text_align="center"),
        rx.text(f"{velocity} SP", size="2", color=rx.color("teal", 9),
                min_width="60px", text_align="center", weight="medium"),
        rx.text(f"{bugs} bug{'s' if bugs != 1 else ''}",
                size="2", color=rx.color("gray", 9), min_width="60px", text_align="center"),
        align="center",
        gap=SPACING["md"],
        padding=f"8px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
        width="100%",
    )


def _sprint_review_section() -> rx.Component:
    by_sprint: dict[str, list] = {}
    for i in _issues:
        key = i.sprint_name or "No Sprint"
        by_sprint.setdefault(key, []).append(i)

    sorted_sprints = sorted(
        [(k, v) for k, v in by_sprint.items() if k != "No Sprint"],
        key=lambda x: x[0],
    )

    return rx.box(
        section_header("Sprint Review", "clipboard-check"),
        rx.flex(
            rx.text("Sprint", size="1", color=rx.color("gray", 8), min_width="160px"),
            rx.text("Status", size="1", color=rx.color("gray", 8), min_width="64px"),
            rx.text("Issues", size="1", color=rx.color("gray", 8),
                    min_width="60px", text_align="center"),
            rx.text("Velocity", size="1", color=rx.color("gray", 8),
                    min_width="60px", text_align="center"),
            rx.text("Bugs", size="1", color=rx.color("gray", 8),
                    min_width="60px", text_align="center"),
            gap=SPACING["md"],
            padding=f"0 0 {SPACING['sm']}",
            border_bottom=f"1.5px solid {rx.color('gray', 4)}",
        ),
        *[_sprint_review_row(name, issues) for name, issues in sorted_sprints],
    )


# ── Tab root ─────────────────────────────────────────────────────────────────

def roadmap_tab() -> rx.Component:
    return rx.box(
        _goals_section(),
        rx.box(height=SPACING["xl"]),
        _timeline_section(),
        rx.box(height=SPACING["xl"]),
        _sprint_review_section(),
        padding=_PAD,
        max_width=_MAX,
        margin="0 auto",
    )
