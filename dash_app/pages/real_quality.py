"""Quality tab — Real project mode."""

import reflex as rx
from ..components import section_header, stat_card, stat_card_row, real_page_header, real_page_wrapper
from ..data.real_project_extract import TESTS, QUALITY_ITEMS
from ..tokens import SPACING, BORDER

_STATUS_COLOR = {"done": "teal", "open": "amber", "planned": "blue"}
_PRIORITY_COLOR = {"high": "red", "medium": "amber", "low": "gray"}


def _test_row(t) -> rx.Component:
    color = "teal" if "test_enrich" in t.module else "blue"
    return rx.flex(
        rx.icon("circle-check", size=14, color=rx.color("teal", 8)),
        rx.text(t.name, size="1", font_family="monospace",
                color=rx.color("gray", 11), flex="1"),
        rx.badge(t.module, color_scheme=color, variant="soft", size="1",
                 min_width="140px"),
        rx.text(t.what, size="1", color=rx.color("gray", 9), flex="1"),
        gap=SPACING["md"],
        align="center",
        padding="6px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


def _quality_row(q) -> rx.Component:
    sc = _STATUS_COLOR.get(q.status, "gray")
    pc = _PRIORITY_COLOR.get(q.priority, "gray")
    return rx.flex(
        rx.text(q.id, size="1", font_family="monospace",
                color=rx.color("gray", 8), min_width="60px"),
        rx.badge(q.priority, color_scheme=pc, variant="soft", size="1",
                 min_width="60px"),
        rx.text(q.title, size="2", color=rx.color("gray", 12), flex="1"),
        rx.badge(q.status, color_scheme=sc, variant="soft", size="1",
                 min_width="60px"),
        rx.text(q.detail, size="1", color=rx.color("gray", 9), flex="1"),
        gap=SPACING["md"],
        align="center",
        padding="8px 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


def real_quality_tab() -> rx.Component:
    done_count    = sum(1 for q in QUALITY_ITEMS if q.status == "done")
    open_count    = sum(1 for q in QUALITY_ITEMS if q.status == "open")
    planned_count = sum(1 for q in QUALITY_ITEMS if q.status == "planned")
    enrich_tests  = sum(1 for t in TESTS if "enrich"      in t.module)
    writer_tests  = sum(1 for t in TESTS if "note_writer" in t.module)

    return real_page_wrapper(
        real_page_header("tests/ + RECOMMENDATIONS.md · knowledge-pipeline"),

        # Stats row
        stat_card_row(
            stat_card("Тестов всего",          str(len(TESTS)),                    icon="shield-check"),
            stat_card("test_enrich.py",        str(enrich_tests),                  icon="flask-conical"),
            stat_card("test_note_writer.py",   str(writer_tests),                  icon="file-text"),
            stat_card("Рекомендаций выполнено", f"{done_count}/{len(QUALITY_ITEMS)}", trend_direction="good", icon="circle-check"),
        ),

        rx.box(height=SPACING["xl"]),

        # Test suite
        section_header(f"Test suite · {len(TESTS)} тестов", "flask-conical"),
        rx.box(
            *[_test_row(t) for t in TESTS],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # Quality backlog
        section_header("Quality backlog · RECOMMENDATIONS.md", "list-checks"),
        rx.flex(
            rx.flex(
                rx.text(str(done_count),    size="4", weight="bold", color=rx.color("teal", 9)),
                rx.text("выполнено", size="1", color=rx.color("gray", 9)),
                direction="column", align="center",
                padding=f"10px {SPACING['lg']}",
                border=f"{BORDER} {rx.color('gray', 4)}",
                border_radius="var(--radius-2)",
            ),
            rx.flex(
                rx.text(str(open_count),    size="4", weight="bold", color=rx.color("amber", 9)),
                rx.text("открыто", size="1", color=rx.color("gray", 9)),
                direction="column", align="center",
                padding=f"10px {SPACING['lg']}",
                border=f"{BORDER} {rx.color('gray', 4)}",
                border_radius="var(--radius-2)",
            ),
            rx.flex(
                rx.text(str(planned_count), size="4", weight="bold", color=rx.color("blue", 9)),
                rx.text("запланировано", size="1", color=rx.color("gray", 9)),
                direction="column", align="center",
                padding=f"10px {SPACING['lg']}",
                border=f"{BORDER} {rx.color('gray', 4)}",
                border_radius="var(--radius-2)",
            ),
            gap=SPACING["md"],
            margin_bottom=SPACING["md"],
        ),
        rx.box(
            *[_quality_row(q) for q in QUALITY_ITEMS],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
        ),

    )
