"""
Backlog tab — полный реестр всех задач с интерактивными фильтрами.

Режимы отображения:
- Issues  — строка = одна задача
- Epics   — строка = один эпик с агрегатами

Фильтры (реактивные):
  Squad · Type · Status · Priority · Severity · Sprint · Epic · OKR
"""

import reflex as rx

from ..tokens import SPACING, BORDER, EPIC_TYPE_COLORS
from ..components import section_header
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


def _select_epic() -> rx.Component:
    """Epic filter with 'KEY · Name' labels but stores KEY as value."""
    return rx.box(
        rx.text("Epic", size="1", color=rx.color("gray", 9),
                style={"text_transform": "uppercase", "letter_spacing": "0.04em"},
                margin_bottom="4px"),
        rx.select.root(
            rx.select.trigger(placeholder="Все", size="1"),
            rx.select.content(
                rx.select.item("Все", value=""),
                rx.foreach(
                    BacklogState.epic_filter_options,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=BacklogState.epic,
            on_change=BacklogState.set_epic,
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
            _select_epic(),
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
# Shared helpers
# ---------------------------------------------------------------------------

_TYPE_COLORS = {
    "bug": "tomato", "story": "teal", "design": "violet",
    "experiment": "iris", "research-spike": "cyan",
    "requirement": "amber", "adr": "plum", "support-ticket": "orange",
}

def _type_badge(issue_type: str) -> rx.Component:
    # Единый источник цветов типа — _TYPE_COLORS; rx.match не индексирует dict
    # по реактивному Var, поэтому разворачиваем пары из словаря.
    return rx.badge(
        issue_type,
        color_scheme=rx.match(
            issue_type,
            *[(t, c) for t, c in _TYPE_COLORS.items()],
            "gray",
        ),
        variant="soft", size="1",
    )


def _status_label(status: str):
    return rx.cond(status == "Done", "✓ Готово",
           rx.cond(status == "In Progress", "⟳ В работе",
           rx.cond(status == "In Review", "⊙ На ревью", "○ Не начато")))


def _status_bg(status: str):
    return rx.cond(status == "Done", rx.color("grass", 9),
           rx.cond(status == "In Progress", rx.color("amber", 9),
           rx.cond(status == "In Review", rx.color("teal", 9),
                   rx.color("gray", 9))))


def _status_badge_large(status: str) -> rx.Component:
    """Full-width Jira-style status block at the top of the right panel."""
    return rx.box(
        rx.text(_status_label(status), size="2", weight="bold",
                style={"color": "white", "text_align": "center"}),
        background=_status_bg(status),
        border_radius="var(--radius-3)",
        padding="8px 12px",
        width="100%",
        margin_bottom="12px",
    )


def _status_badge_small(status: str) -> rx.Component:
    label = rx.cond(status == "Done", "Готово",
            rx.cond(status == "In Progress", "В работе",
            rx.cond(status == "In Review", "На ревью", "Не начато")))
    bg = rx.cond(status == "Done", rx.color("grass", 3),
         rx.cond(status == "In Progress", rx.color("amber", 3),
         rx.cond(status == "In Review", rx.color("teal", 3),
                 rx.color("gray", 3))))
    fg = rx.cond(status == "Done", rx.color("grass", 11),
         rx.cond(status == "In Progress", rx.color("amber", 11),
         rx.cond(status == "In Review", rx.color("teal", 11),
                 rx.color("gray", 11))))
    return rx.box(
        rx.text(label, size="1", weight="medium", style={"color": fg}),
        background=bg,
        border_radius="var(--radius-2)",
        padding="2px 8px",
        display="inline-flex",
        align_items="center",
    )


def _jira_field(label: str, value_component) -> rx.Component:
    """One label-value row in Jira right-panel style."""
    return rx.flex(
        rx.text(
            label,
            size="1",
            color=rx.color("gray", 9),
            weight="medium",
            style={
                "min_width": "90px",
                "text_transform": "uppercase",
                "letter_spacing": "0.04em",
            },
        ),
        value_component,
        align="center",
        gap="3",
        padding_y="6px",
        border_bottom=f"1px solid {rx.color('gray', 4)}",
        width="100%",
    )


# ---------------------------------------------------------------------------
# Popup content builders (no dialog root — shared by one dialog below)
# ---------------------------------------------------------------------------

def _issue_content() -> rx.Component:
    issue = BacklogState.selected_issue
    return rx.box(
        # ── Header ─────────────────────────────────────────────────────────
        rx.flex(
            rx.flex(
                _type_badge(issue["issue_type"]),
                rx.text(issue["key"],
                        style={"font_family": "monospace", "font_size": "12px"},
                        color=rx.color("teal", 11)),
                align="center", gap="2",
            ),
            rx.dialog.close(
                rx.icon_button(rx.icon("x", size=14),
                               size="1", variant="ghost", color_scheme="gray"),
            ),
            justify="between", align="center",
            margin_bottom="2",
        ),
        # ── Summary ────────────────────────────────────────────────────────
        rx.heading(issue["summary"], size="4", weight="bold",
                   margin_bottom="4", style={"line_height": "1.4"}),
        # ── Two-column body ────────────────────────────────────────────────
        rx.flex(
            # Left: description + decision note
            rx.flex(
                rx.cond(
                    issue["description"] != "",
                    rx.box(
                        rx.text("Description", size="1", color=rx.color("gray", 9),
                                weight="medium",
                                style={"text_transform": "uppercase",
                                       "letter_spacing": "0.04em"},
                                margin_bottom="2"),
                        rx.text(issue["description"], size="2", color=rx.color("gray", 11),
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
                            rx.text("Decision Note", size="1",
                                    color=rx.color("amber", 9), weight="medium",
                                    style={"text_transform": "uppercase",
                                           "letter_spacing": "0.04em"}),
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
                direction="column", flex="1", min_width="0",
            ),
            # Right: Jira metadata panel
            rx.flex(
                # Status — full-width colored block, Jira-style top
                _status_badge_large(issue["status"]),
                rx.separator(size="4", margin_bottom="12px"),
                _jira_field("Assignee", rx.text(issue["assignee"], size="2")),
                rx.cond(
                    issue["labels"] != "",
                    _jira_field("Labels",
                                rx.text(issue["labels"], size="2",
                                        color=rx.color("gray", 10))),
                    rx.box(),
                ),
                # Priority — editable select
                rx.flex(
                    rx.text("Priority", size="1", color=rx.color("gray", 9), weight="medium",
                            style={"min_width": "90px", "text_transform": "uppercase",
                                   "letter_spacing": "0.04em"}),
                    rx.select.root(
                        rx.select.trigger(size="1"),
                        rx.select.content(
                            *[rx.select.item(p, value=p) for p in PRIORITY_OPTIONS],
                        ),
                        value=issue["priority"],
                        on_change=BacklogState.set_issue_priority,
                    ),
                    align="center", gap="3", padding_y="6px",
                    border_bottom=f"1px solid {rx.color('gray', 4)}",
                    width="100%",
                ),
                # Epic Link — editable select
                rx.flex(
                    rx.text("Epic Link", size="1", color=rx.color("gray", 9), weight="medium",
                            style={"min_width": "90px", "text_transform": "uppercase",
                                   "letter_spacing": "0.04em"}),
                    rx.select.root(
                        rx.select.trigger(size="1"),
                        rx.select.content(
                            rx.foreach(BacklogState.all_epic_names,
                                       lambda n: rx.select.item(n, value=n)),
                        ),
                        value=issue["epic_name"],
                        on_change=BacklogState.set_issue_epic,
                    ),
                    align="center", gap="3", padding_y="6px",
                    border_bottom=f"1px solid {rx.color('gray', 4)}",
                    width="100%",
                ),
                _jira_field("Sprint",
                            rx.text(issue["sprint_name"], size="2",
                                    color=rx.color("gray", 10))),
                _jira_field("Story Points",
                            rx.text(issue["story_points"].to_string(), size="2")),
                _jira_field("Squad", rx.text(issue["squad_key"], size="2")),
                _jira_field("Created",
                            rx.text(issue["created_at"], size="2",
                                    color=rx.color("gray", 10))),
                direction="column",
                width="280px", flex_shrink="0",
                background=rx.color("gray", 2),
                border_radius="var(--radius-3)",
                padding="12px",
                border=f"{BORDER} {rx.color('gray', 4)}",
            ),
            gap="5", align="start",
        ),
    )


def _epic_child_row(child: dict) -> rx.Component:
    return rx.flex(
        _type_badge(child["issue_type"]),
        rx.text(child["key"], size="1",
                style={"font_family": "monospace", "white_space": "nowrap"},
                color=rx.color("gray", 10), min_width="80px"),
        _status_badge_small(child["status"]),
        rx.text(child["summary"], size="2", color=rx.color("gray", 12),
                style={"overflow": "hidden", "text_overflow": "ellipsis",
                       "white_space": "nowrap"}),
        align="center", gap="2",
        padding_y="5px",
        border_bottom=f"1px solid {rx.color('gray', 3)}",
        width="100%",
    )


def _epic_content() -> rx.Component:
    epic = BacklogState.selected_epic
    done_pct = epic["done_pct"].to(int)
    return rx.box(
        # ── Header ─────────────────────────────────────────────────────────
        rx.flex(
            rx.flex(
                rx.badge("epic", color_scheme="purple", variant="soft", size="1"),
                rx.text(epic["epic_key"],
                        style={"font_family": "monospace", "font_size": "12px"},
                        color=rx.color("purple", 11)),
                _epic_type_chip(epic["epic_type"], epic["unlocks"]),
                align="center", gap="2",
            ),
            rx.dialog.close(
                rx.icon_button(rx.icon("x", size=14),
                               size="1", variant="ghost", color_scheme="gray"),
            ),
            justify="between", align="center",
            margin_bottom="2",
        ),
        # ── Epic name ──────────────────────────────────────────────────────
        rx.heading(epic["epic_name"], size="4", weight="bold",
                   margin_bottom="4", style={"line_height": "1.4"}),
        # ── Two-column body ────────────────────────────────────────────────
        rx.flex(
            # Left: child issues
            rx.flex(
                rx.text("Child Issues (", done_pct.to_string(), " % done)",
                        size="1", color=rx.color("gray", 9), weight="medium",
                        style={"text_transform": "uppercase", "letter_spacing": "0.04em"},
                        margin_bottom="2"),
                rx.flex(
                    rx.foreach(BacklogState.selected_epic_children, _epic_child_row),
                    direction="column", width="100%",
                ),
                direction="column", flex="1", min_width="0",
            ),
            # Right: stats panel
            rx.flex(
                rx.text("Progress", size="1", color=rx.color("gray", 9), weight="medium",
                        style={"text_transform": "uppercase", "letter_spacing": "0.04em"},
                        margin_bottom="2"),
                rx.flex(
                    rx.box(
                        rx.box(
                            height="8px",
                            background=rx.cond(
                                done_pct >= 90, rx.color("grass", 7),
                                rx.cond(done_pct >= 50, rx.color("teal", 7),
                                        rx.color("amber", 7))),
                            border_radius="var(--radius-full)",
                            width=done_pct.to_string() + "%",
                        ),
                        width="100%", height="8px",
                        background=rx.color("gray", 4),
                        border_radius="var(--radius-full)",
                        overflow="hidden",
                    ),
                    rx.text(done_pct.to_string() + "%", size="1",
                            color=rx.color("gray", 11), weight="bold"),
                    align="center", gap="6px", width="100%", margin_bottom="3",
                ),
                rx.separator(size="4", margin_bottom="3"),
                _jira_field("Total",
                            rx.text(epic["total"].to(int).to_string(), size="2")),
                _jira_field("Done",
                            rx.text(epic["done"].to(int).to_string(), size="2",
                                    color=rx.color("grass", 11))),
                _jira_field("In Progress",
                            rx.text(epic["in_progress"].to(int).to_string(), size="2",
                                    color=rx.color("amber", 11))),
                _jira_field("To Do",
                            rx.text(epic["to_do"].to(int).to_string(), size="2",
                                    color=rx.color("gray", 10))),
                rx.separator(size="4", margin_y="3"),
                _jira_field("SP Total",
                            rx.text(epic["sp_total"].to(int).to_string(), size="2")),
                _jira_field("SP Done",
                            rx.text(epic["sp_done"].to(int).to_string(), size="2",
                                    color=rx.color("grass", 11))),
                rx.separator(size="4", margin_y="3"),
                _jira_field("Squads", rx.text(epic["squads"], size="2")),
                rx.cond(
                    epic["unlocks"] != "",
                    rx.fragment(
                        rx.separator(size="4", margin_y="3"),
                        _jira_field("Unlocks",
                                    rx.text(epic["unlocks"], " · ", epic["unlocks_name"],
                                            size="2", color=rx.color("amber", 11))),
                    ),
                    rx.fragment(),
                ),
                direction="column",
                width="240px", flex_shrink="0",
                background=rx.color("gray", 2),
                border_radius="var(--radius-3)",
                padding="12px",
                border=f"{BORDER} {rx.color('gray', 4)}",
            ),
            gap="5", align="start",
        ),
    )


# ---------------------------------------------------------------------------
# Single combined popup (one rx.dialog.root for both issue and epic)
# ---------------------------------------------------------------------------

def _popup() -> rx.Component:
    """One dialog that shows issue or epic content based on which key is set."""
    is_open = (BacklogState.selected_key != "") | (BacklogState.selected_epic_key != "")
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                BacklogState.selected_epic_key != "",
                _epic_content(),
                _issue_content(),
            ),
            max_width="900px",
            width="90vw",
            max_height="85vh",
            overflow_y="auto",
        ),
        open=is_open,
        on_open_change=lambda v: rx.cond(v, rx.noop(), BacklogState.close_popup()),
    )


# ---------------------------------------------------------------------------
# Issues table
# ---------------------------------------------------------------------------

def _issue_row(row: dict) -> rx.Component:
    return rx.table.row(
        # Epic Key (first column) — clickable → epic popup
        rx.table.cell(
            rx.text(row["epic"], size="1",
                    style={"font_family": "monospace", "white_space": "nowrap",
                           "cursor": "pointer",
                           "_hover": {"text_decoration": "underline"}},
                    color=rx.color("purple", 11),
                    on_click=BacklogState.open_epic(row["epic"])),
        ),
        # Epic Name (second column) — clickable → epic popup
        rx.table.cell(
            rx.text(row["epic_name"], size="1", color=rx.color("teal", 11),
                    style={"white_space": "nowrap", "max_width": "140px",
                           "overflow": "hidden", "text_overflow": "ellipsis",
                           "cursor": "pointer",
                           "_hover": {"color": rx.color("purple", 11),
                                      "text_decoration": "underline"}},
                    on_click=BacklogState.open_epic(row["epic"])),
        ),
        # Squad
        rx.table.cell(rx.text(row["squad_key"], size="1", color=rx.color("gray", 11))),
        # Key (clickable → issue popup)
        rx.table.cell(
            rx.text(row["key"],
                    style={"font_family": "monospace", "font_size": "12px",
                           "white_space": "nowrap", "cursor": "pointer",
                           "_hover": {"text_decoration": "underline"}},
                    color=rx.color("gray", 10),
                    on_click=BacklogState.open_issue(row["key"])),
        ),
        # Type
        rx.table.cell(_type_badge(row["issue_type"])),
        # Summary (clickable → issue popup)
        rx.table.cell(
            rx.text(
                row["summary"],
                size="2",
                color=rx.color("gray", 12),
                style={"cursor": "pointer", "max_width": "340px",
                       "overflow": "hidden", "text_overflow": "ellipsis",
                       "white_space": "nowrap",
                       "_hover": {"color": rx.color("teal", 11),
                                  "text_decoration": "underline"}},
                on_click=BacklogState.open_issue(row["key"]),
            ),
        ),
        # Status
        rx.table.cell(_status_badge_small(row["status"])),
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
                      for col in ["Epic Key", "Epic", "Squad", "Key", "Type", "Summary",
                                  "Status", "Priority", "Severity", "SP", "Sprint", "OKR",
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

def _epic_type_chip(epic_type, unlocks) -> rx.Component:
    """Тип эпика (DASH-93). epic_type — реактивный Var, поэтому цвет берём
    через rx.match, развёрнутый из EPIC_TYPE_COLORS (единый источник цвета)."""
    epic_type = epic_type.to(str)
    unlocks = unlocks.to(str)
    label = rx.cond(unlocks != "", epic_type + " → " + unlocks, epic_type)
    fg = rx.match(epic_type, *[(t, rx.color(c, 11)) for t, c in EPIC_TYPE_COLORS.items()],
                  rx.color("gray", 11))
    bg = rx.match(epic_type, *[(t, rx.color(c, 3)) for t, c in EPIC_TYPE_COLORS.items()],
                  rx.color("gray", 3))
    return rx.cond(
        epic_type != "",
        rx.box(
            rx.text(label, size="1", weight="medium", color=fg),
            background=bg,
            padding="1px 8px",
            border_radius="var(--radius-full)",
            display="inline-block",
            white_space="nowrap",
        ),
        rx.fragment(),
    )


def _epic_row(row: dict) -> rx.Component:
    done_pct = row["done_pct"].to(int)
    color = rx.cond(done_pct >= 90, "grass", rx.cond(done_pct >= 50, "teal", "amber"))
    return rx.table.row(
        # Key (monospace, clickable)
        rx.table.cell(
            rx.text(
                row["epic"],
                style={"font_family": "monospace", "font_size": "12px",
                       "cursor": "pointer", "white_space": "nowrap",
                       "_hover": {"text_decoration": "underline"}},
                color=rx.color("purple", 11),
                on_click=BacklogState.open_epic(row["epic"]),
            ),
        ),
        # Name (human-readable, clickable)
        rx.table.cell(
            rx.text(
                row["epic_name"],
                size="2",
                color=rx.color("gray", 12),
                style={"cursor": "pointer", "max_width": "220px",
                       "overflow": "hidden", "text_overflow": "ellipsis",
                       "white_space": "nowrap",
                       "_hover": {"color": rx.color("purple", 11),
                                  "text_decoration": "underline"}},
                on_click=BacklogState.open_epic(row["epic"]),
            ),
        ),
        # Type (business/enabler/component; enabler показывает «→ Ex»)
        rx.table.cell(_epic_type_chip(row["epic_type"], row["unlocks"])),
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
                                                              "text_transform": "uppercase",
                                                              "white_space": "nowrap"})
                      for col in ["Key", "Name", "Type", "OKR", "Squads", "Total", "Done",
                                  "Done %", "SP Total", "SP Done", "In Progress", "Bugs"]]
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
        _popup(),

        section_header(
            "Backlog",
            subtitle="Все задачи Jira · интерактивные фильтры · режимы Issues / Epics",
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
