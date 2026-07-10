"""Overview tab — Real project mode."""

import reflex as rx
from ..components import stat_card, stat_card_row, section_header, data_source_badge, real_page_header, real_page_wrapper
from ..data.real_project_extract import (
    TOTAL_URLS_PROCESSED, TOTAL_NOTES_CREATED, TOTAL_IP_BLOCKS,
    TOTAL_TOO_LONG, TOTAL_NO_TEXT, PROJECT_DESCRIPTION, STACK,
    BATCH_SESSIONS,
)
from ..data.vault_snapshot import TOTAL_NOTES, SNAPSHOT_DATE
from ..tokens import SPACING, BORDER


def real_overview_tab() -> rx.Component:
    success_rate = round(TOTAL_NOTES_CREATED / TOTAL_URLS_PROCESSED * 100, 1)
    ip_rate      = round(TOTAL_IP_BLOCKS      / TOTAL_URLS_PROCESSED * 100, 1)

    stack_rows = [
        rx.flex(
            rx.text(tech, size="2", weight="medium", color=rx.color("gray", 12),
                    min_width="200px"),
            rx.text(role, size="2", color=rx.color("gray", 9)),
            gap=SPACING["md"],
            align="start",
            padding=f"6px 0",
            border_bottom=f"{BORDER} {rx.color('gray', 3)}",
        )
        for tech, role in STACK
    ]

    return real_page_wrapper(
        real_page_header(f"Knowledge Pipeline · снэпшот {SNAPSHOT_DATE}"),

        # Batch metrics
        section_header("Batch run · главный прогон", "database"),
        stat_card_row(
            stat_card("URLs в батче",      str(TOTAL_URLS_PROCESSED), icon="link"),
            stat_card("Заметок создано",   str(TOTAL_NOTES_CREATED),  trend=f"+{success_rate}%", trend_direction="good", icon="file-text"),
            stat_card("IP-блоков YouTube", str(TOTAL_IP_BLOCKS),      trend=f"{ip_rate}% от батча", icon="shield-off"),
            stat_card("Пропущено >40 мин", str(TOTAL_TOO_LONG),       trend="нет субтитров", icon="clock"),
        ),

        rx.box(height=SPACING["xl"]),

        # Vault snapshot
        section_header("Vault Obsidian", "book-open"),
        stat_card_row(
            stat_card("Заметок в vault", str(TOTAL_NOTES),          icon="file-text"),
            stat_card("Сессий батча",    str(len(BATCH_SESSIONS)),   icon="database"),
            stat_card("Без текста",      str(TOTAL_NO_TEXT),         trend="no subtitles + no description", icon="circle-x"),
        ),

        rx.box(height=SPACING["xl"]),

        # Project description
        section_header("О проекте", "info"),
        rx.box(
            rx.text(PROJECT_DESCRIPTION, size="2", color=rx.color("gray", 11),
                    line_height="1.7"),
            padding=f"{SPACING['md']} 0",
        ),

        rx.box(height=SPACING["xl"]),

        # Stack
        section_header("Стек", "layers"),
        rx.box(*stack_rows, margin_top=SPACING["sm"]),

    )
