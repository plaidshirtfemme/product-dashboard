"""
ChartWrapper — consistent card frame around every chart (velocity trend,
AARRR funnel, error trends, cycle time distribution, etc). Keeps title
placement, height, and card chrome identical across all 11 tabs so charts
don't each reinvent their own header/padding.

Usage:
    chart_wrapper(
        title="Velocity по неделям",
        chart=rx.recharts.line_chart(...),
        subtitle="Заметок обработано в неделю",
    )
"""

import reflex as rx
from ..tokens.tokens import SPACING, BORDER


def chart_wrapper(
    title: str,
    chart: rx.Component,
    subtitle: str | None = None,
    height: int = 260,
) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.text(title, weight="medium", size="3"),
            rx.text(subtitle, size="1", color=rx.color("gray", 9)) if subtitle is not None else rx.fragment(),
            direction="column",
            gap="2px",
            margin_bottom=SPACING["sm"],
        ),
        rx.box(chart, height=f"{height}px", width="100%"),
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        padding=SPACING["md"],
        width="100%",
    )
