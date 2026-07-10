"""
DataTable — generic table used for: requirements registry, research journal,
needs_review list, sprint backlogs, decision log, etc.

Deliberately dumb: takes columns + rows already formatted (badges, mono IDs,
etc. are built by the caller and passed in as cell content). Keeps this
component reusable across very different data shapes instead of special-
casing every tab's fields here.

Usage:
    data_table(
        columns=["ID", "Требование", "Источник", "Статус"],
        rows=[
            [mono_text("REQ-014"), "Фильтр по source_type", "Research insight", status_badge("done")],
            ...
        ],
    )
"""

import reflex as rx
from ..tokens.tokens import SPACING, FONTS


def mono_text(value: str) -> rx.Component:
    """Helper: renders IDs/timestamps in the monospace token face."""
    return rx.text(value, style={"font_family": FONTS["mono"], "font_size": "13px"})


def data_table(
    columns: list[str],
    rows: list[list[rx.Component | str]],
    empty_message: str = "Нет данных",
) -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[
                        rx.table.column_header_cell(col, style={"color": rx.color("gray", 10)})
                        for col in columns
                    ]
                )
            ),
            rx.table.body(
                *[
                    rx.table.row(*[rx.table.cell(cell) for cell in row])
                    for row in rows
                ]
            ),
            variant="surface",
            width="100%",
        )
        if rows
        else rx.text(empty_message, color=rx.color("gray", 9), padding=SPACING["md"]),
        width="100%",
    )
