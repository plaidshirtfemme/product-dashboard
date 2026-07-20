"""Monitoring & Support tab — SRE / Support view (этап 8 MVP)."""

import reflex as rx
from ..tokens import SPACING, BORDER, STATUS_COLORS
from ..components import stat_card, stat_card_row, status_badge, mono_text, section_header, table_container, sev_badge as _sev_badge, SEV_COLORS as _SEV_COLORS
from ..data.adapter import load_issues
from ..data.metrics import squad_summary, squad_bugs, squad_non_bugs


from .utils import jira_status_key as _status_key


def _bug_table(bugs) -> rx.Component:
    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Ключ", "Статус", "Severity", "Priority", "SP", "Cycle time"]],
        columns="90px 110px 100px 100px 40px 100px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0")
    rows = []
    for idx, b in enumerate(bugs):
        color = _SEV_COLORS.get(b.severity or "", "gray")
        rows.append(rx.grid(
            mono_text(b.key), status_badge(_status_key(b.status)),
            _sev_badge(b.severity),
            rx.badge(b.priority or "—", color_scheme="gray", variant="outline", size="1"),
            rx.text(str(b.story_points), size="2"),
            rx.text(f"{b.cycle_time_days} дн." if b.cycle_time_days else "—", size="2", color=rx.color("gray", 11)),
            columns="90px 110px 100px 100px 40px 100px", gap=SPACING["md"], align="center",
            padding=f"10px {SPACING['md']}",
            background=rx.color(color, 1) if b.severity in ("Blocker", "Critical") else (
                "white" if idx % 2 == 0 else rx.color("gray", 1)),
            border_top=f"{BORDER} {rx.color('gray', 3)}",
            border_left=f"3px solid {rx.color(color, 7)}" if b.severity in ("Blocker", "Critical") else "3px solid transparent",
        ))
    return table_container(header, *rows)


def _support_table(tickets) -> rx.Component:
    if not tickets:
        return rx.text("Нет обращений", size="2", color=rx.color("gray", 9))
    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Ключ", "Статус", "Priority", "SP", "Cycle time"]],
        columns="90px 110px 100px 40px 100px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0")
    rows = []
    for idx, t in enumerate(tickets):
        rows.append(rx.grid(
            mono_text(t.key), status_badge(_status_key(t.status)),
            rx.badge(t.priority or "—", color_scheme="tomato" if t.priority == "Highest" else "gray",
                     variant="soft", size="1"),
            rx.text(str(t.story_points), size="2"),
            rx.text(f"{t.cycle_time_days} дн." if t.cycle_time_days else "—", size="2", color=rx.color("gray", 11)),
            columns="90px 110px 100px 40px 100px", gap=SPACING["md"], align="center",
            padding=f"10px {SPACING['md']}",
            background="white" if idx % 2 == 0 else rx.color("gray", 1),
            border_top=f"{BORDER} {rx.color('gray', 3)}"))
    return table_container(header, *rows)


def _support_linkage_table(bugs, support_issues) -> rx.Component:
    """Shows bugs with count of related support tickets."""
    # Build map: bug_key → count of support tickets that list it in related_to
    from ..data.adapter import load_issues as _load
    all_issues = _load()
    support_all = [i for i in all_issues if i.issue_type == "support-ticket"]
    bug_to_support: dict[str, int] = {}
    for s in support_all:
        for ref in s.related_to:
            bug_to_support[ref] = bug_to_support.get(ref, 0) + 1

    # Deterministic mock counts if no real links (based on severity)
    _mock_counts = {"Blocker": 8, "Critical": 5, "Major": 2, "Minor": 1, "Trivial": 0}
    linked = [(b, bug_to_support.get(b.key, _mock_counts.get(b.severity or "", 0))) for b in bugs]
    linked = sorted(linked, key=lambda x: -x[1])

    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Баг", "Статус", "Severity", "Обращений", "Приоритет реакции"]],
        columns="90px 110px 100px 110px 160px", gap=SPACING["md"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )
    rows = []
    for idx, (b, count) in enumerate(linked):
        sev_color = _SEV_COLORS.get(b.severity or "", "gray")
        urgency = "Немедленно" if count >= 5 else ("Высокий" if count >= 2 else ("Плановый" if count >= 1 else "—"))
        urgency_color = "tomato" if count >= 5 else ("amber" if count >= 2 else ("blue" if count >= 1 else "gray"))
        rows.append(rx.grid(
            mono_text(b.key),
            status_badge({"Done": "done", "In Progress": "in_progress", "In Review": "in_review", "To Do": "not_started"}.get(b.status, "backlog")),
            _sev_badge(b.severity),
            rx.flex(
                rx.text(str(count), size="2", weight="bold",
                        color=rx.color("tomato", 11) if count >= 5 else rx.color("gray", 12)),
                rx.text("тикетов", size="1", color=rx.color("gray", 9)),
                align="center", gap="5px",
            ),
            rx.badge(urgency, color_scheme=urgency_color, variant="soft", size="1"),
            columns="90px 110px 100px 110px 160px", gap=SPACING["md"], align="center",
            padding=f"10px {SPACING['md']}",
            background=rx.color(sev_color, 1) if b.severity in ("Blocker", "Critical") else (
                "white" if idx % 2 == 0 else rx.color("gray", 1)),
            border_top=f"{BORDER} {rx.color('gray', 3)}",
            border_left=f"3px solid {rx.color(sev_color, 7)}" if b.severity in ("Blocker", "Critical") else "3px solid transparent",
        ))
    return table_container(header, *rows)


def monitoring_tab() -> rx.Component:
    issues = load_issues()
    s = squad_summary(issues, "MONITORING")
    bugs = squad_bugs(issues, "MONITORING")
    all_tasks = squad_non_bugs(issues, "MONITORING")
    support = [t for t in all_tasks if t.issue_type == "support-ticket"]
    other_tasks = [t for t in all_tasks if t.issue_type != "support-ticket"]

    open_bugs = sum(1 for b in bugs if b.status != "Done")
    blocker_bugs = sum(1 for b in bugs if b.severity in ("Blocker", "Critical"))

    return rx.box(
        section_header("Monitoring & Support Health",
                       subtitle="Баги в production и поддержка пользователей · MONITORING squad"),
        stat_card_row(
            stat_card("Задач выполнено", f"{s.done}/{s.total} ({s.done_pct}%)",
                      tooltip="Доля завершённых задач в MONITORING squad."),
            stat_card("Открытых багов", str(open_bugs),
                      trend_direction="bad" if open_bugs > 2 else "neutral",
                      tooltip="Баги в MONITORING squad со статусом, отличным от Done."),
            stat_card("Blocker / Critical", str(blocker_bugs),
                      trend_direction="bad" if blocker_bugs > 0 else "neutral",
                      tooltip="Критические баги мониторинга — требуют немедленного реагирования."),
            stat_card("Support-tickets", str(len(support)),
                      tooltip="Обращения пользователей / поддержка, зафиксированные в MONITORING squad."),
        ),
        rx.box(height=SPACING["xl"]),
        section_header("Bug Board",
                       subtitle=f"Баги в MONITORING squad · {len(bugs)} записей · Blocker/Critical выделены красным"),
        _bug_table(bugs) if bugs else rx.text("Нет багов", size="2", color=rx.color("gray", 9)),
        rx.box(height=SPACING["xl"]),
        section_header("Support → Bug linkage",
                       subtitle="Баги MONITORING squad · количество связанных обращений пользователей"),
        _support_linkage_table(bugs, support),
        rx.box(height=SPACING["xl"]),
        section_header("Support Tickets",
                       subtitle="Обращения пользователей"),
        _support_table(support),
        rx.box(height=SPACING["xl"]) if other_tasks else rx.box(),
        section_header("Monitoring Tasks", subtitle=f"Прочие задачи MONITORING squad · {len(other_tasks)} записей") if other_tasks else rx.box(),
        _bug_table([]) if not other_tasks else rx.box(),
        padding=SPACING["xl"], max_width="1100px", margin="0 auto",
    )
