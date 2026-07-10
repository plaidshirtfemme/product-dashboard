"""Dev & Pipeline tab — Developer view (этап 5 MVP)."""

import reflex as rx
from ..tokens import SPACING, BORDER, STATUS_COLORS
from ..components import stat_card, stat_card_row, status_badge, data_source_badge, mono_text, section_header, table_container, sev_badge as _sev_badge, SEV_COLORS as _SEV_COLORS
from ..data.adapter import load_issues
from ..data.metrics import squad_summary, squad_bugs, squad_non_bugs, sprint_trends, dev_person_wip

_PRI_COLORS = {"Highest": STATUS_COLORS["danger"], "High": STATUS_COLORS["warning"], "Medium": "gray", "Low": "gray", "Lowest": "gray"}

def _pri_badge(p): return rx.badge(p or "—", color_scheme=_PRI_COLORS.get(p or "", "gray"), variant="outline", size="1")


from .utils import jira_status_key as _status_key


def _bug_table(bugs, show_squad=False) -> rx.Component:
    cols = ["Ключ", "Статус", "Severity", "Priority", "SP", "Cycle time"]
    col_template = "90px 110px 100px 100px 40px 90px"
    if show_squad:
        cols = ["Ключ", "Squad", "Статус", "Severity", "Priority", "SP"]
        col_template = "90px 120px 110px 100px 100px 40px"

    header = rx.grid(*[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9)) for c in cols],
                     columns=col_template, gap=SPACING["md"],
                     padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
                     border_radius="var(--radius-2) var(--radius-2) 0 0")

    rows = []
    for idx, b in enumerate(bugs):
        cells = [
            mono_text(b.key),
            rx.text(b.squad_key, size="2", color=rx.color("gray", 11)) if show_squad else None,
            status_badge(_status_key(b.status)),
            _sev_badge(b.severity),
            _pri_badge(b.priority),
            rx.text(str(b.story_points), size="2"),
        ]
        if not show_squad:
            cells.append(rx.text(f"{b.cycle_time_days} дн." if b.cycle_time_days else "—", size="2", color=rx.color("gray", 11)))
        cells = [c for c in cells if c is not None]
        rows.append(rx.grid(*cells, columns=col_template, gap=SPACING["md"], align="center",
                            padding=f"10px {SPACING['md']}",
                            background="white" if idx % 2 == 0 else rx.color("gray", 1),
                            border_top=f"{BORDER} {rx.color('gray', 3)}"))

    return table_container(header, *rows)


def _tasks_table(tasks) -> rx.Component:
    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Ключ", "Статус", "Тип", "Priority", "SP", "Cycle time", "Blocked"]],
        columns="90px 110px 90px 100px 40px 90px 80px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0")

    rows = []
    for idx, t in enumerate(tasks):
        rows.append(rx.grid(
            mono_text(t.key), status_badge(_status_key(t.status)),
            rx.badge(t.issue_type, color_scheme="gray", variant="outline", size="1"),
            _pri_badge(t.priority), rx.text(str(t.story_points), size="2"),
            rx.text(f"{t.cycle_time_days} дн." if t.cycle_time_days else "—", size="2", color=rx.color("gray", 11)),
            rx.icon("circle_x" if t.blocked_by else "circle", size=14,
                    color=rx.color("tomato", 9) if t.blocked_by else rx.color("gray", 5)),
            columns="90px 110px 90px 100px 40px 90px 80px", gap=SPACING["md"], align="center",
            padding=f"10px {SPACING['md']}",
            background="white" if idx % 2 == 0 else rx.color("gray", 1),
            border_top=f"{BORDER} {rx.color('gray', 3)}"))

    return table_container(header, *rows)


def _trend_bars(trends, field: str, label: str, color: str, unit: str = "") -> rx.Component:
    """Mini horizontal bar chart for a numeric field across sprints."""
    values = [getattr(t, field) for t in trends]
    non_null = [v for v in values if v is not None]
    max_val = max(non_null) if non_null else 1

    bars = []
    for t, v in zip(trends, values):
        if v is None:
            pct = 0
            display = "—"
        else:
            pct = round(100 * v / max_val) if max_val else 0
            display = f"{v}{unit}"
        bars.append(
            rx.flex(
                rx.text(t.label, size="1", color=rx.color("gray", 9),
                        width="60px", flex_shrink="0"),
                rx.box(
                    rx.box(
                        height="24px",
                        background=rx.color(color, 6),
                        border_radius="var(--radius-1)",
                        width=f"{max(pct, 2)}%",
                    ),
                    flex="1",
                    background=rx.color("gray", 3),
                    border_radius="var(--radius-1)",
                    height="24px",
                    overflow="hidden",
                ),
                rx.text(display, size="1", weight="medium",
                        color=rx.color(color, 11),
                        style={"width": "60px", "text_align": "right", "flex_shrink": "0"}),
                align="center",
                gap=SPACING["sm"],
                width="100%",
            )
        )

    return rx.box(
        rx.text(label, size="2", weight="medium", color=rx.color("gray", 11),
                margin_bottom=SPACING["sm"]),
        rx.flex(*bars, direction="column", gap="6px"),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
        flex="1",
        min_width="220px",
    )


def _person_wip_table(people) -> rx.Component:
    _wip_colors = {"overloaded": STATUS_COLORS["danger"], "at_risk": STATUS_COLORS["warning"], "ok": STATUS_COLORS["success"]}
    _wip_labels = {"overloaded": "Перегружен", "at_risk": "Риск", "ok": "OK"}

    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Разработчик", "Всего задач", "В работе (WIP)", "Готово", "Context-switching", "Статус"]],
        columns="160px 110px 130px 80px 160px 120px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )
    rows = []
    for idx, p in enumerate(people):
        color = _wip_colors[p.wip_status]
        rows.append(rx.grid(
            rx.text(p.assignee, size="2", weight="medium"),
            rx.text(str(p.total), size="2"),
            rx.flex(
                rx.text(str(p.in_progress), size="2", weight="bold",
                        color=rx.color(color, 11)),
                *[rx.box(width="10px", height="10px", border_radius="2px",
                         background=rx.color(color, 6)) for _ in range(p.in_progress)],
                align="center", gap="4px",
            ),
            rx.text(str(p.done), size="2", color=rx.color("gray", 10)),
            rx.flex(
                rx.text(str(p.context_switches), size="2",
                        color=rx.color("amber", 11) if p.context_switches > 3 else rx.color("gray", 10)),
                rx.text("переключений", size="1", color=rx.color("gray", 9)),
                align="center", gap="6px",
            ),
            rx.badge(_wip_labels[p.wip_status], color_scheme=color, variant="soft", size="1"),
            columns="160px 110px 130px 80px 160px 120px", gap=SPACING["md"], align="center",
            padding=f"10px {SPACING['md']}",
            background="white" if idx % 2 == 0 else rx.color("gray", 1),
            border_top=f"{BORDER} {rx.color('gray', 3)}",
            border_left=f"3px solid {rx.color(color, 6)}" if p.wip_status != "ok" else "3px solid transparent",
        ))
    return table_container(header, *rows)


def dev_tab() -> rx.Component:
    issues = load_issues()
    s = squad_summary(issues, "DEV")
    bugs = squad_bugs(issues, "DEV")
    tasks = squad_non_bugs(issues, "DEV")
    trends = sprint_trends(issues)
    person_wip = dev_person_wip(issues)

    return rx.box(
        section_header("Dev & Pipeline Health",
                       subtitle="Метрики разработки и пайплайна · DEV squad",
                       action=data_source_badge("mock")),
        stat_card_row(
            stat_card("Задач выполнено", f"{s.done}/{s.total} ({s.done_pct}%)",
                      tooltip="Доля завершённых задач в DEV squad."),
            stat_card("Bugs", str(s.bugs), trend_direction="bad" if s.bugs > 3 else "neutral",
                      tooltip="Количество задач типа bug в DEV squad."),
            stat_card("Заблокировано", str(s.blocked), trend_direction="bad" if s.blocked > 1 else "neutral",
                      tooltip="Задачи с активной блокировкой (blocked_by заполнено)."),
            stat_card("Rework", str(s.rework), trend_direction="bad" if s.rework > 3 else "neutral",
                      tooltip="Суммарные откаты статуса в DEV squad."),
        ),
        rx.box(height=SPACING["xl"]),
        section_header("Bug Register", subtitle=f"Баги в DEV squad · {len(bugs)} записей",
                       action=data_source_badge("mock")),
        _bug_table(bugs) if bugs else rx.text("Нет багов", size="2", color=rx.color("gray", 9)),
        rx.box(height=SPACING["xl"]),
        section_header("Tasks & Stories", subtitle=f"Задачи DEV squad (без багов) · {len(tasks)} записей",
                       action=data_source_badge("mock")),
        _tasks_table(tasks),
        rx.box(height=SPACING["xl"]),
        section_header("Per-person WIP",
                       subtitle="Нагрузка по разработчикам · DEV squad · WIP ≥ 3 = перегрузка",
                       action=data_source_badge("mock")),
        _person_wip_table(person_wip),
        rx.box(height=SPACING["xl"]),
        section_header("Flow Trends",
                       subtitle="Динамика по спринтам · все команды агрегированы",
                       action=data_source_badge("mock")),
        rx.flex(
            _trend_bars(trends, "throughput", "Throughput (issues Done)", "teal"),
            _trend_bars(trends, "sp_done", "Story Points Done", "iris"),
            _trend_bars(trends, "avg_cycle_time", "Avg Cycle Time", "amber", unit=" дн."),
            _trend_bars(trends, "rework_count", "Rework events", "tomato"),
            gap=SPACING["md"],
            wrap="wrap",
            width="100%",
        ),
        padding=SPACING["xl"], max_width="1100px", margin="0 auto",
    )
