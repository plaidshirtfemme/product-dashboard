"""About project tab — onboarding for new dashboard readers."""

import reflex as rx
from ..tokens import SPACING


def about_tab() -> rx.Component:
    return rx.box(
        rx.text(
            "About project",
            size="5",
            weight="medium",
            color=rx.color("gray", 11),
        ),
        rx.text(
            "Описание проекта появится здесь.",
            size="2",
            color=rx.color("gray", 9),
            margin_top=SPACING["sm"],
        ),
        padding=f"0 2rem 2rem",
        max_width="1100px",
        margin="0 auto",
    )
