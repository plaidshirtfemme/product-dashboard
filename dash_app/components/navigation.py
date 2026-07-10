"""
Navigation — two variants toggled via burger menu:
  - "sidebar"  : vertical left panel, fixed width
  - "tabs"     : horizontal bar at top

Only tabs in BUILT_TABS are clickable; the rest are greyed out with a
"в разработке" tooltip so the portfolio viewer sees the full SDLC
structure without hitting empty pages.

Project selector dropdown lives at the top of the sidebar (and inline
in the tabs bar) and switches ProjectState.project_mode between
"demo" and "real".
"""

import reflex as rx
from ..states import NavState, ProjectState, NAV_TABS, BUILT_TABS
from ..tokens import SPACING, SIDEBAR_WIDTH, BORDER

_SIDEBAR_W = SIDEBAR_WIDTH
_TAB_H = "48px"


def _burger_btn() -> rx.Component:
    return rx.tooltip(
        rx.icon_button(
            rx.icon("menu", size=18),
            variant="ghost",
            color_scheme="gray",
            on_click=NavState.toggle_variant,
            size="2",
        ),
        content=rx.cond(
            NavState.nav_variant == "sidebar",
            "Переключить на горизонтальные табы",
            "Переключить на боковую панель",
        ),
    )


def _project_dropdown() -> rx.Component:
    """
    Project selector dropdown — replaces the static 'Demo Dashboard' header.
    Shows current project name + chevron; clicking opens a menu to switch modes.
    """
    current_label = rx.cond(
        ProjectState.project_mode == "demo",
        "Motif",
        rx.cond(ProjectState.project_mode == "real", "Knowledge Pipeline", "Product Dashboard"),
    )
    current_sub = rx.cond(
        ProjectState.project_mode == "demo",
        "Demo · вымышленная команда",
        rx.cond(ProjectState.project_mode == "real", "Real · соло-пайплайн", "Real · этот дашборд"),
    )

    return rx.dropdown_menu.root(
        rx.dropdown_menu.trigger(
            rx.flex(
                rx.flex(
                    rx.icon("layers", size=16, color=rx.color("teal", 9)),
                    rx.flex(
                        rx.text(
                            current_label,
                            size="2",
                            weight="medium",
                            color=rx.color("gray", 12),
                        ),
                        rx.text(
                            current_sub,
                            size="1",
                            color=rx.color("gray", 9),
                        ),
                        direction="column",
                        gap="0",
                    ),
                    align="center",
                    gap=SPACING["sm"],
                    flex="1",
                ),
                rx.icon("chevron-down", size=14, color=rx.color("gray", 9)),
                align="center",
                justify="between",
                width="100%",
                padding=SPACING["md"],
                cursor="pointer",
                border_bottom=f"{BORDER} {rx.color('gray', 4)}",
                _hover={"background": rx.color("gray", 2)},
            ),
            as_child=True,
        ),
        rx.dropdown_menu.content(
            rx.dropdown_menu.item(
                rx.flex(
                    rx.flex(
                        rx.icon("check", size=14,
                                color=rx.cond(
                                    ProjectState.project_mode == "demo",
                                    rx.color("teal", 9),
                                    "transparent",
                                )),
                        width="20px",
                        justify="center",
                    ),
                    rx.flex(
                        rx.text("Motif", size="2", weight="medium"),
                        rx.text("Demo · вымышленная продуктовая команда", size="1",
                                color=rx.color("gray", 9)),
                        direction="column",
                        gap="0",
                    ),
                    align="center",
                    gap="6px",
                ),
                on_click=ProjectState.set_demo,
            ),
            rx.dropdown_menu.separator(),
            rx.dropdown_menu.item(
                rx.flex(
                    rx.flex(
                        rx.icon("check", size=14,
                                color=rx.cond(
                                    ProjectState.project_mode == "real",
                                    rx.color("teal", 9),
                                    "transparent",
                                )),
                        width="20px",
                        justify="center",
                    ),
                    rx.flex(
                        rx.text("Knowledge Pipeline", size="2", weight="medium"),
                        rx.text("Real · соло-пайплайн YouTube→Obsidian", size="1",
                                color=rx.color("gray", 9)),
                        direction="column",
                        gap="0",
                    ),
                    align="center",
                    gap="6px",
                ),
                on_click=ProjectState.set_real,
            ),
            rx.dropdown_menu.separator(),
            rx.dropdown_menu.item(
                rx.flex(
                    rx.flex(
                        rx.icon("check", size=14,
                                color=rx.cond(
                                    ProjectState.project_mode == "dash",
                                    rx.color("teal", 9),
                                    "transparent",
                                )),
                        width="20px",
                        justify="center",
                    ),
                    rx.flex(
                        rx.text("Product Dashboard", size="2", weight="medium"),
                        rx.text("Real · этот дашборд как продуктовый проект", size="1",
                                color=rx.color("gray", 9)),
                        direction="column",
                        gap="0",
                    ),
                    align="center",
                    gap="6px",
                ),
                on_click=ProjectState.set_dash,
            ),
            width="280px",
        ),
        modal=False,
    )


def _project_dropdown_compact() -> rx.Component:
    """Compact version for the horizontal tabs bar."""
    current_label = rx.cond(
        ProjectState.project_mode == "demo",
        "Motif",
        rx.cond(ProjectState.project_mode == "real", "KP", "DASH"),
    )
    return rx.dropdown_menu.root(
        rx.dropdown_menu.trigger(
            rx.flex(
                rx.icon("layers", size=14, color=rx.color("teal", 9)),
                rx.text(current_label, size="1", weight="medium",
                        color=rx.color("gray", 11)),
                rx.icon("chevron-down", size=12, color=rx.color("gray", 8)),
                align="center",
                gap="4px",
                padding=f"4px {SPACING['sm']}",
                border=f"{BORDER} {rx.color('gray', 5)}",
                border_radius="var(--radius-2)",
                cursor="pointer",
                _hover={"background": rx.color("gray", 2)},
            ),
            as_child=True,
        ),
        rx.dropdown_menu.content(
            rx.dropdown_menu.item(
                rx.flex(
                    rx.icon("check", size=14,
                            color=rx.cond(
                                ProjectState.project_mode == "demo",
                                rx.color("teal", 9), "transparent",
                            )),
                    rx.text("Motif (Demo)", size="2"),
                    align="center", gap="6px",
                ),
                on_click=ProjectState.set_demo,
            ),
            rx.dropdown_menu.separator(),
            rx.dropdown_menu.item(
                rx.flex(
                    rx.icon("check", size=14,
                            color=rx.cond(
                                ProjectState.project_mode == "real",
                                rx.color("teal", 9), "transparent",
                            )),
                    rx.text("Knowledge Pipeline (Real)", size="2"),
                    align="center", gap="6px",
                ),
                on_click=ProjectState.set_real,
            ),
            rx.dropdown_menu.separator(),
            rx.dropdown_menu.item(
                rx.flex(
                    rx.icon("check", size=14,
                            color=rx.cond(
                                ProjectState.project_mode == "dash",
                                rx.color("teal", 9), "transparent",
                            )),
                    rx.text("Product Dashboard (Real)", size="2"),
                    align="center", gap="6px",
                ),
                on_click=ProjectState.set_dash,
            ),
            width="240px",
        ),
        modal=False,
    )


def _sidebar_item(key: str, label: str, icon: str) -> rx.Component:
    is_active = NavState.active_tab == key
    is_built = key in BUILT_TABS
    is_sub = key == "ds"

    item = rx.flex(
        rx.icon(icon, size=16),
        rx.text(label, size="2"),
        align="center",
        gap=SPACING["sm"],
        padding=f"{SPACING['sm']} {SPACING['md']}",
        margin_left="20px" if is_sub else "0",
        border_radius="var(--radius-2)",
        border_left=f"2px solid {rx.color('gray', 4)}" if is_sub else "none",
        cursor="pointer" if is_built else "default",
        background=rx.cond(is_active, rx.color("teal", 3), "transparent"),
        color=rx.cond(
            is_active,
            rx.color("teal", 11),
            rx.color("gray", 10 if is_built else 7),
        ),
        width="100%",
        _hover={"background": rx.color("gray", 3)} if is_built else {},
        on_click=NavState.set_tab(key) if is_built else None,
    )

    if not is_built:
        return rx.tooltip(item, content="В разработке")
    return item


def _design_accordion() -> rx.Component:
    """Design group header + collapsible Design System sub-item."""
    is_active = NavState.active_tab == "design"
    return rx.fragment(
        rx.flex(
            rx.icon("pen-tool", size=16),
            rx.text("Design", size="2"),
            rx.box(flex="1"),
            rx.icon(
                rx.cond(NavState.design_open, "chevron-up", "chevron-down"),
                size=12,
                color=rx.color("gray", 7),
            ),
            align="center",
            gap=SPACING["sm"],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border_radius="var(--radius-2)",
            cursor="pointer",
            background=rx.cond(is_active, rx.color("teal", 3), "transparent"),
            color=rx.cond(is_active, rx.color("teal", 11), rx.color("gray", 10)),
            width="100%",
            _hover={"background": rx.color("gray", 3)},
            on_click=NavState.toggle_design,
        ),
        rx.cond(
            NavState.design_open,
            _sidebar_item("ds", "Design System", "palette"),
            rx.fragment(),
        ),
    )


def _sidebar_items() -> list[rx.Component]:
    items = []
    for key, label, icon in NAV_TABS:
        if key == "design":
            items.append(_design_accordion())
        elif key == "ds":
            pass  # rendered inside _design_accordion
        else:
            items.append(_sidebar_item(key, label, icon))
    return items


def sidebar_nav() -> rx.Component:
    return rx.flex(
        _project_dropdown(),
        rx.flex(
            *_sidebar_items(),
            direction="column",
            gap="2px",
            padding=SPACING["sm"],
            flex="1",
            overflow_y="auto",
        ),
        direction="column",
        width=_SIDEBAR_W,
        min_width=_SIDEBAR_W,
        height="100vh",
        border_right=f"{BORDER} {rx.color('gray', 4)}",
        background=rx.color("gray", 1),
        flex_shrink="0",
    )


def _tab_item(key: str, label: str) -> rx.Component:
    is_active = NavState.active_tab == key
    is_built = key in BUILT_TABS

    item = rx.box(
        rx.text(label, size="2", weight=rx.cond(is_active, "medium", "regular")),
        padding=f"0 {SPACING['md']}",
        height=_TAB_H,
        display="flex",
        align_items="center",
        border_bottom=rx.cond(is_active, f"2px solid {rx.color('teal', 9)}", "2px solid transparent"),
        color=rx.cond(
            is_active,
            rx.color("teal", 11),
            rx.color("gray", 10 if is_built else 7),
        ),
        cursor="pointer" if is_built else "default",
        white_space="nowrap",
        _hover={"color": rx.color("teal", 10)} if is_built else {},
        on_click=NavState.set_tab(key) if is_built else None,
    )

    if not is_built:
        return rx.tooltip(item, content="В разработке")
    return item


def tabs_nav() -> rx.Component:
    return rx.flex(
        _burger_btn(),
        rx.box(
            rx.flex(
                *[_tab_item(key, label) for key, label, _ in NAV_TABS if key != "ds"],
                gap="0",
            ),
            overflow_x="auto",
            flex="1",
        ),
        _project_dropdown_compact(),
        align="center",
        gap=SPACING["sm"],
        padding=f"0 {SPACING['md']}",
        height=_TAB_H,
        border_bottom=f"{BORDER} {rx.color('gray', 4)}",
        background=rx.color("gray", 1),
        width="100%",
        position="sticky",
        top="0",
        z_index="10",
    )
