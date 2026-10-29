"""
Navigation — two variants toggled via burger menu:
  - "sidebar"  : vertical left panel, fixed width
  - "tabs"     : horizontal bar at top

Only tabs in BUILT_TABS are clickable; the rest are greyed out with a
"в разработке" tooltip so the portfolio viewer sees the full SDLC
structure without hitting empty pages.

Project selector dropdown lives at the top of the sidebar (and inline
in the tabs bar) and switches ProjectState.project_mode between
"motif" and "kp".
"""

import reflex as rx
from ..states import NavState, ProjectState, NAV_TABS, BUILT_TABS, show_mode
from ..states.ba_sa_state import BaSaState
from ..tokens import SPACING, SIDEBAR_WIDTH, BORDER, STATE, ROLE

_SIDEBAR_W = SIDEBAR_WIDTH
_TAB_H = "48px"


def _mode_menu_item(mode: str, label: str, sub: str, on_click) -> rx.Component:
    """Один пункт переключателя проекта. Вынесен из трёх почти одинаковых блоков
    (Motif / KP / Product Dashboard), чтобы правка меню жила в одном месте."""
    return rx.dropdown_menu.item(
        rx.flex(
            rx.flex(
                rx.icon("check", size=14,
                        color=rx.cond(
                            ProjectState.project_mode == mode,
                            rx.color("teal", 9),
                            "transparent",
                        )),
                width="20px",
                justify="center",
            ),
            rx.flex(
                rx.text(label, size="2", weight="medium"),
                rx.text(sub, size="1", color=ROLE["text-secondary"]),
                direction="column",
                gap="0",
            ),
            align="center",
            gap="6px",
        ),
        on_click=on_click,
    )


def _project_dropdown() -> rx.Component:
    """
    Project selector dropdown — replaces the static 'Demo Dashboard' header.
    Shows current project name + chevron; clicking opens a menu to switch modes.
    """
    current_label = rx.cond(
        ProjectState.project_mode == "motif",
        "Motif",
        rx.cond(ProjectState.project_mode == "kp", "Knowledge Pipeline", "Product Dashboard"),
    )
    current_sub = rx.cond(
        ProjectState.project_mode == "motif",
        "Demo · вымышленная команда",
        rx.cond(ProjectState.project_mode == "kp", "Real · соло-пайплайн", "Real · этот дашборд"),
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
                            color=ROLE["text-primary"],
                        ),
                        rx.text(
                            current_sub,
                            size="1",
                            color=ROLE["text-secondary"],
                        ),
                        direction="column",
                        gap="0",
                    ),
                    align="center",
                    gap=SPACING["sm"],
                    flex="1",
                ),
                rx.icon("chevron-down", size=14, color=ROLE["text-secondary"]),
                align="center",
                justify="between",
                width="100%",
                padding=SPACING["md"],
                cursor="pointer",
                border_bottom=f"{BORDER} {ROLE['border-default']}",
                _hover={"background": STATE["hover-bg-subtle"]},
            ),
            as_child=True,
        ),
        rx.dropdown_menu.content(
            _mode_menu_item(
                "motif", "Motif", "Demo · вымышленная продуктовая команда",
                ProjectState.set_motif,
            ),
            # Knowledge Pipeline (real) — в переключателе только в ЛОКАЛЬНОЙ сборке.
            # В публичной сборке проект закрыт (DASH-162, show_mode). Прежнее
            # решение Guzel 25.07 «пока не показываем» заменено на «видно локально».
            *(
                [_mode_menu_item(
                    "kp", "Knowledge Pipeline", "Real · соло-пайплайн · локально",
                    ProjectState.set_kp,
                )]
                if show_mode("kp") else []
            ),
            rx.dropdown_menu.separator(),
            _mode_menu_item(
                "dash", "Product Dashboard", "Real · этот дашборд как продуктовый проект",
                ProjectState.set_dash,
            ),
            width="280px",
        ),
        modal=False,
    )


def _sidebar_item(key: str, label: str, icon: str) -> rx.Component:
    is_active = NavState.active_tab == key
    is_built = key in BUILT_TABS
    is_sub = key in {"ds", "discover", "define", "develop", "deliver"}

    item = rx.flex(
        rx.icon(icon, size=16),
        rx.text(label, size="2"),
        align="center",
        gap=SPACING["sm"],
        padding=f"{SPACING['sm']} {SPACING['md']}",
        margin_left="20px" if is_sub else "0",
        border_radius="var(--radius-2)",
        border_left=f"2px solid {ROLE['border-default']}" if is_sub else "none",
        cursor="pointer" if is_built else "default",
        background=rx.cond(is_active, rx.color("teal", 3), "transparent"),
        color=rx.cond(
            is_active,
            rx.color("teal", 11),
            rx.color("gray", 10 if is_built else 7),
        ),
        width="100%",
        _hover={"background": STATE["hover-bg"]} if is_built else {},
        on_click=NavState.set_tab(key) if is_built else None,
    )

    if not is_built:
        return rx.tooltip(item, content="В разработке")
    return item


def _ba_sa_sub_item(item: rx.Var) -> rx.Component:
    """Один из двенадцати разделов конспекта. Иконки нет намеренно: двенадцать
    одинаковых значков подряд — шум, отступ и полоска слева и так показывают
    вложенность."""
    is_active = (NavState.active_tab == "analysis") & (BaSaState.active_slug == item["slug"])
    return rx.flex(
        rx.text(item["title"], size="2"),
        align="center",
        padding=f"{SPACING['sm']} {SPACING['md']}",
        margin_left="20px",
        border_radius="var(--radius-2)",
        border_left=f"2px solid {ROLE['border-default']}",
        cursor="pointer",
        background=rx.cond(is_active, rx.color("teal", 3), "transparent"),
        color=rx.cond(is_active, rx.color("teal", 11), rx.color("gray", 10)),
        width="100%",
        _hover={"background": STATE["hover-bg"]},
        on_click=[
            NavState.set_tab("analysis"),
            BaSaState.open_section(item["slug"]),
        ],
    )


def _ba_sa_accordion(label: str, icon: str) -> rx.Component:
    """Requirements · BA/SA как группа с разделами внутри — устроено так же,
    как Design с его пятью подвкладками.

    Отличие от Design: там подвкладки перечислены в NAV_TABS, а здесь их
    список приходит из файлов на диске, поэтому строится через foreach по
    состоянию. Показываем вложенное только в режиме Product Dashboard —
    в других проектах на этой вкладке реестр требований, а не конспект.
    """
    is_active = NavState.active_tab == "analysis"
    has_sections = (
        (ProjectState.project_mode == "dash") & (BaSaState.sections.length() > 0)
    )
    return rx.fragment(
        rx.flex(
            rx.icon(icon, size=16),
            rx.text(label, size="2"),
            rx.box(flex="1"),
            rx.cond(
                has_sections,
                rx.icon(
                    rx.cond(NavState.analysis_open, "chevron-up", "chevron-down"),
                    size=12,
                    color=rx.color("gray", 7),
                ),
                rx.fragment(),
            ),
            align="center",
            gap=SPACING["sm"],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border_radius="var(--radius-2)",
            cursor="pointer",
            background=rx.cond(is_active, rx.color("teal", 3), "transparent"),
            color=rx.cond(is_active, rx.color("teal", 11), rx.color("gray", 10)),
            width="100%",
            _hover={"background": STATE["hover-bg"]},
            on_click=NavState.toggle_analysis,
        ),
        rx.cond(
            has_sections & NavState.analysis_open,
            rx.foreach(BaSaState.sections, _ba_sa_sub_item),
            rx.fragment(),
        ),
    )


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
            _hover={"background": STATE["hover-bg"]},
            on_click=NavState.toggle_design,
        ),
        rx.cond(
            NavState.design_open,
            rx.fragment(
                _sidebar_item("ds", "Design System", "palette"),
                _sidebar_item("discover", "Discover", "search"),
                _sidebar_item("define", "Define", "target"),
                _sidebar_item("develop", "Develop", "hammer"),
                _sidebar_item("deliver", "Deliver", "rocket"),
            ),
            rx.fragment(),
        ),
    )


def _sidebar_items() -> list[rx.Component]:
    items = []
    for key, label, icon in NAV_TABS:
        if key == "design":
            items.append(_design_accordion())
        elif key == "analysis":
            items.append(_ba_sa_accordion(label, icon))
        elif key in {"ds", "discover", "define", "develop", "deliver"}:
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
        border_right=f"{BORDER} {ROLE['border-default']}",
        background=ROLE["bg-card"],
        flex_shrink="0",
    )

