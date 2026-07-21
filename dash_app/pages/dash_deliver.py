"""Deliver tab (dash-mode only) — Double Diamond, этап 4.

Часть DASH-60. Working prototype уже существует — это сам дашборд (self-hosting).
Wireframes (DASH-62) и hi-fi макеты в Figma (DASH-63) — позже на этой неделе.
"""

import reflex as rx

from ..tokens import SPACING, PAGE_MAX_WIDTH
from ..components import section_header
from .motif_about import _placeholder

_MAX = PAGE_MAX_WIDTH


def dash_deliver_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Deliver",
            subtitle="Double Diamond · этап 4 — готовая поставка",
        ),
        _placeholder(
            "Working prototype — уже здесь: весь этот дашборд и есть поставленный продукт "
            "(self-hosting). Wireframes (DASH-62) и hi-fi макеты в Figma (DASH-63) — позже "
            "на этой неделе.",
        ),
        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
