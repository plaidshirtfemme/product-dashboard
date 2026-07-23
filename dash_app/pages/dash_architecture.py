"""
Architecture tab — Product Dashboard mode (dash).

DASH-129, часть 1: C4-модель СОБСТВЕННОЙ архитектуры дашборда, выведенная в UI.
Мета: дашборд документирует сам себя (self-hosting). Подаётся как ГЛУБИНА под
дизайн-заголовком (systems-thinking Product Designer), не как «я архитектор».

Три уровня C4 переключаются сегментами (DashArchState.c4_level):
  1. System Context — кто пользуется дашбордом и с чем он интегрируется.
  2. Container      — из чего состоит система как набор запускаемых частей (Reflex).
  3. Component      — внутренности бэкенда: router → pages → components/state/data.

Диаграмма статична (архитектура не тянется из данных) — рисуется нативными
rx-боксами на токенах, связи показаны колоночным потоком со стрелками-глифами.
Части 2–4 DASH-129 (Figma-цепочка, схема Goal→Epic→Issue, ADR) — отдельно.
"""

import reflex as rx

from ..tokens import SPACING, BORDER, PAGE_MAX_WIDTH
from ..components import section_header
from ..states.dash_arch_state import DashArchState

_MAX = PAGE_MAX_WIDTH  # 1100px — вмещает полосы из 4 узлов, как у motif-версии Architecture

# ---------------------------------------------------------------------------
# C4 node — one styled box per element kind.
# kinds: person | system (in-focus) | external | container | component
# ---------------------------------------------------------------------------

# Overlay text colors for dark-filled nodes (person / focus system) — rgba over
# the fill, not a palette color, so they stay legible on any accent shade.
_ON_DARK_TITLE = "white"
_ON_DARK_DESC = "rgba(255,255,255,0.78)"
_ON_DARK_TECH = "rgba(255,255,255,0.60)"


def _kind_style(kind: str) -> dict:
    if kind == "person":
        return dict(
            background=rx.color("slate", 12),
            border="none",
            title_color=_ON_DARK_TITLE, desc_color=_ON_DARK_DESC,
            tech_color=_ON_DARK_TECH, icon_color="white",
        )
    if kind == "system":
        return dict(
            background=rx.color("teal", 9),
            border="none",
            title_color=_ON_DARK_TITLE, desc_color=_ON_DARK_DESC,
            tech_color=_ON_DARK_TECH, icon_color="white",
        )
    if kind == "container":
        return dict(
            background=rx.color("teal", 3),
            border=f"{BORDER} {rx.color('teal', 6)}",
            title_color=rx.color("gray", 12), desc_color=rx.color("gray", 11),
            tech_color=rx.color("teal", 10), icon_color=rx.color("teal", 9),
        )
    if kind == "component":
        return dict(
            background="white",
            border=f"{BORDER} {rx.color('gray', 5)}",
            border_left=f"3px solid {rx.color('teal', 7)}",
            title_color=rx.color("gray", 12), desc_color=rx.color("gray", 11),
            tech_color=rx.color("gray", 9), icon_color=rx.color("teal", 9),
        )
    # external
    return dict(
        background=rx.color("gray", 3),
        border=f"{BORDER} {rx.color('gray', 6)}",
        title_color=rx.color("gray", 12), desc_color=rx.color("gray", 11),
        tech_color=rx.color("gray", 9), icon_color=rx.color("gray", 10),
    )


def _c4_node(
    kind: str,
    title: str,
    icon: str,
    tech: str,
    desc: str,
    width: str = "240px",
) -> rx.Component:
    s = _kind_style(kind)
    return rx.flex(
        rx.flex(
            rx.icon(icon, size=16, color=s["icon_color"], flex_shrink="0"),
            rx.text(title, size="2", weight="bold", color=s["title_color"],
                    line_height="1.3"),
            align="center",
            gap=SPACING["sm"],
        ),
        rx.text(tech, size="1", color=s["tech_color"],
                style={"font_family": "var(--font-mono, monospace)"},
                margin_top="2px"),
        rx.text(desc, size="1", color=s["desc_color"], line_height="1.45",
                margin_top="4px"),
        direction="column",
        gap="0",
        padding=SPACING["md"],
        width=width,
        min_height="104px",
        background=s["background"],
        border=s.get("border", "none"),
        border_left=s.get("border_left"),
        border_radius="var(--radius-3)",
        box_shadow="0 1px 2px rgba(0,0,0,0.04)",
    )


# ---------------------------------------------------------------------------
# Connectors — labelled arrow glyphs for the columnar flow.
# ---------------------------------------------------------------------------

def _down_arrow(label: str, width: str = "auto", icon: str = "arrow-down") -> rx.Component:
    return rx.flex(
        rx.text(label, size="1", color=rx.color("gray", 10),
                text_align="center", line_height="1.3",
                style={"max_width": "260px"}),
        rx.icon(icon, size=18, color=rx.color("teal", 8)),
        direction="column",
        align="center",
        gap="2px",
        width=width,
        padding_y=SPACING["xs"],
    )


def _band(*children, gap: str | None = None) -> rx.Component:
    """A horizontal row of nodes, centered, wrapping on narrow screens."""
    return rx.flex(
        *children,
        direction="row",
        wrap="wrap",
        justify="center",
        align="stretch",
        gap=gap or SPACING["lg"],
        width="100%",
    )


# ---------------------------------------------------------------------------
# Level 1 — System Context
# ---------------------------------------------------------------------------

def _context_view() -> rx.Component:
    return rx.flex(
        # People
        _band(
            _c4_node("person", "Рекрутер / Hiring manager", "user",
                     "[Person]",
                     "Смотрит кейс, оценивает продуктовые компетенции. North Star: "
                     "понимает контекст за 30 секунд."),
            _c4_node("person", "Guzel K.", "user-cog",
                     "[Person · PM / Designer / Dev]",
                     "Ведёт проект, наполняет данными, деплоит. Единственная A по RACI."),
        ),
        _band(
            _down_arrow("просматривает в браузере", width="240px"),
            _down_arrow("разрабатывает и наполняет", width="240px"),
        ),
        # System in focus
        _band(
            _c4_node("system", "Product Dashboard", "layout-dashboard",
                     "[Software System · Reflex]",
                     "Портфолио-витрина продуктовых компетенций. Reflex-приложение "
                     "(Python→React) в 3 режимах проекта: Motif / Knowledge Pipeline / этот дашборд.",
                     width="380px"),
        ),
        _down_arrow("развёрнут на · хранит код · синкает токены · читает реальные данные"),
        # External systems
        _band(
            _c4_node("external", "Reflex Cloud", "cloud",
                     "[Хостинг]",
                     "Фронт + websocket-бэкенд. Регион fra, машина c1m1, без пингера."),
            _c4_node("external", "GitHub", "folder-git-2",
                     "[VCS · Releases]",
                     "Репозиторий и аннотированные SemVer-релизы — витрина эволюции проекта."),
            _c4_node("external", "Figma · Tokens Studio", "pen-tool",
                     "[Дизайн-инструмент]",
                     "Синк дизайн-токенов: design_tokens.json ↔ Tokens Studio ↔ Figma Variables."),
            _c4_node("external", "Obsidian Vault · KP", "database",
                     "[Источник данных]",
                     "Реальный Knowledge Pipeline: vault_snapshot питает real-режим дашборда."),
        ),
        direction="column",
        align="center",
        gap=SPACING["xs"],
        width="100%",
    )


# ---------------------------------------------------------------------------
# Level 2 — Container
# ---------------------------------------------------------------------------

def _container_view() -> rx.Component:
    return rx.flex(
        _band(
            _c4_node("external", "Браузер рекрутера", "monitor",
                     "[Web browser]",
                     "Загружает SPA, рендерит вкладки, шлёт события пользователя.",
                     width="320px"),
        ),
        _down_arrow("HTTPS · отдаёт статику и SPA"),
        _band(
            _c4_node("container", "Frontend SPA", "app-window",
                     "[Container · React / Vite]",
                     "Скомпилирован из Python (.web/). Отрисовывает UI, применяет дельты "
                     "состояния, шлёт события. Reflex генерит React — JS-файлов не пишем.",
                     width="360px"),
        ),
        _down_arrow("WebSocket · события ↔ дельты состояния", icon="arrow-up-down"),
        _band(
            _c4_node("container", "Reflex Backend", "server",
                     "[Container · Python / FastAPI]",
                     "Python-процесс (dash_app/, reflex run). Держит State, гоняет "
                     "event handlers, компилирует Python-компоненты во фронт.",
                     width="360px"),
        ),
        _down_arrow("держит в памяти · читает при импорте"),
        _band(
            _c4_node("container", "State (in-memory)", "toggle-left",
                     "[Container · rx.State]",
                     "NavState (активная вкладка), ProjectState (режим проекта), "
                     "backlog_state / dash_arch_state (фильтры, уровень C4)."),
            _c4_node("container", "Data & Tokens (static)", "database",
                     "[Container · Python / JSON]",
                     "jira_mock_raw, real_project_extract, vault_snapshot.json, okr, "
                     "design_tokens.json. Читаются при импорте, не БД."),
        ),
        direction="column",
        align="center",
        gap=SPACING["xs"],
        width="100%",
    )


# ---------------------------------------------------------------------------
# Level 3 — Component (inside Reflex Backend)
# ---------------------------------------------------------------------------

def _component_view() -> rx.Component:
    return rx.flex(
        _band(
            _c4_node("component", "App shell", "app-window",
                     "dash_app.py · layout.py",
                     "Каркас: тема (Radix), sidebar + область страницы. Монтирует роутер.",
                     width="360px"),
        ),
        _down_arrow("монтирует page_content"),
        _band(
            _c4_node("component", "Tab Router", "route",
                     "router.py",
                     "active_tab → нужный компонент. _by_project() разводит demo / real / "
                     "dash одной вкладкой.",
                     width="360px"),
        ),
        _down_arrow("выбирает вкладку по режиму"),
        _band(
            _c4_node("component", "Pages", "layout-grid",
                     "pages/*.py  (~40 вкладок)",
                     "Функции-вкладки → rx.Component. Читают state, зовут адаптер данных, "
                     "собирают UI из компонентов.",
                     width="380px"),
        ),
        _down_arrow("используют · читают · запрашивают"),
        _band(
            _c4_node("component", "UI Components", "blocks",
                     "components/*.py",
                     "stat_card, data_table, section_header — переиспользуемые молекулы.",
                     width="230px"),
            _c4_node("component", "States", "toggle-left",
                     "states/*.py",
                     "Реактивные vars: фильтры, поиск, режим, уровень C4.",
                     width="230px"),
            _c4_node("component", "Data Adapter", "cable",
                     "data/adapter.py",
                     "load_issues(config) — единая точка входа к любым данным.",
                     width="230px"),
            _c4_node("component", "Tokens", "palette",
                     "tokens/tokens.py",
                     "Читает design_tokens.json → SPACING / BORDER / COLORS.",
                     width="230px"),
        ),
        _down_arrow("Data Adapter грузит источник по режиму"),
        _band(
            _c4_node("component", "Data Sources", "database",
                     "data/jira_mock_raw · real_project_extract · vault_snapshot",
                     "Hand-authored DASH-история, статика KP-пайплайна, снэпшот Obsidian-vault.",
                     width="480px"),
        ),
        direction="column",
        align="center",
        gap=SPACING["xs"],
        width="100%",
    )


# ---------------------------------------------------------------------------
# Level switcher (segmented control) + legend
# ---------------------------------------------------------------------------

_LEVELS = [
    ("context",   "1 · System Context", "Кто пользуется и с чем интегрируется"),
    ("container", "2 · Container",       "Из каких запускаемых частей состоит"),
    ("component", "3 · Component",       "Внутренности бэкенда"),
]


def _level_button(level: str, label: str, sub: str) -> rx.Component:
    is_active = DashArchState.c4_level == level
    return rx.flex(
        rx.text(label, size="2", weight="medium",
                color=rx.cond(is_active, rx.color("teal", 11), rx.color("gray", 11))),
        rx.text(sub, size="1",
                color=rx.cond(is_active, rx.color("teal", 10), rx.color("gray", 9))),
        direction="column",
        gap="0",
        padding=f"{SPACING['sm']} {SPACING['md']}",
        border_radius="var(--radius-2)",
        cursor="pointer",
        flex="1",
        min_width="200px",
        background=rx.cond(is_active, rx.color("teal", 3), rx.color("gray", 2)),
        border=rx.cond(
            is_active,
            f"{BORDER} {rx.color('teal', 7)}",
            f"{BORDER} {rx.color('gray', 4)}",
        ),
        _hover={"background": rx.cond(is_active, rx.color("teal", 3), rx.color("gray", 3))},
        on_click=DashArchState.set_level(level),
    )


def _switcher() -> rx.Component:
    return rx.flex(
        *[_level_button(lvl, label, sub) for lvl, label, sub in _LEVELS],
        direction="row",
        wrap="wrap",
        gap=SPACING["sm"],
        width="100%",
    )


def _legend_chip(color, label: str) -> rx.Component:
    return rx.flex(
        rx.box(width="12px", height="12px", border_radius="3px",
               background=color, flex_shrink="0"),
        rx.text(label, size="1", color=rx.color("gray", 10)),
        align="center",
        gap="6px",
    )


def _legend() -> rx.Component:
    return rx.flex(
        _legend_chip(rx.color("slate", 12), "Person — актёр"),
        _legend_chip(rx.color("teal", 9), "System — система в фокусе"),
        _legend_chip(rx.color("gray", 3), "External — внешняя система"),
        _legend_chip(rx.color("teal", 3), "Container — запускаемая часть"),
        _legend_chip("white", "Component — модуль внутри бэкенда"),
        direction="row",
        wrap="wrap",
        gap=SPACING["lg"],
        padding=SPACING["md"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        width="100%",
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def dash_architecture_tab() -> rx.Component:
    return rx.box(
        # Meta framing — self-hosting, depth-under-design
        section_header(
            "Архитектура дашборда · C4",
            subtitle="Дашборд документирует свою же архитектуру (self-hosting) · "
                     "глубина под дизайн-заголовком: systems-thinking Product Designer",
        ),
        rx.flex(
            rx.icon("info", size=15, color=rx.color("teal", 9), flex_shrink="0",
                    margin_top="2px"),
            rx.text(
                "Модель C4 — четыре уровня масштаба одной системы. Здесь три: Context "
                "(окружение), Container (запускаемые части), Component (модули бэкенда). "
                "Переключай уровень, чтобы «приблизить» архитектуру.",
                size="1", color=rx.color("gray", 11), line_height="1.5",
            ),
            align="start",
            gap=SPACING["sm"],
            padding=SPACING["md"],
            background=rx.color("teal", 2),
            border_radius="var(--radius-3)",
            margin_bottom=SPACING["md"],
        ),

        _switcher(),
        rx.box(height=SPACING["md"]),
        _legend(),
        rx.box(height=SPACING["xl"]),

        # Diagram — one level at a time
        rx.match(
            DashArchState.c4_level,
            ("context", _context_view()),
            ("container", _container_view()),
            ("component", _component_view()),
            _context_view(),
        ),

        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
