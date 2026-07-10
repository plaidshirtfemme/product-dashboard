"""Monitoring tab — Real project mode."""

import reflex as rx
from ..components import section_header, stat_card, stat_card_row, real_page_header, real_page_wrapper
from ..data.real_project_extract import (
    BATCH_SESSIONS,
    TOTAL_URLS_PROCESSED, TOTAL_NOTES_CREATED, TOTAL_IP_BLOCKS,
    TOTAL_TOO_LONG, TOTAL_NO_TEXT, TOTAL_ERRORS,
)
from ..tokens import SPACING, BORDER


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{round(part / total * 100, 1)}%"


def _session_row(s) -> rx.Component:
    success_rate = _pct(s.created, s.total_urls)
    ip_rate      = _pct(s.ip_blocks, s.total_urls)
    is_big = s.total_urls > 100
    return rx.flex(
        rx.flex(
            rx.text(f"{s.date} {s.time}", size="1", color=rx.color("gray", 8),
                    font_family="monospace", min_width="110px"),
            rx.badge(
                "main batch" if is_big else "test run",
                color_scheme="teal" if is_big else "gray",
                variant="soft", size="1",
            ),
            gap=SPACING["sm"],
            align="center",
            min_width="180px",
        ),
        rx.text(str(s.total_urls), size="2", color=rx.color("gray", 11),
                min_width="50px", text_align="right"),
        rx.text(f"{s.created} ({success_rate})", size="2",
                color=rx.color("teal", 9), min_width="90px", text_align="right"),
        rx.text(str(s.too_long), size="2", color=rx.color("gray", 9),
                min_width="50px", text_align="right"),
        rx.text(f"{s.ip_blocks} ({ip_rate})", size="2",
                color=rx.color("amber", 9) if s.ip_blocks > 0 else rx.color("gray", 7),
                min_width="80px", text_align="right"),
        rx.text(str(s.no_text), size="2", color=rx.color("gray", 9),
                min_width="50px", text_align="right"),
        gap=SPACING["lg"],
        align="center",
        padding="8px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
        _hover={"background": rx.color("gray", 2)},
    )


def _table_header() -> rx.Component:
    cols = ["Сессия", "URLs", "Создано", ">40 мин", "IP-блоки", "Нет текста"]
    widths = ["180px", "50px", "90px", "50px", "80px", "50px"]
    return rx.flex(
        *[
            rx.text(c, size="1", weight="medium", color=rx.color("gray", 8),
                    text_transform="uppercase", letter_spacing="0.05em",
                    min_width=w, text_align="right" if i > 0 else "left")
            for i, (c, w) in enumerate(zip(cols, widths))
        ],
        gap=SPACING["lg"],
        padding="6px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 5)}",
    )


def real_monitoring_tab() -> rx.Component:
    ip_rate   = _pct(TOTAL_IP_BLOCKS, TOTAL_URLS_PROCESSED)
    succ_rate = _pct(TOTAL_NOTES_CREATED, TOTAL_URLS_PROCESSED)

    return real_page_wrapper(
        real_page_header(f"{len(BATCH_SESSIONS)} batch-сессий · logs/ · knowledge-pipeline"),

        # Aggregate stats
        section_header("Итого по всем сессиям", "activity"),
        stat_card_row(
            stat_card("URLs обработано",   str(TOTAL_URLS_PROCESSED),              icon="link"),
            stat_card("Заметок создано",   f"{TOTAL_NOTES_CREATED} ({succ_rate})", trend_direction="good", icon="file-text"),
            stat_card("IP-блоков",         f"{TOTAL_IP_BLOCKS} ({ip_rate})",       icon="shield-off"),
            stat_card("Пропущено >40 мин", str(TOTAL_TOO_LONG),                    icon="clock"),
        ),

        rx.box(height=SPACING["xl"]),

        # Error breakdown callout
        section_header("Типы ошибок", "triangle-alert"),
        rx.flex(
            _error_badge("IP-блоки YouTube (VPN)", TOTAL_IP_BLOCKS,    TOTAL_ERRORS, "amber"),
            _error_badge("Видео >40 мин",           TOTAL_TOO_LONG,     TOTAL_ERRORS, "gray"),
            _error_badge("Нет текста/субтитров",    TOTAL_NO_TEXT,      TOTAL_ERRORS, "red"),
            gap=SPACING["md"],
            flex_wrap="wrap",
            margin_top=SPACING["sm"],
            margin_bottom=SPACING["xl"],
        ),

        # Sessions table
        section_header(f"Batch sessions · {len(BATCH_SESSIONS)} прогонов", "database"),
        rx.box(
            _table_header(),
            *[_session_row(s) for s in BATCH_SESSIONS],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
            overflow_x="auto",
        ),

        rx.callout(
            "Главный прогон (S7, 22:07) — 704 URLs, батч из 36 порций по 20, "
            "пауза 10 мин между ними. IP-блоки сосредоточены в конце прогона: "
            "YouTube начинает блокировать после ~600 запросов с одного VPN-IP.",
            icon="info",
            color_scheme="gray",
            variant="soft",
            size="1",
            margin_top=SPACING["md"],
        ),

    )


def _error_badge(label: str, count: int, total: int, color: str) -> rx.Component:
    pct = _pct(count, total)
    return rx.flex(
        rx.text(str(count), size="5", weight="bold", color=rx.color(color, 9)),
        rx.text(label, size="1", color=rx.color("gray", 9)),
        rx.text(f"{pct} ошибок", size="1", color=rx.color("gray", 7)),
        direction="column",
        align="center",
        padding=f"{SPACING['md']} {SPACING['lg']}",
        border=f"{BORDER} {rx.color(color, 4)}",
        border_radius="var(--radius-3)",
        background=rx.color(color, 1),
        min_width="160px",
    )
