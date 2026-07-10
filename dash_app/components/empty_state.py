"""Reusable empty state component for tabs without real data."""

import reflex as rx
from ..tokens import SPACING


def empty_state(
    title: str,
    reason: str,
    icon: str = "inbox",
    mode: str = "demo_only",  # "demo_only" | "coming_soon" | "no_data"
) -> rx.Component:
    """
    Centered empty state with icon, title, explanation, and mode badge.

    Args:
        title:  Short noun phrase describing what's absent, e.g. "Business Analysis data"
        reason: One or two sentences explaining WHY it's absent — be honest and specific.
                Good: "В соло-проекте не было внешних стейкхолдеров, поэтому формального
                       BA-хендоффа не существует."
                Bad:  "Данные недоступны."
        icon:   Lucide icon name (hyphen-separated).
        mode:   Controls the badge colour and label.
    """
    _mode_cfg = {
        "demo_only":    ("Только демо",         "amber"),
        "coming_soon":  ("Скоро",               "blue"),
        "no_data":      ("Нет данных",           "gray"),
    }
    badge_label, badge_color = _mode_cfg.get(mode, _mode_cfg["no_data"])

    return rx.box(
        rx.flex(
            rx.box(
                rx.icon(icon, size=32, color=rx.color("gray", 6)),
                margin_bottom=SPACING["md"],
            ),
            rx.badge(
                badge_label,
                color_scheme=badge_color,
                variant="soft",
                size="2",
                margin_bottom=SPACING["sm"],
            ),
            rx.text(
                title,
                size="4",
                weight="medium",
                color=rx.color("gray", 11),
                text_align="center",
                margin_bottom=SPACING["sm"],
            ),
            rx.text(
                reason,
                size="2",
                color=rx.color("gray", 9),
                text_align="center",
                max_width="480px",
                line_height="1.6",
            ),
            direction="column",
            align="center",
            justify="center",
            padding=f"{SPACING['xl']} {SPACING['md']}",
            min_height="280px",
        ),
        background=rx.color("gray", 1),
        border=f"1px dashed {rx.color('gray', 5)}",
        border_radius="var(--radius-3)",
        width="100%",
    )
