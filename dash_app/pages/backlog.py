"""
Backlog tab — полный реестр всех задач с интерактивными фильтрами.

Режимы отображения:
- Issues  — строка = одна задача
- Epics   — строка = один эпик с агрегатами

Фильтры (реактивные):
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
# Filter bar
# ---------------------------------------------------------------------------

def _select(label: str, options: list[str], value_var, on_change) -> rx.Component:
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
            _select_dyn("Squad",  BacklogState.squad_options,  BacklogState.squad,    BacklogState.set_squad),
            _select_dyn("Type",   BacklogState.type_options,   BacklogState.type_,    BacklogState.set_type),
            _select("Status",   STATUS_OPTIONS,   BacklogState.status,   BacklogState.set_status),
            _select("Priority", PRIORITY_OPTIONS, BacklogState.priority, BacklogState.set_priority),
            _select("Severity", SEVERITY_OPTIONS, BacklogState.severity, BacklogState.set_severity),
            _select_dyn("Sprint", BacklogState.sprint_options, BacklogState.sprint,   BacklogState.set_sprint),
            _select_dyn("Epic",   BacklogState.epic_options,   BacklogState.epic,     BacklogState.set_epic),
            _select_dyn("OKR",    BacklogState.okr_options,    BacklogState.okr,      BacklogState.set_okr),
            rx.separator(orientation="vertical", size="2"),
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
# Issue detail popup (Jira-style dialog)
# ---------------------------------------------------------------------------

def _priority_badge(priority: str) -> rx.Component:
    return rx.badge(
        priority,
        color_scheme=rx.match(
            priority,
            ("Highest", "tomato"), ("High", "amber"),
            ("Medium", "blue"), ("Low", "gray"), ("Lowest", "gray"),
            "gray",
        ),
        variant="outline", size="1",
    )


def _status_badge(status: str) -> rx.Component:
    return rx.badge(
        rx.match(status,
            ("Done", "Готово"), ("In Progress", "В работе"),
            ("In Review", "На ревью"), ("To Do", "Не начато"),
            status),
        color_scheme=rx.match(
            status,
            ("Done", "grass"), ("In Progress", "amber"), ("In Review", "teal"),
            "gray",
        ),
        variant="soft", size="1",
    )


def _detail_field(label: str, value) -> rx.Component:
    return rx.flex(
        rx.text(label, size="1", color=rx.color("gray", 9), weight="medium",
                style={"min_width": "120px", "text_transform": "uppercase",
                       "letter_spacing": "0.04em"}),
        value,
        align="start",
        gap="3",
        padding_y="6px",
        border_bottom=f"1px solid {rx.color('gray', 4)}",
        width="100%",
    )


def _issue_popup() -> rx.Component:
    issue = BacklogState.selected_issue
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.flex(
                rx.flex(
                    rx.badge(
                        issue["issue_type"],
                        color_scheme=rx.match(
                            issue["issue_type"],
                            ("bug", "tomato"), ("story", "teal"),
                            ("design", "violet"), ("experiment", "iris"),
                            ("research-spike", "cyan"), ("requirement", "amber"),
                            ("adr", "plum"), ("support-ticket", "orange"),
                            "gray",
                        ),
                        variant="soft", size="1",
                    ),
                    rx.text(issue["key"],
                            style={"font_family": "monospace", "font_size": "12px"},
                            color=rx.color("teal", 11)),
                    align="center",
                    gap="2",
                ),
                rx.dialog.close(
                    rx.icon_button(
                        rx.icon("x", size=14),
                        size="1", variant="ghost", color_scheme="gray",
                    ),
                ),
                justify="between",
                align="center",
                margin_bottom="3",
            ),
            # Title
            rx.heading(issue["summary"], size="4", weight="bold",
                       margin_bottom="4",
                       style={"line_height": "1.4"}),
            # Two-column layout like Jira
            rx.flex(
                # Left: description + decision note
                rx.flex(
                    rx.cond(
                        issue["description"] != "",
                        rx.box(
                            rx.text("Description", size="1", color=rx.color("gray", 9),
                                    weight="medium",
                                    style={"text_transform": "uppercase", "letter_spacing": "0.04em"},
                                    margin_bottom="2"),
                            rx.text(issue["description"], size="2",
                                    color=rx.color("gray", 11),
                                    style={"white_space": "pre-wrap", "line_height": "1.6"}),
                            margin_bottom="4",
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        issue["decision_note"] != "",
                        rx.box(
                            rx.flex(
                                rx.icon("lightbulb", size=13, color=rx.color("amber", 9)),
                                rx.text("Decision Note", size="1", color=rx.color("amber", 9),
                                        weight="medium",
                                        style={"text_transform": "uppercase", "letter_spacing": "0.04em"}),
                                align="center", gap="1", margin_bottom="2",
                            ),
                            rx.box(
                                rx.text(issue["decision_note"], size="2",
                                        color=rx.color("gray", 11),
                                        style={"white_space": "pre-wrap", "line_height": "1.6"}),
                                background=rx.color("amber", 2),
                                border_left=f"3px solid {rx.color('amber', 6)}",
                                border_radius="0 var(--radius-2) var(--radius-2) 0",
                                padding="10px 12px",
                            ),
                        ),
                        rx.box(),
                    ),
                    direction="column",
                    flex="1",
                    min_width="0",
                ),
                # Right: metadata fields
                rx.flex(
                    # Editable priority
                    rx.flex(
                        rx.text("Priority", size="1", color=rx.color("gray", 9), weight="medium",
                                style={"min_width": "120px", "text_transform": "uppercase",
                                       "letter_spacing": "0.04em"}),
                        rx.select.root(
                            rx.select.trigger(size="1"),
                            rx.select.content(
                                *[rx.select.item(p, value=p) for p in PRIORITY_OPTIONS],
                            ),
                            value=issue["priority"],
                            on_change=BacklogState.set_issue_priority,
                        ),
                        align="center",
                        gap="3",
                        padding_y="6px",
                        border_bottom=f"1px solid {rx.color('gray', 4)}",
                        width="100%",
                    ),
                    _detail_field("Status",   _status_badge(issue["status"])),
                    _detail_field("Assignee", rx.text(issue["assignee"], size="2")),
                    _detail_field("Epic",     rx.text(issue["epic_name"], size="2",
                                                      color=rx.color("teal", 11))),
                    _detail_field("Squad",    rx.text(issue["squad_key"], size="2")),
                    _detail_field("Sprint",   rx.text(issue["sprint_name"], size="2",
                                                      color=rx.color("gray", 10))),
                    _detail_field("Story Pts", rx.text(issue["story_points"].to_string(), size="2")),
                    _detail_field("Created",  rx.text(issue["created_at"], size="2",
                                                      color=rx.color("gray", 10))),
                    rx.cond(
                        issue["labels"] != "",
                        _detail_field("Labels", rx.text(issue["labels"], size="2",
                                                        color=rx.color("gray", 10))),
                        rx.box(),
                    ),
                    direction="column",
                    width="260px",
                    flex_shrink="0",
                    background=rx.color("gray", 2),
                    border_radius="var(--radius-3)",
                    padding="12px",
                    border=f"{BORDER} {rx.color('gray', 4)}",
                ),
                gap="5",
                align="start",
            ),
            max_width="860px",
            width="90vw",
            max_height="85vh",
            overflow_y="auto",
        ),
        open=BacklogState.selected_key != "",
        on_open_change=lambda open: rx.cond(open, rx.noop(), BacklogState.close_issue()),
    )


# ---------------------------------------------------------------------------
# Issues table
# ---------------------------------------------------------------------------

def _issue_row(row: dict) -> rx.Component:
    return rx.table.row(
        # Epic (first)
        rx.table.cell(
            rx.text(row["epic_name"], size="1", color=rx.color("teal", 11),
                    style={"white_space": "nowrap", "max_width": "160px",
                           "overflow": "hidden", "text_overflow": "ellipsis"}),
        ),
        # Squad (second)
        rx.table.cell(rx.text(row["squad_key"], size="1", color=rx.color("gray", 11))),
        # Key
        rx.table.cell(
            rx.text(row["key"],
                    style={"font_family": "monospace", "font_size": "12px",
                           "white_space": "nowrap"},
                    color=rx.color("gray", 10)),
        ),
        # Type
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
        # Summary (clickable)
        rx.table.cell(
            rx.text(
                row["summary"],
                size="2",
                color=rx.color("gray", 12),
                style={"cursor": "pointer", "max_width": "340px",
                       "overflow": "hidden", "text_overflow": "ellipsis",
                       "white_space": "nowrap",
                       "_hover": {"color": rx.color("teal", 11), "text_decoration": "underline"}},
                on_click=BacklogState.open_issue(row["key"]),
            ),
        ),
        # Status
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
        # Priority
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
        # Severity
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
                    *[rx.table.column_header_cell(col, style={"font_size": "11px",
                                                              "color": rx.color("gray", 10),
                                                              "text_transform": "uppercase",
                                                              "white_space": "nowrap"})
                      for col in ["Epic", "Squad", "Key", "Type", "Summary", "Status",
                                  "Priority", "Severity", "SP", "Sprint", "OKR",
                                  "Cycle time", "Rework", "🔒", "📊"]]
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
# Epics table
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
                rx.text(done_pct.to_string() + "%", size="1", color=rx.color(color, 11)),
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
                    *[rx.table.column_header_cell(col, style={"font_size": "11px",
                                                              "color": rx.color("gray", 10),
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
        _issue_popup(),

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
        max_width="1400px",
        margin="0 auto",
    )
