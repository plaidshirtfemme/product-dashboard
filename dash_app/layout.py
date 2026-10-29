"""Page layout — sidebar and tabs variants, page header."""

import reflex as rx
from .states import ProjectState
from .components import sidebar_nav
from .router import page_content
from .tokens import SPACING, ROLE

_SPACING_XL = SPACING["xl"]


def index() -> rx.Component:
    subtitle = rx.cond(
        ProjectState.project_mode == "kp",
        "Knowledge Pipeline — реальный соло-проект",
        "Симуляция Jira-интеграции · Демо для портфолио",
    )

    page_header = rx.box(
        rx.text(
            # DASH-165: временная заглушка вместо захардкоженного «Knowledge Pipeline»
            # (светился над всеми режимами). Полная параметризация по project_mode — позже.
            "project",
            style={"font_size": "11px", "font_weight": "600",
                   "text_transform": "uppercase", "letter_spacing": "0.08em"},
            color=ROLE["text-secondary"],
        ),
        rx.heading(
            "Product Dashboard",
            size="6",
            color=ROLE["text-primary"],
            margin_top="2px",
        ),
        rx.text(
            subtitle,
            size="1",
            color=ROLE["text-secondary"],
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

    return sidebar_layout
