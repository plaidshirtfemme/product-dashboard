"""Kanban board — read-only. Swimlanes by squad, 6 columns, WIP limits."""

import reflex as rx
from ..tokens import SPACING, BORDER
from ..components import data_source_badge, section_header, color_legend
from ..data.adapter import load_issues, Issue
from ..data.jira_mock_raw import DASH_CONFIG

# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

COLUMNS = [
    ("backlog",            "Backlog",             "gray",   None),
    ("ready_for_dev",      "Ready for Dev",        "blue",   15),
    ("in_progress",        "In Progress",          "amber",  10),
    ("in_review",          "In Review",            "violet", 8),
    ("ready_for_release",  "Ready for Release",    "grass",  5),
    ("done",               "Done",                 "teal",   None),
]

SQUAD_LABELS = {
    # Motif Demo squads
    "RESEARCH":     "Research",
    "ARCHITECTURE": "Architecture",
    "ANALYSIS":     "Analysis BA+SA",
    "DESIGN":       "Design",
    "DEV":          "Dev & Pipeline",
    "QUALITY":      "Quality",
    "RELEASE":      "Instructions & Release",
    "MONITORING":   "Monitoring & Support",
    "GROWTH":       "Growth",
    # DASH project squads
    "DISCOVERY":    "Discovery",
    "ARCH":         "Architecture",
    "PM":           "Product Management",
}

_TYPE_COLORS = {
    "story":          "blue",
    "bug":            "tomato",
    "task":           "gray",
    "research-spike": "violet",
    "design":         "iris",
    "experiment":     "amber",
    "requirement":    "cyan",
    "adr":            "plum",
    "tech-debt":      "orange",
}

_PRI_COLORS = {
    "Highest": "tomato",
    "High":    "amber",
    "Medium":  "gray",
    "Low":     "gray",
    "Lowest":  "gray",
}

_PRI_DOT = {
    "Highest": "●",
    "High":    "●",
    "Medium":  "●",
    "Low":     "○",
    "Lowest":  "○",
}


# ---------------------------------------------------------------------------
# Column assignment
# ---------------------------------------------------------------------------

def _issue_column(issue: Issue) -> str:
    if not issue.sprint_name:
        return "backlog"
    if issue.status == "To Do":
        return "ready_for_dev"
    if issue.status == "In Progress":
        return "in_progress"
    if issue.status == "In Review":
        # RELEASE squad "In Review" = waiting for deploy approval
        if issue.squad_key == "RELEASE":
            return "ready_for_release"
        return "in_review"
    if issue.status == "Done":
        return "done"
    return "backlog"


# ---------------------------------------------------------------------------
# Card component
# ---------------------------------------------------------------------------

def _card(issue: Issue) -> rx.Component:
    type_color = _TYPE_COLORS.get(issue.issue_type, "gray")
    pri_color = _PRI_COLORS.get(issue.priority or "", "gray")
    pri_dot = _PRI_DOT.get(issue.priority or "", "○")
    is_blocked = bool(issue.blocked_by)
    border_left = f"3px solid {rx.color('tomato', 7)}" if is_blocked else f"3px solid {rx.color(type_color, 6)}"

    return rx.box(
        rx.flex(
            rx.text(
                issue.key,
                size="1",
                weight="medium",
                color=rx.color("gray", 11),
                style={"font_family": "monospace"},
            ),
            rx.flex(
                rx.text(pri_dot, size="1", color=rx.color(pri_color, 9)),
                rx.icon("circle-x", size=11, color=rx.color("tomato", 9)) if is_blocked else rx.box(),
                align="center",
                gap="4px",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.text(
            issue.epic,
            size="1",
            color=rx.color("gray", 10),
            margin_top="3px",
            style={"overflow": "hidden", "text_overflow": "ellipsis", "white_space": "nowrap"},
        ),
        rx.flex(
            rx.badge(issue.issue_type, color_scheme=type_color, variant="soft", size="1"),
            rx.badge(str(issue.story_points), color_scheme="gray", variant="outline", size="1") if issue.story_points > 0 else rx.box(),
            gap="4px",
            margin_top="6px",
            wrap="wrap",
        ),
        padding="8px",
        background="white",
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_left=border_left,
        border_radius="var(--radius-2)",
        width="100%",
        _hover={"background": rx.color("gray", 1)},
    )


# ---------------------------------------------------------------------------
# Column header
# ---------------------------------------------------------------------------

def _col_header(col_key: str, col_label: str, color: str, wip_limit, wip_current: int) -> rx.Component:
    over_limit = wip_limit is not None and wip_current > wip_limit
    return rx.box(
        rx.flex(
            rx.text(
                col_label,
                size="1",
                weight="bold",
                color=rx.color(color, 11),
                style={"text_transform": "uppercase", "letter_spacing": "0.05em"},
            ),
            rx.flex(
                rx.text(
                    str(wip_current),
                    size="1",
                    weight="bold",
                    color=rx.color("tomato", 11) if over_limit else rx.color(color, 11),
                ),
                rx.cond(
                    wip_limit is not None,
                    rx.text(
                        f"/ {wip_limit}",
                        size="1",
                        color=rx.color("gray", 9),
                    ),
                    rx.box(),
                ),
                align="center",
                gap="2px",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.box(
            height="3px",
            background=rx.color("tomato", 7) if over_limit else rx.color(color, 6),
            border_radius="var(--radius-full)",
            width="100%",
            margin_top="6px",
        ),
        padding=f"10px {SPACING['sm']}",
        background=rx.color(color, 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
        border_bottom=f"{BORDER} {rx.color(color, 4)}",
        flex_shrink="0",
    )


# ---------------------------------------------------------------------------
# Board builder
# ---------------------------------------------------------------------------

def _build_board(issues: list[Issue]) -> rx.Component:
    # group by squad, then by column
    squad_order = list(SQUAD_LABELS.keys())
    col_keys = [c[0] for c in COLUMNS]

    # index: squad_key → col_key → [issues]
    board: dict[str, dict[str, list[Issue]]] = {
        sq: {col: [] for col in col_keys} for sq in squad_order
    }
    col_totals: dict[str, int] = {col: 0 for col in col_keys}

    for issue in issues:
        sq = issue.squad_key
        if sq not in board:
            continue
        col = _issue_column(issue)
        board[sq][col].append(issue)
        # count WIP (not backlog, not done)
        if col not in ("backlog", "done"):
            col_totals[col] += 1

    # ── header row ────────────────────────────────────────────────────────
    col_headers = [
        rx.box(width="130px", flex_shrink="0"),  # swimlane label placeholder
    ]
    for col_key, col_label, color, wip_limit in COLUMNS:
        current = col_totals[col_key]
        col_headers.append(
            rx.box(
                _col_header(col_key, col_label, color, wip_limit, current),
                width="160px",
                flex_shrink="0",
            )
        )

    # ── swimlane rows ─────────────────────────────────────────────────────
    swimlane_rows = []
    for sq in squad_order:
        cols_in_squad = board[sq]
        total_in_squad = sum(len(v) for v in cols_in_squad.values())
        if total_in_squad == 0:
            continue

        cells = [
            # swimlane label
            rx.flex(
                rx.text(
                    SQUAD_LABELS[sq],
                    size="1",
                    weight="medium",
                    color=rx.color("gray", 11),
                    style={"writing_mode": "horizontal-tb"},
                ),
                rx.text(
                    str(total_in_squad),
                    size="1",
                    color=rx.color("gray", 9),
                ),
                direction="column",
                gap="4px",
                justify="center",
                align="start",
                width="130px",
                flex_shrink="0",
                padding=f"8px {SPACING['sm']}",
                background=rx.color("gray", 2),
                border_right=f"{BORDER} {rx.color('gray', 4)}",
                min_height="60px",
            ),
        ]

        for col_key, col_label, color, wip_limit in COLUMNS:
            card_list = cols_in_squad.get(col_key, [])
            cell_cards = [_card(i) for i in card_list]
            cells.append(
                rx.box(
                    *cell_cards,
                    rx.cond(
                        len(card_list) == 0,
                        rx.box(height="40px"),
                        rx.box(),
                    ),
                    display="flex",
                    flex_direction="column",
                    gap="6px",
                    width="160px",
                    flex_shrink="0",
                    padding="8px",
                    background=rx.color("gray", 1),
                    border_right=f"{BORDER} {rx.color('gray', 3)}",
                    min_height="60px",
                    align_items="stretch",
                )
            )

        swimlane_rows.append(
            rx.flex(
                *cells,
                width="100%",
                border_top=f"{BORDER} {rx.color('gray', 4)}",
                align="stretch",
            )
        )

    return rx.box(
        rx.box(
            rx.flex(
                *col_headers,
                width="100%",
                align="stretch",
            ),
            *swimlane_rows,
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            overflow="hidden",
            width="fit-content",
            min_width="100%",
        ),
        overflow_x="auto",
        width="100%",
    )


_LEGEND_ITEMS = [
    ("tomato", "Blocked"),
    ("blue", "Story"),
    ("tomato", "Bug"),
    ("violet", "Research spike"),
    ("iris", "Design"),
    ("amber", "Experiment"),
    ("cyan", "Requirement"),
    ("plum", "ADR"),
    ("orange", "Tech debt"),
]


# ---------------------------------------------------------------------------
# Tab entry point
# ---------------------------------------------------------------------------

def _kanban_for(issues) -> rx.Component:
    board = _build_board(issues)

    total = len(issues)
    wip = sum(1 for i in issues if i.status in ("In Progress", "In Review"))
    blocked = sum(1 for i in issues if i.blocked_by)

    return rx.box(
        section_header(
            "Kanban Board",
            subtitle="Read-only · swimlanes по 9 командам · 6 колонок · WIP limits",
            action=data_source_badge("mock"),
        ),
        # summary strip
        rx.flex(
            rx.flex(
                rx.text("Всего задач:", size="2", color=rx.color("gray", 9)),
                rx.text(str(total), size="2", weight="bold", color=rx.color("gray", 12)),
                gap="6px", align="center",
            ),
            rx.flex(
                rx.text("WIP сейчас:", size="2", color=rx.color("gray", 9)),
                rx.text(str(wip), size="2", weight="bold",
                        color=rx.color("amber", 11) if wip > 15 else rx.color("gray", 12)),
                gap="6px", align="center",
            ),
            rx.flex(
                rx.text("Заблокировано:", size="2", color=rx.color("gray", 9)),
                rx.text(str(blocked), size="2", weight="bold",
                        color=rx.color("tomato", 11) if blocked > 0 else rx.color("gray", 12)),
                gap="6px", align="center",
            ),
            gap=SPACING["xl"],
            margin_bottom=SPACING["md"],
            flex_wrap="wrap",
        ),
        board,
        rx.box(height=SPACING["md"]),
        color_legend(_LEGEND_ITEMS),
        padding=SPACING["xl"],
        max_width="1400px",
        margin="0 auto",
    )


def kanban_tab() -> rx.Component:
    return _kanban_for(load_issues())


def dash_kanban_tab() -> rx.Component:
    return _kanban_for(load_issues(DASH_CONFIG))
