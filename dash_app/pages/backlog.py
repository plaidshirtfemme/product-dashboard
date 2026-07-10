"""
Backlog tab — полный реестр всех 103 Jira-задач с интерактивными фильтрами.

Режимы отображения:
- Issues  — строка = одна задача (12 колонок, как в Jira Board/List)
- Epics   — строка = один эпик с агрегатами

Фильтры (реактивные, без перезагрузки):
  Squad · Type · Status · Priority · Severity · Sprint · Epic · OKR
"""

import reflex as rx

from ..tokens import SPACING, BORDER
from ..components import data_source_badge, section_header
from ..states.backlog_state import (
    BacklogState,
    STATUS_OPTIONS, PRIORITY_OPTIONS, SEVERITY_OPTIONS,
)

# ---------------------------------------------------------------------------
# Color maps
# ---------------------------------------------------------------------------

_STATUS_COLORS = {
    "Done":        ("grass",  "Готово"),
    "In Progress": ("amber",  "В работе"),
    "In Review":   ("teal",   "На ревью"),
    "To Do":       ("gray",   "Не начато"),
}
_SEV_COLORS = {
    "Blocker":  "tomato", "Critical": "tomato",
    "Major":    "amber",  "Minor":    "amber",  "Trivial": "gray",
}
_PRI_COLORS = {
    "Highest": "tomato", "High": "amber",
    "Medium":  "gray",   "Low":  "gray",  "Lowest": "gray",
}
_TYPE_COLORS = {
    "bug":            "tomato", "story":          "teal",
    "task":           "gray",   "design":         "violet",
    "experiment":     "iris",   "research-spike": "cyan",
    "requirement":    "amber",  "adr":            "plum",
    "support-ticket": "orange",
}


# ---------------------------------------------------------------------------
# Filter bar
# ---------------------------------------------------------------------------

def _select(label: str, options: list[str], value_var, on_change) -> rx.Component:
    """Static select — for options that don't change between project modes."""
    items = [rx.select.item("Все", value="")] + [rx.select.item(o, value=o) for o in options]
    return rx.box(
        rx.text(label, size="1", color=rx.color("gray", 9),
                style={"text_transform": "uppercase", "letter_spacing": "0.04em"},
                margin_bottom="4px"),
        rx.select.root(
            rx.select.trigger(placeholder="Все", size="1"),
            rx.select.content(*items),
            value=value_var,
            on_change=on_change,
        ),
        flex_shrink="0",
    )


def _select_dyn(label: str, options_var, value_var, on_change) -> rx.Component:
    """Dynamic select — options_var is a BacklogState computed var (list[str])."""
    return rx.box(
        rx.text(label, size="1", color=rx.color("gray", 9),
                style={"text_transform": "uppercase", "letter_spacing": "0.04em"},
                margin_bottom="4px"),
        rx.select.root(
            rx.select.trigger(placeholder="Все", size="1"),
            rx.select.content(
                rx.select.item("Все", value=""),
                rx.foreach(options_var, lambda o: rx.select.item(o, value=o)),
            ),
            value=value_var,
            on_change=on_change,
        ),
        flex_shrink="0",
    )


def _filter_bar() -> rx.Component:
    return rx.box(
        rx.flex(
            # Mode toggle
            rx.flex(
                rx.button(
                    rx.icon("list", size=13), "Issues",
                    size="1",
                    variant=rx.cond(BacklogState.mode == "issues", "solid", "soft"),
                    color_scheme="teal",
                    on_click=BacklogState.set_mode("issues"),
                ),
                rx.button(
                    rx.icon("layers", size=13), "Epics",
                    size="1",
                    variant=rx.cond(BacklogState.mode == "epics", "solid", "soft"),
                    color_scheme="teal",
                    on_click=BacklogState.set_mode("epics"),
                ),
                gap="4px",
            ),

            rx.separator(orientation="vertical", size="2"),

            # Filters (squad/type/sprint/epic/okr are reactive — change with project mode)
            _select_dyn("Squad",  BacklogState.squad_options,  BacklogState.squad,    BacklogState.set_squad),
            _select_dyn("Type",   BacklogState.type_options,   BacklogState.type_,    BacklogState.set_type),
            _select("Status",   STATUS_OPTIONS,   BacklogState.status,   BacklogState.set_status),
            _select("Priority", PRIORITY_OPTIONS, BacklogState.priority, BacklogState.set_priority),
            _select("Severity", SEVERITY_OPTIONS, BacklogState.severity, BacklogState.set_severity),
            _select_dyn("Sprint", BacklogState.sprint_options, BacklogState.sprint,   BacklogState.set_sprint),
            _select_dyn("Epic",   BacklogState.epic_options,   BacklogState.epic,     BacklogState.set_epic),
            _select_dyn("OKR",    BacklogState.okr_options,    BacklogState.okr,      BacklogState.set_okr),

            rx.separator(orientation="vertical", size="2"),

            # Reset + count
            rx.flex(
                rx.button(
                    rx.icon("x", size=13), "Сбросить",
                    size="1", variant="ghost", color_scheme="gray",
                    on_click=BacklogState.reset_filters,
                    display=rx.cond(BacklogState.has_active_filters, "flex", "none"),
                ),
                rx.text(
                    BacklogState.filtered_count.to_string(), " задач",
                    size="1", color=rx.color("gray", 9),
                ),
                align="center",
                gap=SPACING["sm"],
            ),

            align="end",
            gap=SPACING["md"],
            wrap="wrap",
        ),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        width="100%",
        margin_bottom=SPACING["md"],
    )


# ---------------------------------------------------------------------------
# Issues table (rx.foreach — reactive)
# ---------------------------------------------------------------------------

def _status_chip(status: str) -> rx.Component:
    color, label = _STATUS_COLORS.get(status, ("gray", status))
    return rx.badge(label, color_scheme=color, variant="soft", size="1")


def _issue_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.text(row["key"],
                    style={"font_family": "monospace", "font_size": "12px",
                           "white_space": "nowrap"},
                    color=rx.color("teal", 11)),
        ),
        rx.table.cell(
            rx.badge(row["issue_type"],
                     color_scheme=rx.match(
                         row["issue_type"],
                         ("bug",            "tomato"),
                         ("story",          "teal"),
                         ("design",         "violet"),
                         ("experiment",     "iris"),
                         ("research-spike", "cyan"),
                         ("requirement",    "amber"),
                         ("adr",            "plum"),
                         ("support-ticket", "orange"),
                         "gray",
                     ),
                     variant="soft", size="1"),
        ),
        rx.table.cell(
            rx.badge(
                rx.match(row["status"],
                    ("Done",        "Готово"),
                    ("In Progress", "В работе"),
                    ("In Review",   "На ревью"),
                    ("To Do",       "Не начато"),
                    row["status"]),
                color_scheme=rx.match(
                    row["status"],
                    ("Done",        "grass"),
                    ("In Progress", "amber"),
                    ("In Review",   "teal"),
                    "gray",
                ),
                variant="soft", size="1",
            ),
        ),
        rx.table.cell(rx.text(row["squad_key"], size="1", color=rx.color("gray", 11))),
        rx.table.cell(rx.text(row["epic"], size="1",
                              style={"font_family": "monospace"},
                              color=rx.color("gray", 10))),
        rx.table.cell(
            rx.cond(
                row["priority"] != "",
                rx.badge(row["priority"],
                         color_scheme=rx.match(
                             row["priority"],
                             ("Highest", "tomato"), ("High", "amber"),
                             "gray"),
                         variant="outline", size="1"),
                rx.text("—", size="1", color=rx.color("gray", 7)),
            )
        ),
        rx.table.cell(
            rx.cond(
                row["severity"] != "",
                rx.badge(row["severity"],
                         color_scheme=rx.match(
                             row["severity"],
                             ("Blocker", "tomato"), ("Critical", "tomato"),
                             ("Major", "amber"), ("Minor", "amber"),
                             "gray"),
                         variant="soft", size="1"),
                rx.text("—", size="1", color=rx.color("gray", 7)),
            )
        ),
        rx.table.cell(rx.text(row["story_points"].to(int).to_string(), size="1")),
        rx.table.cell(rx.text(row["sprint_name"], size="1", color=rx.color("gray", 10))),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["okr_tag"], size="1", color=rx.color("violet", 11),
                        style={"cursor": "default", "text_decoration": "underline dotted"}),
                content=row["okr_title"],
            )
        ),
        rx.table.cell(rx.text(row["cycle_time"], size="1", color=rx.color("gray", 10))),
        rx.table.cell(
            rx.cond(
                row["rework_count"].to(int) > 0,
                rx.badge(row["rework_count"].to(int).to_string(),
                         color_scheme="tomato", variant="soft", size="1"),
                rx.text("0", size="1", color=rx.color("gray", 7)),
            )
        ),
        rx.table.cell(
            rx.cond(
                row["blocked"] != "",
                rx.icon("circle_x", size=13, color=rx.color("tomato", 9)),
                rx.box(),
            )
        ),
        rx.table.cell(
            rx.tooltip(
                rx.cond(
                    row["tracking_added"] == "yes",
                    rx.icon("chart-line", size=13, color=rx.color("grass", 9)),
                    rx.cond(
                        row["tracking_added"] == "no",
                        rx.icon("chart-line", size=13, color=rx.color("tomato", 9)),
                        rx.text("—", size="1", color=rx.color("gray", 6)),
                    ),
                ),
                content=rx.cond(
                    row["tracking_added"] == "yes",
                    "DoD: инструментация добавлена",
                    rx.cond(
                        row["tracking_added"] == "no",
                        "DoD: инструментация НЕ добавлена (rework)",
                        "DoD: не применимо",
                    ),
                ),
            )
        ),
        style={"_hover": {"background": rx.color("gray", 2)}},
    )


def _issues_table() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[rx.table.column_header_cell(col, style={"font_size": "11px", "color": rx.color("gray", 10),
                                                              "text_transform": "uppercase", "white_space": "nowrap"})
                      for col in ["Key", "Type", "Status", "Squad", "Epic", "Priority",
                                  "Severity", "SP", "Sprint", "OKR", "Cycle time", "Rework", "🔒", "📊"]]
                )
            ),
            rx.table.body(
                rx.foreach(BacklogState.filtered, _issue_row)
            ),
            variant="surface",
            width="100%",
            size="1",
        ),
        width="100%",
        overflow_x="auto",
    )


# ---------------------------------------------------------------------------
# Epics table (rx.foreach — reactive)
# ---------------------------------------------------------------------------

def _epic_row(row: dict) -> rx.Component:
    done_pct = row["done_pct"].to(int)
    color = rx.cond(done_pct >= 90, "grass", rx.cond(done_pct >= 50, "teal", "amber"))
    return rx.table.row(
        rx.table.cell(
            rx.text(row["epic"], style={"font_family": "monospace", "font_size": "12px"},
                    color=rx.color("teal", 11)),
        ),
        rx.table.cell(
            rx.tooltip(
                rx.text(row["okr_tag"], size="1", color=rx.color("violet", 11),
                        style={"cursor": "default", "text_decoration": "underline dotted"}),
                content=row["okr_title"],
            )
        ),
        rx.table.cell(rx.text(row["squads"], size="1", color=rx.color("gray", 10))),
        rx.table.cell(rx.text(row["total"].to(int).to_string(), size="1")),
        rx.table.cell(rx.text(row["done"].to(int).to_string(), size="1")),
        rx.table.cell(
            rx.flex(
                rx.box(
                    rx.box(height="6px", background=rx.color(color, 7),
                           border_radius="var(--radius-full)",
                           width=done_pct.to_string() + "%"),
                    width="60px", height="6px",
                    background=rx.color("gray", 4), border_radius="var(--radius-full)",
                    overflow="hidden",
                ),
                rx.text(done_pct.to_string() + "%", size="1",
                        color=rx.color(color, 11)),
                align="center", gap="6px",
            )
        ),
        rx.table.cell(rx.text(row["sp_total"].to(int).to_string(), size="1")),
        rx.table.cell(rx.text(row["sp_done"].to(int).to_string(), size="1")),
        rx.table.cell(rx.text(row["in_progress"].to(int).to_string(), size="1")),
        rx.table.cell(
            rx.cond(
                row["bugs"].to(int) > 0,
                rx.badge(row["bugs"].to(int).to_string(), color_scheme="tomato", variant="soft", size="1"),
                rx.text("0", size="1", color=rx.color("gray", 7)),
            )
        ),
        style={"_hover": {"background": rx.color("gray", 2)}},
    )


def _epics_table() -> rx.Component:
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[rx.table.column_header_cell(col, style={"font_size": "11px", "color": rx.color("gray", 10),
                                                              "text_transform": "uppercase"})
                      for col in ["Epic", "OKR", "Squads", "Total", "Done", "Done %",
                                  "SP Total", "SP Done", "In Progress", "Bugs"]]
                )
            ),
            rx.table.body(
                rx.foreach(BacklogState.epic_rows, _epic_row)
            ),
            variant="surface",
            width="100%",
            size="1",
        ),
        width="100%",
        overflow_x="auto",
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def backlog_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Backlog",
            subtitle="Все задачи Jira · интерактивные фильтры · режимы Issues / Epics",
            action=data_source_badge("mock"),
        ),

        _filter_bar(),

        rx.cond(
            BacklogState.mode == "issues",
            _issues_table(),
            _epics_table(),
        ),

        padding=SPACING["xl"],
        max_width="1400px",   # шире чем остальные вкладки — много колонок
        margin="0 auto",
    )
