"""Shared low-level components reused across multiple page files."""

import reflex as rx
from ..tokens import SPACING, BORDER, STATUS_COLORS, PAGE_MAX_WIDTH

_GAP_THRESHOLD = 5


def real_page_wrapper(*children: rx.Component) -> rx.Component:
    """Standard outer box for all real_* tabs: padding, max_width, center."""
    return rx.box(
        *children,
        padding=f"0 {SPACING['xl']} {SPACING['xl']}",
        max_width=PAGE_MAX_WIDTH,
        margin="0 auto",
    )


def real_page_header(subtitle: str) -> rx.Component:
    """'Real project' badge + source subtitle shown at the top of every real_* tab."""
    return rx.flex(
        rx.badge("Real project", color_scheme="teal", variant="soft", size="1"),
        rx.text(subtitle, size="1", color=rx.color("gray", 9)),
        gap=SPACING["sm"],
        align="center",
        padding=f"0 0 {SPACING['md']}",
    )


def progress_bar(
    pct: int,
    color: str = "teal",
    shade: int = 6,
    height: str = "16px",
    min_pct: int = 2,
) -> rx.Component:
    """Horizontal bar showing `pct`% fill. Use inside a flex row alongside a label."""
    return rx.box(
        rx.box(
            height=height,
            background=rx.color(color, shade),
            border_radius="var(--radius-1)",
            width=f"{max(pct, min_pct)}%",
        ),
        flex="1",
        background=rx.color("gray", 3),
        border_radius="var(--radius-1)",
        height=height,
        overflow="hidden",
    )


def vault_coverage_chart(
    folders: list[tuple[str, int]],
    gap_threshold: int = _GAP_THRESHOLD,
) -> rx.Component:
    """Horizontal bar chart of note counts per vault folder. Red = gap (below threshold)."""
    folders = sorted(folders, key=lambda x: x[1])
    max_count = max(c for _, c in folders) if folders else 1
    gap_count = sum(1 for _, c in folders if c < gap_threshold)

    bars = [
        rx.flex(
            rx.text(
                name,
                size="1",
                color=rx.color(STATUS_COLORS["danger"], 11) if count < gap_threshold else rx.color("gray", 11),
                width="180px",
                flex_shrink="0",
                style={"font_family": "monospace"},
            ),
            progress_bar(
                pct=round(100 * count / max_count),
                color=STATUS_COLORS["danger"] if count < gap_threshold else "teal",
                shade=7 if count < gap_threshold else 6,
            ),
            rx.text(
                str(count),
                size="1",
                color=rx.color(STATUS_COLORS["danger"], 11) if count < gap_threshold else rx.color("gray", 9),
                width="36px",
                text_align="right",
                flex_shrink="0",
            ),
            align="center",
            gap=SPACING["sm"],
            width="100%",
        )
        for name, count in folders
    ]

    return rx.box(
        rx.flex(
            rx.badge(
                f"⚠ {gap_count} папок < {gap_threshold} заметок",
                color_scheme="tomato", variant="soft", size="1",
            ) if gap_count else rx.box(),
            rx.text(f"Всего папок: {len(folders)}", size="1", color=rx.color("gray", 9)),
            justify="between",
            align="center",
            margin_bottom=SPACING["md"],
        ),
        rx.flex(*bars, direction="column", gap="8px"),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
        width="100%",
    )


def table_header(labels: list[str], columns: str) -> rx.Component:
    """Standard table header row: gray-2 background, rounded top corners."""
    return rx.grid(
        *[rx.text(label, size="1", weight="medium", color=rx.color("gray", 9)) for label in labels],
        columns=columns,
        gap=SPACING["md"],
        padding=f"8px {SPACING['md']}",
        background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )


def table_container(*children, **kwargs) -> rx.Component:
    """Wraps header + rows with standard border, radius, overflow."""
    return rx.box(
        *children,
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-2)",
        overflow="hidden",
        width="100%",
        **kwargs,
    )


def color_legend(
    items: list[tuple[str, str]],
    dot_size: str = "10px",
    shade: int = 7,
) -> rx.Component:
    """Colored-dot + label legend. items = [(radix_color_name, label), ...]."""
    return rx.flex(
        *[
            rx.flex(
                rx.box(
                    width=dot_size, height=dot_size,
                    background=rx.color(color, shade),
                    border_radius="var(--radius-1)",
                    flex_shrink="0",
                ),
                rx.text(label, size="1", color=rx.color("gray", 10)),
                align="center",
                gap=SPACING["xs"],
            )
            for color, label in items
        ],
        gap=SPACING["md"],
        wrap="wrap",
        padding=f"{SPACING['sm']} 0",
    )
