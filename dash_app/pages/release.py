"""Instructions & Release tab — Release Manager view (этап 6 MVP)."""

import reflex as rx
from ..tokens import SPACING, BORDER
from ..components import stat_card, stat_card_row, status_badge, mono_text, section_header, table_header, table_row, table_container
from ..data.adapter import load_issues
from ..data.metrics import squad_summary, squad_non_bugs, release_plan, slipped_issues


from .utils import jira_status_key as _status_key


def _release_cards(releases) -> rx.Component:
    cards = []
    for r in releases:
        color = "grass" if r.done_pct == 100 else "tomato" if r.slipped else "amber"
        cards.append(rx.box(
            rx.flex(
                rx.text(r.version, size="2", weight="medium"),
                rx.badge(f"{r.slipped} слип" if r.slipped else "В срок",
                         color_scheme="tomato" if r.slipped else "grass", variant="soft", size="1"),
                justify="between", align="center", margin_bottom="10px"),
            rx.box(
                rx.box(height="10px", background=rx.color(color, 7),
                       border_radius="var(--radius-full)", width=f"{r.done_pct}%"),
                height="10px", background=rx.color("gray", 4),
                border_radius="var(--radius-full)", overflow="hidden", margin_bottom="6px"),
            rx.text(f"{r.done}/{r.total} задач ({r.done_pct}%)", size="1", color=rx.color("gray", 9)),
            background="white", border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)", padding=SPACING["md"], flex="1"))
    return rx.flex(*cards, gap=SPACING["md"], wrap="wrap", width="100%")


def _slipped_table(rows) -> rx.Component:
    if not rows:
        return rx.callout("Нет просроченных задач — все задачи выполнены в срок ✓",
                          icon="circle_check", color_scheme="grass", variant="soft", size="1")
    _TPL = "90px 110px 100px 50px"
    header = table_header(["Ключ", "Статус", "Priority", "SP"], _TPL)
    table_rows = []
    for idx, r in enumerate(rows):
        table_rows.append(table_row([
            mono_text(r.key), status_badge(_status_key(r.status)),
            rx.badge(r.priority or "—", color_scheme="gray", variant="outline", size="1"),
            rx.text(str(r.story_points), size="2"),
        ], _TPL, idx, accent=f"3px solid {rx.color('tomato', 7)}"))
    return table_container(header, *table_rows)


def _tasks_table(tasks) -> rx.Component:
    _TPL = "90px 110px 100px 40px 90px 70px"
    header = table_header(["Ключ", "Статус", "Priority", "SP", "Cycle time", "Rework"], _TPL)
    rows = []
    for idx, t in enumerate(tasks):
        rows.append(table_row([
            mono_text(t.key), status_badge(_status_key(t.status)),
            rx.badge(t.priority or "—", color_scheme="gray", variant="outline", size="1"),
            rx.text(str(t.story_points), size="2"),
            rx.text(f"{t.cycle_time_days} дн." if t.cycle_time_days else "—", size="2", color=rx.color("gray", 11)),
            rx.badge(str(t.rework_count), color_scheme="tomato" if t.rework_count > 0 else "gray",
                     variant="soft", size="1"),
        ], _TPL, idx))
    return table_container(header, *rows)


def release_tab() -> rx.Component:
    issues = load_issues()
    s = squad_summary(issues, "RELEASE")
    releases = release_plan(issues)
    slipped = slipped_issues(issues)
    tasks = squad_non_bugs(issues, "RELEASE")
    total_slipped = sum(r.slipped for r in releases)

    return rx.box(
        section_header("Release Health",
                       subtitle="Статус поставки по релизам · RELEASE squad"),
        stat_card_row(
            stat_card("Задач выполнено", f"{s.done}/{s.total} ({s.done_pct}%)",
                      tooltip="Доля завершённых задач в RELEASE squad."),
            stat_card("Релизов", str(len(releases)),
                      tooltip="Число релизов с задачами в RELEASE squad."),
            stat_card("Просрочено (slip)", str(total_slipped),
                      trend_direction="bad" if total_slipped > 0 else "neutral",
                      tooltip="Задачи, перенесённые из исходного fix_version в более поздний релиз."),
            stat_card("Rework", str(s.rework),
                      trend_direction="bad" if s.rework > 5 else "neutral",
                      tooltip="Откаты статуса в RELEASE squad — частый признак нестабильного scope релиза."),
        ),
        rx.box(height=SPACING["xl"]),
        section_header("Release Plan",
                       subtitle="Прогресс выполнения по релизным версиям"),
        _release_cards(releases),
        rx.box(height=SPACING["xl"]),
        section_header("Slipped Tasks",
                       subtitle="Задачи, сдвинутые относительно исходного срока"),
        _slipped_table(slipped),
        rx.box(height=SPACING["xl"]),
        section_header("Release Tasks", subtitle=f"Все задачи RELEASE squad · {len(tasks)} записей"),
        _tasks_table(tasks),
        padding=SPACING["xl"], max_width="1100px", margin="0 auto",
    )
