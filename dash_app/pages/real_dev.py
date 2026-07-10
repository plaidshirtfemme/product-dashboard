"""Dev & Pipeline tab — Real project mode."""

import reflex as rx
from ..components import section_header, data_table, real_page_header, real_page_wrapper
from ..data.real_project_extract import GIT_COMMITS, EXCEPTIONS
from ..tokens import SPACING, BORDER

_CAT_COLOR = {
    "feat":     "teal",
    "refactor": "blue",
    "fix":      "amber",
    "chore":    "gray",
    "security": "red",
}
_CAT_LABEL = {
    "feat":     "feat",
    "refactor": "refactor",
    "fix":      "fix",
    "chore":    "chore",
    "security": "security",
}


def _commit_row(c) -> rx.Component:
    color = _CAT_COLOR.get(c.category, "gray")
    return rx.flex(
        rx.text(c.date, size="1", color=rx.color("gray", 8),
                min_width="90px", font_family="monospace"),
        rx.text(c.sha,  size="1", color=rx.color("teal", 9),
                min_width="60px", font_family="monospace"),
        rx.badge(_CAT_LABEL.get(c.category, c.category),
                 color_scheme=color, variant="soft", size="1",
                 min_width="70px"),
        rx.text(c.message, size="2", color=rx.color("gray", 11),
                flex="1"),
        gap=SPACING["md"],
        align="center",
        padding=f"8px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


def _exception_row(e) -> rx.Component:
    return rx.flex(
        rx.text(e.name, size="2", weight="medium", color=rx.color("teal", 10),
                font_family="monospace", min_width="260px"),
        rx.text(e.description, size="2", color=rx.color("gray", 11), flex="1"),
        rx.text(e.raised_by, size="1", color=rx.color("gray", 8),
                font_family="monospace"),
        gap=SPACING["md"],
        align="center",
        padding=f"8px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


def real_dev_tab() -> rx.Component:
    feat_count     = sum(1 for c in GIT_COMMITS if c.category == "feat")
    security_count = sum(1 for c in GIT_COMMITS if c.category == "security")

    return real_page_wrapper(
        real_page_header("git log + exceptions.py · knowledge-pipeline"),

        # Git history
        section_header(f"Git history · {len(GIT_COMMITS)} коммитов", "git-commit-horizontal"),
        rx.flex(
            rx.flex(
                rx.text(str(feat_count), size="5", weight="bold",
                        color=rx.color("teal", 9)),
                rx.text("feat", size="1", color=rx.color("gray", 9)),
                direction="column", align="center",
                padding=f"12px {SPACING['lg']}",
                border=f"{BORDER} {rx.color('gray', 4)}",
                border_radius="var(--radius-2)",
            ),
            rx.flex(
                rx.text(str(security_count), size="5", weight="bold",
                        color=rx.color("red", 9)),
                rx.text("security", size="1", color=rx.color("gray", 9)),
                direction="column", align="center",
                padding=f"12px {SPACING['lg']}",
                border=f"{BORDER} {rx.color('gray', 4)}",
                border_radius="var(--radius-2)",
            ),
            rx.flex(
                rx.text("3", size="5", weight="bold", color=rx.color("gray", 9)),
                rx.text("дня", size="1", color=rx.color("gray", 9)),
                direction="column", align="center",
                padding=f"12px {SPACING['lg']}",
                border=f"{BORDER} {rx.color('gray', 4)}",
                border_radius="var(--radius-2)",
            ),
            gap=SPACING["md"],
            margin_bottom=SPACING["md"],
        ),
        rx.box(
            *[_commit_row(c) for c in reversed(GIT_COMMITS)],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
        ),

        rx.box(height=SPACING["xl"]),

        # Typed exceptions
        section_header(f"Typed exceptions · {len(EXCEPTIONS)} классов", "triangle-alert"),
        rx.callout(
            "Вместо разбора текста ошибок по подстрокам — иерархия typed exceptions. "
            "Ловятся по типу, не по regex. Текст остаётся только для лога.",
            icon="info",
            color_scheme="teal",
            variant="soft",
            size="1",
            margin_bottom=SPACING["md"],
        ),
        rx.box(
            *[_exception_row(e) for e in EXCEPTIONS],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
        ),

    )
