"""
FilterBar — the per-page filter row (date range, squad, source_type, severity
etc). Written once, reused on every tab per the original Streamlit plan
(st.sidebar reused across pages) — this is the Reflex equivalent.

Usage:
    filter_bar([
        rx.select(["Все команды", "Research", "Design", ...], placeholder="Команда"),
        date_range_picker(...),
    ])
"""

import reflex as rx
from ..tokens.tokens import SPACING, BORDER


def filter_bar(controls: list[rx.Component]) -> rx.Component:
    return rx.flex(
        *controls,
        gap=SPACING["sm"],
        align="center",
        wrap="wrap",
        padding_bottom=SPACING["md"],
        margin_bottom=SPACING["md"],
        border_bottom=f"{BORDER} {rx.color('gray', 4)}",
        width="100%",
    )
