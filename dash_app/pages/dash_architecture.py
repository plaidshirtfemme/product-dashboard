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
from ..data.adapter import load_issues
from ..data.jira_mock_raw import DASH_CONFIG
from ..data.metrics import dash_adrs

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
# Дизайн-токены · мост код ↔ Figma (DASH-129 ч.2)
# Единый источник правды design_tokens.json (W3C DTCG) → две стороны:
# КОД (tokens.py → Reflex, one-way чтение) и ДИЗАЙН (Tokens Studio ↔ Figma
# Variables, two-way синк). Round-trip честный: едут только токены (DASH-119).
# Значения ниже — реальные из tokens/design_tokens.json.
# ---------------------------------------------------------------------------

def _token_cat_chip(name: str, example: str) -> rx.Component:
    return rx.flex(
        rx.text(name, size="1", weight="bold", color=rx.color("teal", 11),
                style={"font_family": "var(--font-mono, monospace)"}),
        rx.text(example, size="1", color=rx.color("gray", 10), line_height="1.35"),
        direction="column",
        gap="1px",
        padding=f"{SPACING['sm']} {SPACING['md']}",
        background=rx.color("gray", 2),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-2)",
        min_width="170px",
        flex="1",
    )


def _branch_col(header: str, icon: str, tag: str, *nodes) -> rx.Component:
    return rx.flex(
        rx.flex(
            rx.icon(icon, size=16, color=rx.color("teal", 9), flex_shrink="0"),
            rx.text(header, size="2", weight="bold", color=rx.color("gray", 12)),
            rx.text(tag, size="1", color=rx.color("gray", 9)),
            align="center",
            gap=SPACING["sm"],
            margin_bottom=SPACING["sm"],
        ),
        *nodes,
        direction="column",
        align="center",
        gap=SPACING["xs"],
        flex="1",
        min_width="340px",
        padding=SPACING["md"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
    )


def _callout_line(mark: str, text: str) -> rx.Component:
    return rx.flex(
        rx.text(mark, size="2", flex_shrink="0"),
        rx.text(text, size="1", color=rx.color("gray", 11), line_height="1.5"),
        direction="row",
        gap=SPACING["sm"],
        align="start",
    )


def _roundtrip_callout() -> rx.Component:
    return rx.flex(
        rx.text("Round-trip — честно", size="1", weight="bold",
                color=rx.color("gray", 12),
                style={"text_transform": "uppercase", "letter_spacing": "0.05em"},
                margin_bottom="2px"),
        _callout_line("✅", "Токены синкаются в обе стороны: "
                      "design_tokens.json ↔ Tokens Studio ↔ Figma Variables."),
        _callout_line("⚠️", "Едут ТОЛЬКО токены. Layout и компоненты — руками в Reflex; "
                      "Figma→код генерации нет (это про JS, не Reflex — DASH-119)."),
        _callout_line("🔜", "Токен-гэп (честно): JSON сейчас плоский; цель — 3 уровня "
                      "primitive → semantic → component (канон DASH-121)."),
        direction="column",
        gap="6px",
        padding=SPACING["lg"],
        background=rx.color("amber", 2),
        border=f"{BORDER} {rx.color('amber', 5)}",
        border_left=f"4px solid {rx.color('amber', 8)}",
        border_radius="var(--radius-3)",
        width="100%",
        margin_top=SPACING["lg"],
    )


def _token_chain_view() -> rx.Component:
    return rx.flex(
        # single source of truth
        _band(
            _c4_node("system", "design_tokens.json", "braces",
                     "[W3C DTCG · single source of truth]",
                     "7 категорий токенов · $schema = design-tokens.github.io. "
                     "Правишь здесь — меняется И код, И Figma.",
                     width="460px"),
        ),
        # real token categories
        rx.flex(
            _token_cat_chip("theme", "accent=teal · gray=slate · radius=medium"),
            _token_cat_chip("color.status", "success=grass · warning=amber · danger=tomato"),
            _token_cat_chip("spacing", "2xs=2px … 2xl=3rem (md=1rem)"),
            _token_cat_chip("border · radius", "1px solid · 4/8/12/9999px"),
            _token_cat_chip("layout", "1100 · 1400 · 220px"),
            _token_cat_chip("typography", "Inter · JetBrains Mono · 12–24px"),
            direction="row", wrap="wrap", gap=SPACING["sm"],
            width="100%", margin_y=SPACING["md"],
        ),
        _down_arrow("питает обе стороны"),
        # two branches
        rx.flex(
            _branch_col(
                "Код", "file-code-2", "Reflex · one-way чтение",
                _c4_node("component", "tokens.py", "braces",
                         "Python-обёртка",
                         "Читает JSON при импорте, отдаёт типизированные dict-ы.",
                         width="300px"),
                _down_arrow("экспортирует"),
                _c4_node("component", "SPACING · BORDER · STATUS_COLORS · …", "list",
                         "EPIC_TYPE_COLORS · RADIUS · TYPE_SCALE · FONTS · THEME_CONFIG",
                         "Semantic-константы для компонентов.",
                         width="300px"),
                _down_arrow("потребляют"),
                _c4_node("component", "Reflex-компоненты", "blocks",
                         "components/*.py · pages/*.py",
                         "Никогда не хардкодят цвет/отступ — только через токены.",
                         width="300px"),
            ),
            _branch_col(
                "Дизайн", "pen-tool", "Figma · two-way синк",
                _c4_node("external", "Tokens Studio", "puzzle",
                         "[Плагин Figma]",
                         "Читает и пишет тот же design_tokens.json — мост JSON ↔ Figma.",
                         width="300px"),
                _down_arrow("синк в обе стороны", icon="arrow-up-down"),
                _c4_node("external", "Figma Variables", "sliders-horizontal",
                         "[Дизайн-сторона]",
                         "Переменные Figma = те же токены. На free-плане — 1 мод (multi-mode платный).",
                         width="300px"),
            ),
            direction="row",
            wrap="wrap",
            justify="center",
            gap=SPACING["lg"],
            width="100%",
        ),
        _roundtrip_callout(),
        direction="column",
        align="center",
        gap=SPACING["xs"],
        width="100%",
    )


# ---------------------------------------------------------------------------
# Goal → Epic → Issue — entity schema (ERD-style SA artifact, DASH-129 ч.3)
# Живые числа: 4 Goals · 12 KR · 19 Epics (8 component/9 business/2 enabler) ·
# ~140 Issues. Источник: okr_dash.py (Objective/KeyResult), jira_mock_raw.py
# (_DASH_EPICS / EPIC_OKR / EPIC_UNLOCKS / get_dash_issues).
# ---------------------------------------------------------------------------

# (field, note, kind) — kind: pk | fk | self | attr
def _erd_attr(field: str, note: str, kind: str = "attr") -> rx.Component:
    marks = {
        "pk":   ("PK", rx.color("teal", 9)),
        "fk":   ("FK", rx.color("blue", 9)),
        "self": ("⟳", rx.color("iris", 9)),
    }
    if kind in marks:
        label, mcolor = marks[kind]
        badge = rx.box(
            rx.text(label, size="1", weight="bold", color="white", line_height="1"),
            background=mcolor,
            border_radius="3px",
            padding="1px 4px",
            min_width="26px",
            style={"text_align": "center"},
            flex_shrink="0",
        )
    else:
        badge = rx.box(width="26px", flex_shrink="0")

    return rx.flex(
        badge,
        rx.text(field, size="1", weight="medium", color=rx.color("gray", 12),
                style={"font_family": "var(--font-mono, monospace)"}, flex_shrink="0"),
        rx.text(note, size="1", color=rx.color("gray", 10), line_height="1.4"),
        align="center",
        gap=SPACING["sm"],
        width="100%",
    )


def _entity_card(name: str, icon: str, count_label: str, count_color,
                 attrs: list[rx.Component], footnote: str) -> rx.Component:
    return rx.flex(
        rx.flex(
            rx.flex(
                rx.icon(icon, size=16, color=rx.color("teal", 9), flex_shrink="0"),
                rx.text(name, size="3", weight="bold", color=rx.color("gray", 12)),
                align="center",
                gap=SPACING["sm"],
            ),
            rx.box(
                rx.text(count_label, size="1", weight="medium", color="white"),
                background=count_color,
                border_radius="var(--radius-2)",
                padding="2px 8px",
            ),
            justify="between",
            align="center",
            width="100%",
        ),
        rx.divider(margin_y=SPACING["sm"], border_color=rx.color("gray", 4)),
        rx.flex(*attrs, direction="column", gap="6px", width="100%"),
        rx.text(footnote, size="1", color=rx.color("gray", 9), line_height="1.4",
                margin_top=SPACING["sm"],
                style={"border_top": f"{BORDER} {rx.color('gray', 3)}", "padding_top": "8px"}),
        direction="column",
        gap="0",
        padding=SPACING["lg"],
        width="560px",
        max_width="100%",
        background="white",
        border=f"{BORDER} {rx.color('gray', 5)}",
        border_left=f"3px solid {rx.color('teal', 7)}",
        border_radius="var(--radius-3)",
        box_shadow="0 1px 2px rgba(0,0,0,0.04)",
    )


def _goal_epic_issue_view() -> rx.Component:
    goal_card = _entity_card(
        "Goal", "target", "O0–O3 · 4 записи · 12 KR", rx.color("teal", 9),
        [
            _erd_attr("tag", "PK · «O0 · North Star» … «O3 · Quality»", "pk"),
            _erd_attr("title", "формулировка цели"),
            _erd_attr("description / quarter", "контекст и горизонт"),
            _erd_attr("key_results[]", "KR-x.y · current / target / unit / baseline"),
        ],
        "okr_dash.py · Objective + KeyResult. North Star = O0, O1–O3 операционные.",
    )
    epic_card = _entity_card(
        "Epic", "layers", "19 эпиков", rx.color("iris", 9),
        [
            _erd_attr("key", "PK · DASH-EPIC-1 … DASH-EPIC-19", "pk"),
            _erd_attr("name / type", "type: business (9) · enabler (2) · component (8)"),
            _erd_attr("okr", "FK → Goal.tag · карта EPIC_OKR", "fk"),
            _erd_attr("unlocks", "→ Epic · enabler разблокирует business (EPIC_UNLOCKS, ×2)", "self"),
        ],
        "jira_mock_raw.py · _DASH_EPICS / EPIC_NAMES / EPIC_TYPES / EPIC_OKR / EPIC_UNLOCKS.",
    )
    issue_card = _entity_card(
        "Issue", "square-check-big", "≈140 задач", rx.color("gray", 9),
        [
            _erd_attr("key", "PK · DASH-1 … DASH-140", "pk"),
            _erd_attr("summary / status / type / priority", "ядро задачи"),
            _erd_attr("squad / sprint / story_points / assignee", "распределение и оценка"),
            _erd_attr("epic", "FK → Epic.key · поле epic в _di()", "fk"),
            _erd_attr("okr", "производный FK → Goal (через epic → EPIC_OKR)", "fk"),
            _erd_attr("links[]", "→ Issue · Blocks / Relates (issuelinks)", "self"),
            _erd_attr("decision_note", "→ CF_DECISION · питает реестр ADR (часть 4)"),
        ],
        "jira_mock_raw.py · get_dash_issues() → _di(). Схема Issue едина с Motif-генератором.",
    )

    return rx.flex(
        # live counts strip
        rx.flex(
            _count_chip("4", "Goals"),
            _count_chip("12", "Key Results"),
            _count_chip("19", "Epics"),
            _count_chip("≈140", "Issues"),
            direction="row", wrap="wrap", gap=SPACING["md"], margin_bottom=SPACING["lg"],
        ),
        goal_card,
        _down_arrow("1 → N · детализируется в эпики  ·  Epic.okr → Goal.tag"),
        epic_card,
        _down_arrow("1 → N · реализуется задачами  ·  Issue.epic → Epic.key"),
        issue_card,
        # notation legend
        rx.flex(
            _legend_chip(rx.color("teal", 9), "PK — первичный ключ"),
            _legend_chip(rx.color("blue", 9), "FK — внешний ключ (ссылка)"),
            _legend_chip(rx.color("iris", 9), "⟳ — само-связь (Epic/Issue на себя)"),
            direction="row", wrap="wrap", gap=SPACING["lg"],
            margin_top=SPACING["lg"], padding=SPACING["md"],
            background=rx.color("gray", 1),
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
        ),
        direction="column",
        align="center",
        gap=SPACING["xs"],
        width="100%",
    )


def _count_chip(value: str, label: str) -> rx.Component:
    return rx.flex(
        rx.text(value, size="4", weight="bold", color=rx.color("teal", 11)),
        rx.text(label, size="1", color=rx.color("gray", 10)),
        direction="column",
        align="center",
        gap="0",
        padding=f"{SPACING['sm']} {SPACING['lg']}",
        background=rx.color("teal", 2),
        border_radius="var(--radius-3)",
        min_width="100px",
    )


# ---------------------------------------------------------------------------
# Key ADR register (DASH-129 ч.4) — decision_note на реальных DASH-задачах
# (метка architecture / squad ARCHITECTURE). Данные — dash_adrs(load_issues(DASH_CONFIG)).
# ---------------------------------------------------------------------------

_ADR_STATUS_COLOR = {
    "Done":        "grass",
    "In Review":   "blue",
    "In Progress": "amber",
    "To Do":       "gray",
}


def _adr_card(row) -> rx.Component:
    accent = {
        "Done":        rx.color("grass", 7),
        "In Progress": rx.color("amber", 7),
        "In Review":   rx.color("blue", 7),
    }.get(row.status, rx.color("gray", 6))

    label_chips = [
        rx.badge(lbl, color_scheme="gray", variant="outline", size="1")
        for lbl in row.labels
    ]

    return rx.flex(
        rx.flex(
            rx.flex(
                rx.text(row.key, size="1", weight="bold", color=rx.color("gray", 11),
                        style={"font_family": "var(--font-mono, monospace)"}),
                rx.badge(row.status,
                         color_scheme=_ADR_STATUS_COLOR.get(row.status, "gray"),
                         variant="soft", size="1"),
                rx.badge(row.squad_key, color_scheme="teal", variant="soft", size="1"),
                *label_chips,
                align="center",
                gap=SPACING["sm"],
                wrap="wrap",
            ),
            width="100%",
        ),
        rx.text(row.summary, size="2", weight="medium", color=rx.color("gray", 12),
                line_height="1.4", margin_top="6px"),
        rx.flex(
            rx.text("Решение", size="1", weight="medium", color=rx.color("teal", 10),
                    style={"text_transform": "uppercase", "letter_spacing": "0.05em"},
                    flex_shrink="0", margin_top="2px", width="72px"),
            rx.text(row.decision, size="1", color=rx.color("gray", 11), line_height="1.55"),
            direction="row",
            gap=SPACING["sm"],
            align="start",
            margin_top=SPACING["sm"],
        ),
        direction="column",
        gap="0",
        padding=SPACING["lg"],
        width="100%",
        background="white",
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_left=f"4px solid {accent}",
        border_radius="var(--radius-3)",
        box_shadow="0 1px 2px rgba(0,0,0,0.04)",
    )


def _adr_register(rows) -> rx.Component:
    return rx.flex(
        *[_adr_card(r) for r in rows],
        direction="column",
        gap=SPACING["md"],
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
    _adr_rows = dash_adrs(load_issues(DASH_CONFIG))
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

        rx.box(height=SPACING["2xl"]),

        # ── Design tokens · code ↔ Figma bridge (DASH-129 ч.2) ──────────────
        section_header(
            "Дизайн-токены · мост код ↔ Figma",
            subtitle="Единый источник правды design_tokens.json (W3C DTCG) питает и код, и Figma · "
                     "round-trip честный: едут только токены, компоненты — руками",
        ),
        _token_chain_view(),

        rx.box(height=SPACING["2xl"]),

        # ── Goal → Epic → Issue entity schema (DASH-129 ч.3) ────────────────
        section_header(
            "Схема сущностей · Goal → Epic → Issue",
            subtitle="SA-артефакт: как связаны цели, эпики и задачи проекта · "
                     "ERD на живых данных DASH (не выдуманная модель)",
        ),
        _goal_epic_issue_view(),

        rx.box(height=SPACING["2xl"]),

        # ── Key ADR register (DASH-129 ч.4) ─────────────────────────────────
        section_header(
            "Ключевые архитектурные решения · ADR",
            subtitle=f"{len(_adr_rows)} решений из decision_note реальных DASH-задач "
                     f"(метка architecture / squad ARCHITECTURE) · решение записано на самой задаче, как в Jira",
        ),
        _adr_register(_adr_rows),

        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
