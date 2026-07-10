"""Architecture tab — Real project mode."""

import reflex as rx
from ..components import section_header, real_page_header, real_page_wrapper
from ..data.real_project_extract import ADR_LIST
from ..tokens import SPACING, BORDER

_STATUS_COLOR = {
    "accepted":   "teal",
    "proposed":   "blue",
    "superseded": "gray",
}


def _adr_card(adr) -> rx.Component:
    color = _STATUS_COLOR.get(adr.status, "gray")
    return rx.box(
        rx.flex(
            rx.flex(
                rx.text(adr.id, size="1", weight="medium",
                        color=rx.color("gray", 9)),
                rx.badge(adr.status, color_scheme=color, variant="soft", size="1"),
                gap=SPACING["sm"],
                align="center",
            ),
            rx.text(adr.title, size="3", weight="medium",
                    color=rx.color("gray", 12), margin_top="4px"),
            direction="column",
            gap="2px",
        ),
        rx.box(height=SPACING["md"]),
        rx.flex(
            _adr_section("Контекст", adr.context, "circle-help", "amber"),
            _adr_section("Решение",  adr.decision, "circle-check", "teal"),
            _adr_section("Результат", adr.consequence, "trending-up", "blue"),
            direction="column",
            gap=SPACING["sm"],
        ),
        padding=SPACING["lg"],
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        background=rx.color("gray", 1),
        margin_bottom=SPACING["md"],
    )


def _adr_section(label: str, text: str, icon: str, color: str) -> rx.Component:
    return rx.flex(
        rx.icon(icon, size=14, color=rx.color(color, 9), flex_shrink="0",
                margin_top="2px"),
        rx.flex(
            rx.text(label, size="1", weight="medium",
                    color=rx.color("gray", 9), text_transform="uppercase",
                    letter_spacing="0.05em"),
            rx.text(text, size="2", color=rx.color("gray", 11),
                    line_height="1.6"),
            direction="column",
            gap="2px",
        ),
        gap=SPACING["sm"],
        align="start",
    )


def real_architecture_tab() -> rx.Component:
    return real_page_wrapper(
        real_page_header(f"{len(ADR_LIST)} Architecture Decision Records · из README.md"),
        section_header("Architecture Decision Records", "git-branch"),
        rx.box(height=SPACING["md"]),
        *[_adr_card(adr) for adr in ADR_LIST],
    )
