"""
Badge — status pills used for sprint status, squad health, task status,
research journal status, etc. Single source of the traffic-light mapping
so "green means done" is consistent across all 11 tabs.

Usage:
    status_badge("done")           -> green "Готово"
    status_badge("blocked")        -> red "Заблокировано"
    status_badge("in_progress")    -> amber "В работе"
"""

import reflex as rx
from ..tokens.tokens import STATUS_COLORS, RADIUS

_STATUS_MAP: dict[str, tuple[str, str]] = {
    "done": ("success", "Готово"),
    "on_track": ("success", "В графике"),
    "in_progress": ("warning", "В работе"),
    "in_review": ("info", "На ревью"),
    "at_risk": ("warning", "Риск срыва"),
    "blocked": ("danger", "Заблокировано"),
    "overdue": ("danger", "Просрочено"),
    "backlog": ("neutral", "В бэклоге"),
    "not_started": ("neutral", "Не начато"),
}


def status_badge(status: str, label: str | None = None) -> rx.Component:
    tone, default_label = _STATUS_MAP.get(status, ("neutral", status))
    color = STATUS_COLORS[tone]
    return rx.box(
        rx.text(label or default_label, size="1", weight="medium"),
        background=rx.color(color, 3),
        color=rx.color(color, 11),
        padding="4px 10px",
        border_radius=RADIUS["full"],
        display="inline-block",
        width="fit-content",
    )


def badge_group(*statuses: str) -> rx.Component:
    return rx.flex(*[status_badge(s) for s in statuses], gap="8px", wrap="wrap")


# ---------------------------------------------------------------------------
# Data-source badge — separate from status_badge above. This is not about
# task status, it's about honesty: does this metric come from the real
# Knowledge Pipeline project, or from the simulated Jira integration?
# Every stat_card / chart_wrapper on every tab should carry one of these.
# See HANDOFF doc, "Смешение реальных и смоделированных данных" for why
# this exists — mixing real and mocked metrics on one dashboard is fine
# as long as it's visibly labeled, not fine if it's silently blended.
# ---------------------------------------------------------------------------

_SOURCE_MAP: dict[str, tuple[str, str, str]] = {
    # key -> (icon, label, tone)
    "real": ("database", "Реальные данные проекта", "success"),
    "mock": ("flask_conical", "Демо (модель Jira-интеграции)", "info"),
}


# ---------------------------------------------------------------------------
# Severity badge — shared across Dev, Monitoring, Quality tabs
# ---------------------------------------------------------------------------

SEV_COLORS: dict[str, str] = {
    "Blocker":  STATUS_COLORS["danger"],
    "Critical": STATUS_COLORS["danger"],
    "Major":    STATUS_COLORS["warning"],
    "Minor":    STATUS_COLORS["warning"],
    "Trivial":  "gray",
}


def sev_badge(severity: str | None) -> rx.Component:
    s = severity or "—"
    return rx.badge(s, color_scheme=SEV_COLORS.get(s, "gray"), variant="soft", size="1")


def data_source_badge(source: str) -> rx.Component:
    icon, label, tone = _SOURCE_MAP.get(source, _SOURCE_MAP["mock"])
    color = STATUS_COLORS[tone]
    return rx.flex(
        rx.icon(icon, size=12, color=rx.color(color, 11)),
        rx.text(label, size="1", color=rx.color(color, 11)),
        gap="4px",
        align="center",
        display="inline-flex",
    )
