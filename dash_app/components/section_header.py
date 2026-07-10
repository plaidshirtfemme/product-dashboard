"""
SectionHeader — divides a tab into named blocks (e.g. on the Analysis tab:
"BA" section header, then "SA" section header below it). Optional action
slot for things like "Открыть спринт ->" buttons.

Usage:
    section_header("Специфичные метрики SA", subtitle="Этап 6")
    section_header("Реестр требований", action=rx.button("Добавить"))
"""

import reflex as rx
from ..tokens.tokens import SPACING, TYPE_SCALE, BORDER


def section_header(
    title: str,
    subtitle: str | None = None,
    action: rx.Component | None = None,
) -> rx.Component:
    return rx.flex(
        rx.flex(
            rx.text(title, style={"font_size": TYPE_SCALE["heading"], "font_weight": "500"}),
            rx.text(subtitle, size="1", color=rx.color("gray", 9)) if subtitle is not None else rx.fragment(),
            direction="column",
            gap="2px",
        ),
        action if action is not None else rx.fragment(),
        justify="between",
        align="center",
        width="100%",
        padding_y=SPACING["md"],
        border_bottom=f"{BORDER} {rx.color('gray', 4)}",
        margin_bottom=SPACING["md"],
    )
