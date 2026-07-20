"""Quality tab — QA Engineer view (этап 7 MVP)."""

from collections import Counter
import reflex as rx
from ..tokens import SPACING, BORDER, STATUS_COLORS
from ..components import stat_card, stat_card_row, status_badge, mono_text, section_header, table_container, progress_bar, sev_badge as _sev_badge, SEV_COLORS as _SEV_COLORS
from ..data.adapter import load_issues
from ..data.metrics import squad_summary, squad_bugs, squad_non_bugs, go_no_go_criteria

_SEV_ORDER = {"Blocker": 0, "Critical": 1, "Major": 2, "Minor": 3, "Trivial": 4}


from .utils import jira_status_key as _status_key


def _severity_distribution(all_bugs) -> rx.Component:
    counts = Counter(b.severity or "Unknown" for b in all_bugs)
    total = len(all_bugs)
    ordered = sorted(counts.items(), key=lambda x: _SEV_ORDER.get(x[0], 9))
    bars = []
    for sev, cnt in ordered:
        color = _SEV_COLORS.get(sev, "gray")
        pct = round(100 * cnt / total)
        bars.append(rx.flex(
            rx.box(rx.badge(sev, color_scheme=color, variant="soft", size="1"), width="90px", flex_shrink="0"),
            progress_bar(pct, color, 6, height="20px"),
            rx.text(f"{cnt} ({pct}%)", size="1", color=rx.color(color, 11),
                    style={"width": "70px", "text_align": "right", "flex_shrink": "0"}),
            align="center", gap=SPACING["sm"], width="100%"))

    return rx.box(rx.flex(*bars, direction="column", gap="10px"),
                  padding=SPACING["md"], background=rx.color("gray", 2),
                  border_radius="var(--radius-3)", width="100%")


def _bug_table(bugs) -> rx.Component:
    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Ключ", "Squad", "Статус", "Severity", "Priority", "SP", "Rework"]],
        columns="90px 120px 110px 100px 100px 40px 70px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0")
    rows = []
    for idx, b in enumerate(bugs):
        color = _SEV_COLORS.get(b.severity or "", "gray")
        rows.append(rx.grid(
            mono_text(b.key),
            rx.text(b.squad_key, size="2", color=rx.color("gray", 11)),
            status_badge(_status_key(b.status)),
            _sev_badge(b.severity),
            rx.badge(b.priority or "—", color_scheme="gray", variant="outline", size="1"),
            rx.text(str(b.story_points), size="2"),
            rx.badge(str(b.rework_count), color_scheme="tomato" if b.rework_count > 0 else "gray",
                     variant="soft", size="1"),
            columns="90px 120px 110px 100px 100px 40px 70px", gap=SPACING["md"], align="center",
            padding=f"10px {SPACING['md']}",
            background=rx.color(color, 1) if b.severity in ("Blocker", "Critical") else (
                "white" if idx % 2 == 0 else rx.color("gray", 1)),
            border_top=f"{BORDER} {rx.color('gray', 3)}",
            border_left=f"3px solid {rx.color(color, 7)}" if b.severity in ("Blocker", "Critical") else "3px solid transparent",
        ))
    return table_container(header, *rows)


def _tasks_table(tasks) -> rx.Component:
    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Ключ", "Статус", "SP", "Cycle time"]],
        columns="90px 110px 50px 100px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0")
    rows = []
    for idx, t in enumerate(tasks):
        rows.append(rx.grid(
            mono_text(t.key), status_badge(_status_key(t.status)),
            rx.text(str(t.story_points), size="2"),
            rx.text(f"{t.cycle_time_days} дн." if t.cycle_time_days else "—", size="2", color=rx.color("gray", 11)),
            columns="90px 110px 50px 100px", gap=SPACING["md"], align="center",
            padding=f"10px {SPACING['md']}",
            background="white" if idx % 2 == 0 else rx.color("gray", 1),
            border_top=f"{BORDER} {rx.color('gray', 3)}"))
    return table_container(header, *rows)


def _go_no_go_checklist(criteria) -> rx.Component:
    go = all(c.ok for c in criteria if c.critical)
    verdict_color = STATUS_COLORS["success"] if go else STATUS_COLORS["danger"]
    verdict_text = "GO — релиз разрешён" if go else "NO GO — релиз заблокирован"

    rows = []
    for c in criteria:
        icon_color = rx.color(STATUS_COLORS["success"], 9) if c.ok else (rx.color(STATUS_COLORS["danger"], 9) if c.critical else rx.color(STATUS_COLORS["warning"], 9))
        icon_name = "circle_check" if c.ok else "circle_x"
        rows.append(rx.flex(
            rx.icon(icon_name, size=16, color=icon_color, flex_shrink="0"),
            rx.flex(
                rx.text(c.label, size="2", weight="medium" if not c.ok else "regular",
                        color=rx.color(STATUS_COLORS["danger"], 11) if (not c.ok and c.critical) else rx.color("gray", 12)),
                rx.text(c.detail, size="1", color=rx.color("gray", 9)),
                direction="column",
                gap="2px",
                flex="1",
            ),
            rx.badge(
                "Критично" if c.critical else "Рекомендовано",
                color_scheme="tomato" if c.critical else "gray",
                variant="outline",
                size="1",
                flex_shrink="0",
            ),
            align="center",
            gap=SPACING["sm"],
            padding=f"10px {SPACING['md']}",
            background=rx.color(STATUS_COLORS["danger"], 2) if (not c.ok and c.critical) else "white",
            border_top=f"{BORDER} {rx.color('gray', 3)}",
            width="100%",
        ))

    header = rx.grid(
        *[rx.text(col, size="1", weight="medium", color=rx.color("gray", 9))
          for col in ["", "Критерий", "Важность"]],
        columns="28px 1fr 120px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}",
        background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )

    return rx.box(
        # verdict banner
        rx.flex(
            rx.icon("circle_check" if go else "circle_x", size=20,
                    color=rx.color(verdict_color, 11)),
            rx.text(verdict_text, size="3", weight="bold",
                    color=rx.color(verdict_color, 11)),
            align="center",
            gap=SPACING["sm"],
            padding=SPACING["md"],
            background=rx.color(verdict_color, 2),
            border=f"{BORDER} {rx.color(verdict_color, 5)}",
            border_radius="var(--radius-2)",
            margin_bottom=SPACING["md"],
        ),
        table_container(
            header,
            *rows
    ),
        width="100%",
    )


def quality_tab() -> rx.Component:
    issues = load_issues()
    s = squad_summary(issues, "QUALITY")
    all_bugs = squad_bugs(issues)          # all bugs across project
    quality_bugs = squad_bugs(issues, "QUALITY")
    tasks = squad_non_bugs(issues, "QUALITY")
    criteria = go_no_go_criteria(issues)

    blocker_count = sum(1 for b in all_bugs if b.severity == "Blocker")
    open_bugs = sum(1 for b in all_bugs if b.status != "Done")

    return rx.box(
        section_header("Quality Health",
                       subtitle="Метрики качества · баги по severity · QUALITY squad"),
        stat_card_row(
            stat_card("Всего багов (проект)", str(len(all_bugs)),
                      tooltip="Суммарное число задач типа bug по всем 9 squad."),
            stat_card("Открытых багов", str(open_bugs),
                      trend_direction="bad" if open_bugs > 5 else "neutral",
                      tooltip="Баги со статусом, отличным от Done."),
            stat_card("Blocker / Critical", str(blocker_count),
                      trend_direction="bad" if blocker_count > 0 else "neutral",
                      tooltip="Критические баги, блокирующие релиз или пользователей."),
            stat_card("QA задач выполнено", f"{s.done}/{s.total}",
                      tooltip="Задачи QUALITY squad: Done / всего."),
        ),
        rx.box(height=SPACING["xl"]),
        section_header("Bug Severity Distribution",
                       subtitle=f"Все {len(all_bugs)} багов по severity · по всему проекту"),
        _severity_distribution(all_bugs),
        rx.box(height=SPACING["xl"]),
        section_header("Bug Register",
                       subtitle=f"Все баги проекта · {len(all_bugs)} записей · отсортировано по severity"),
        _bug_table(all_bugs),
        rx.box(height=SPACING["xl"]),
        section_header("QA Tasks", subtitle=f"Задачи QUALITY squad (без багов) · {len(tasks)} записей"),
        _tasks_table(tasks),
        rx.box(height=SPACING["xl"]),
        section_header("Go / No-Go Checklist",
                       subtitle="Критерии готовности к релизу · проверяется перед каждым деплоем"),
        _go_no_go_checklist(criteria),
        padding=SPACING["xl"], max_width="1100px", margin="0 auto",
    )
