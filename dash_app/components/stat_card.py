"""
StatCard — headline number card used on every tab.

Usage:
    stat_card("Cycle time", "3.2 дня", trend="-0.4д", trend_direction="good",
              tooltip="Среднее время от первого 'In Progress' до 'Done'")
    stat_card("Blocked tickets", "2", trend_direction="bad",
              tooltip="Задачи с активной блокировкой (issuelinks типа 'Blocks')")

trend_direction:
  "good"    → green trend text
  "bad"     → red trend text + red left border on the card
  "neutral" → grey, no border
"""

import reflex as rx
from ..tokens.tokens import SPACING, TYPE_SCALE, STATUS_COLORS


def stat_card(
    label: str,
    value: str,
    *,
    trend: str | None = None,
    trend_direction: str = "neutral",  # "good" | "bad" | "neutral"
    icon: str | None = None,
    tooltip: str | None = None,
) -> rx.Component:
    trend_color = {
        "good": STATUS_COLORS["success"],
        "bad": STATUS_COLORS["danger"],
        "neutral": STATUS_COLORS["neutral"],
    }[trend_direction]

    # Info icon with tooltip — only rendered when tooltip text is provided.
    info_icon = (
        rx.tooltip(
            rx.icon("info", size=13, color=rx.color("gray", 8)),
            content=tooltip,
        )
        if tooltip
        else rx.fragment()
    )

    return rx.box(
        rx.flex(
            rx.flex(
                rx.text(
                    label,
                    size="1",
                    color=rx.color("gray", 10),
                    style={
                        "font_size": TYPE_SCALE["label"],
                        "text_transform": "uppercase",
                        "letter_spacing": "0.03em",
                    },
                ),
                info_icon,
                gap="4px",
                align="center",
            ),
            rx.icon(icon, size=16, color=rx.color("gray", 9)) if icon else rx.fragment(),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.text(
            value,
            style={
                "font_size": TYPE_SCALE["value"],
                "font_weight": "500",
                "color": "var(--tomato-11)" if trend_direction == "bad" else "inherit",
            },
            margin_top=SPACING["xs"],
        ),
        rx.text(
            trend,
            size="1",
            color=rx.color(trend_color, 9),
            margin_top=SPACING["xs"],
        ) if trend is not None else rx.fragment(),
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
        border_left="3px solid var(--tomato-9)" if trend_direction == "bad" else "3px solid transparent",
        padding=SPACING["md"],
        width="100%",
    )


def stat_card_row(*cards: rx.Component) -> rx.Component:
    """Responsive grid wrapper for a row of stat_card()s. 2-4 per row."""
    return rx.grid(
        *cards,
        columns=rx.breakpoints(initial="2", md=str(len(cards))),
        gap=SPACING["md"],
        width="100%",
    )
