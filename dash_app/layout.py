"""Page layout — sidebar and tabs variants, page header."""

import reflex as rx
from .states import NavState, ProjectState
from .components import sidebar_nav, tabs_nav
from .router import page_content
from .tokens import SPACING

_SPACING_XL = SPACING["xl"]


def index() -> rx.Component:
    subtitle = rx.cond(
        ProjectState.project_mode == "real",
        "Knowledge Pipeline — реальный соло-проект",
        "Симуляция Jira-интеграции · Демо для портфолио",
    )

    page_header = rx.box(
        rx.text(
            "Knowledge Pipeline",
            style={"font_size": "11px", "font_weight": "600",
                   "text_transform": "uppercase", "letter_spacing": "0.08em"},
            color=rx.color("gray", 9),
        ),
        rx.heading(
            "Product Dashboard",
            size="6",
            color=rx.color("gray", 12),
            margin_top="2px",
        ),
        rx.text(
            subtitle,
            size="1",
            color=rx.color("gray", 9),
            margin_top="2px",
        ),
        padding=f"1.5rem {_SPACING_XL} 0",
        max_width="1100px",
        margin="0 auto",
    )

    sidebar_layout = rx.flex(
        sidebar_nav(),
        rx.box(
            page_header,
            rx.box(height=_SPACING_XL),
            page_content,
            flex="1",
            overflow_y="auto",
            height="100vh",
        ),
        width="100%",
        overflow="hidden",
    )

    tabs_layout = rx.box(
        tabs_nav(),
        rx.box(
            page_header,
            rx.box(height=_SPACING_XL),
            page_content,
        ),
        width="100%",
    )

    return rx.cond(
        NavState.nav_variant == "sidebar",
        sidebar_layout,
        tabs_layout,
    )
