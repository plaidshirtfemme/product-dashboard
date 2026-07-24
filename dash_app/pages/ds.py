"""Design System tab — живая документация токенов и компонентов.

Читает значения напрямую из tokens/ и components/ —
любое изменение design_tokens.json автоматически отражается здесь.
"""

import reflex as rx
from ..tokens import (
    SPACING, STATUS_COLORS, COLOR_ROLE, TYPE_SCALE, FONTS,
    BORDER, BORDER_WIDTH, RADIUS,
    PAGE_MAX_WIDTH, PAGE_MAX_WIDTH_WIDE, SIDEBAR_WIDTH,
)
from ..components import section_header, stat_card, stat_card_row, progress_bar, color_legend
from ..components.empty_state import empty_state
from ..states.dash_ds_state import DsState

_PAD = f"0 {SPACING['xl']} {SPACING['xl']}"
_MAX = PAGE_MAX_WIDTH

# ---------------------------------------------------------------------------
# Color section
# ---------------------------------------------------------------------------

_COLOR_PALETTE = [
    ("teal",   9,  "Primary / accent, active tab, 'real' badge"),
    ("amber",  9,  "Warning, demo-only badge, IP-блоки"),
    ("tomato", 9,  "Danger, bad trend, security items"),
    ("blue",   9,  "Coming soon, info, neutral-positive"),
    ("gray",   12, "Primary text"),
    ("gray",   9,  "Secondary text, labels"),
    ("gray",   4,  "Borders, dividers"),
    ("gray",   1,  "Card backgrounds"),
]

_STATUS_USAGE = {
    "success": "Done / on-time / green light",
    "warning": "In-progress / at-risk / yellow light",
    "danger":  "Blocked / overdue / red light",
    "info":    "Neutral informational, matches accent",
    "neutral": "Backlog / not-started / no signal",
}


def _color_row(color: str, shade: int, usage: str) -> rx.Component:
    token_name = f"{color}-{shade}"
    return rx.flex(
        rx.box(
            width="32px", height="32px",
            border_radius="var(--radius-2)",
            background=rx.color(color, shade),
            border=f"{BORDER} {rx.color('gray', 4)}",
            flex_shrink="0",
        ),
        rx.text(token_name, size="2", weight="medium",
                color=rx.color("gray", 12),
                font_family="monospace", min_width="80px"),
        rx.text(usage, size="2", color=rx.color("gray", 9), flex="1"),
        gap=SPACING["md"],
        align="center",
        padding=f"{SPACING['xs']} 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


def _status_color_row(key: str, radix_name: str, usage: str) -> rx.Component:
    return rx.flex(
        rx.box(
            width="32px", height="32px",
            border_radius="var(--radius-2)",
            background=rx.color(radix_name, 9),
            flex_shrink="0",
        ),
        rx.flex(
            rx.text(f"STATUS_COLORS['{key}']", size="1",
                    color=rx.color("gray", 9), font_family="monospace"),
            rx.text(radix_name, size="2", weight="medium",
                    color=rx.color("gray", 12)),
            direction="column", gap="0",
        ),
        rx.text(usage, size="2", color=rx.color("gray", 9), flex="1"),
        gap=SPACING["md"],
        align="center",
        padding=f"{SPACING['xs']} 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


# ---------------------------------------------------------------------------
# Semantic role section (component-level color tokens → Radix step)
# ---------------------------------------------------------------------------

_ROLE_USAGE = {
    "text-primary":   "Заголовки, значения, ключевые подписи",
    "text-secondary": "Вторичный текст, подписи таблиц",
    "text-muted":     "Приглушённый — ID / таймстемпы (моно)",
    "border-default": "Рамка карточки / разделитель",
    "border-subtle":  "Тонкий внутренний разделитель (строки)",
    "bg-card":        "Фон карточки / панели",
    "bg-subtle":      "Фон превью / вставки",
}


def _role_row(name: str, scale: str, step: int) -> rx.Component:
    return rx.flex(
        rx.box(
            width="32px", height="32px",
            border_radius="var(--radius-2)",
            background=rx.color(scale, step),
            border=f"{BORDER} {rx.color('gray', 4)}",
            flex_shrink="0",
        ),
        rx.flex(
            rx.text(name, size="2", weight="medium", color=rx.color("gray", 12),
                    font_family="monospace"),
            rx.text(f"{scale}-{step}", size="1", color=rx.color("gray", 9),
                    font_family="monospace"),
            direction="column", gap="0", min_width="150px",
        ),
        rx.text(_ROLE_USAGE.get(name, ""), size="2", color=rx.color("gray", 9), flex="1"),
        gap=SPACING["md"],
        align="center",
        padding=f"{SPACING['xs']} 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


# ---------------------------------------------------------------------------
# Spacing section
# ---------------------------------------------------------------------------

def _spacing_row(key: str, value: str) -> rx.Component:
    # Convert rem to approximate px for the bar (1rem ≈ 16px)
    try:
        if "rem" in value:
            px = float(value.replace("rem", "")) * 16
        else:
            px = float(value.replace("px", ""))
        max_px = 3 * 16  # 2xl = 3rem = 48px → 100%
        pct = min(round(px / max_px * 100), 100)
    except ValueError:
        pct = 10

    return rx.flex(
        rx.text(f"SPACING['{key}']", size="1", font_family="monospace",
                color=rx.color("gray", 9), min_width="120px", flex_shrink="0"),
        rx.text(value, size="2", weight="medium",
                color=rx.color("gray", 12), min_width="50px", flex_shrink="0"),
        progress_bar(pct=pct, color="teal", shade=5, height="12px"),
        gap=SPACING["md"],
        align="center",
        padding=f"{SPACING['xs']} 0",
    )


# ---------------------------------------------------------------------------
# Typography section
# ---------------------------------------------------------------------------

_TYPE_SAMPLES = [
    ("label",      "Метка / заголовок таблицы",  "medium", "gray", 9),
    ("body",       "Основной текст интерфейса",   "regular", "gray", 12),
    ("value",      "Большое число в карточке",    "bold",   "gray", 12),
    ("heading",    "Заголовок секции",             "medium", "gray", 12),
    ("page_title", "Заголовок страницы",           "bold",   "gray", 12),
]


def _type_row(key: str, sample: str, weight: str, color: str, shade: int) -> rx.Component:
    return rx.flex(
        rx.text(f"TYPE_SCALE['{key}']", size="1", font_family="monospace",
                color=rx.color("gray", 8), min_width="160px", flex_shrink="0"),
        rx.text(TYPE_SCALE[key], size="1", font_family="monospace",
                color=rx.color("gray", 9), min_width="40px", flex_shrink="0"),
        rx.text(
            sample,
            style={
                "font_size": TYPE_SCALE[key],
                "font_weight": "600" if weight == "bold" else ("500" if weight == "medium" else "400"),
                "color": f"var(--{color}-{shade})",
            },
            flex="1",
        ),
        gap=SPACING["md"],
        align="center",
        padding=f"{SPACING['xs']} 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


# ---------------------------------------------------------------------------
# Layout & border section
# ---------------------------------------------------------------------------

def _const_row(name: str, value: str, note: str) -> rx.Component:
    return rx.flex(
        rx.text(name, size="2", weight="medium",
                font_family="monospace", color=rx.color("gray", 12),
                min_width="200px", flex_shrink="0"),
        rx.text(value, size="2", font_family="monospace",
                color=rx.color("teal", 9), min_width="120px", flex_shrink="0"),
        rx.text(note, size="2", color=rx.color("gray", 9), flex="1"),
        gap=SPACING["md"],
        align="center",
        padding=f"{SPACING['xs']} 0",
        border_bottom=f"{BORDER} {rx.color('gray', 3)}",
    )


# ---------------------------------------------------------------------------
# Components preview section
# ---------------------------------------------------------------------------

def _component_card(name: str, description: str, preview: rx.Component) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.text(name, size="2", weight="medium", color=rx.color("gray", 12),
                    font_family="monospace"),
            rx.text(description, size="1", color=rx.color("gray", 9)),
            direction="column", gap=SPACING["xs"],
            margin_bottom=SPACING["md"],
        ),
        rx.box(
            preview,
            padding=SPACING["md"],
            background=rx.color("gray", 2),
            border_radius="var(--radius-2)",
            border=f"{BORDER} {rx.color('gray', 3)}",
        ),
        padding=SPACING["lg"],
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        background=rx.color("gray", 1),
    )


# ---------------------------------------------------------------------------
# Sub-view 1 — Токены и компоненты (живая справка)
# ---------------------------------------------------------------------------

def _tokens_view() -> rx.Component:
    return rx.box(

        # ── 1. Цвета ──────────────────────────────────────────────────────
        section_header("Цвета · Color Tokens", "palette"),
        rx.box(
            rx.text("STATUS_COLORS — семантические токены",
                    size="1", weight="medium", color=rx.color("gray", 9),
                    text_transform="uppercase", letter_spacing="0.06em",
                    margin_bottom=SPACING["sm"]),
            *[
                _status_color_row(k, STATUS_COLORS[k], _STATUS_USAGE[k])
                for k in STATUS_COLORS
            ],
            rx.box(height=SPACING["md"]),
            rx.text("Radix color scale — прямое использование",
                    size="1", weight="medium", color=rx.color("gray", 9),
                    text_transform="uppercase", letter_spacing="0.06em",
                    margin_bottom=SPACING["sm"]),
            *[_color_row(c, s, u) for c, s, u in _COLOR_PALETTE],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # ── 1b. Семантические роли (Radix-шаги закодированы в токенах) ─────
        section_header("Семантические роли · component tokens", "layers"),
        rx.box(
            rx.text("COLOR_ROLE — какой Radix-шаг какую роль играет (карта в токенах, не в комментариях)",
                    size="1", weight="medium", color=rx.color("gray", 9),
                    text_transform="uppercase", letter_spacing="0.06em",
                    margin_bottom=SPACING["sm"]),
            *[_role_row(name, scale, step) for name, (scale, step) in COLOR_ROLE.items()],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # ── 2. Отступы ────────────────────────────────────────────────────
        section_header("Отступы · SPACING", "ruler"),
        rx.box(
            *[_spacing_row(k, SPACING[k]) for k in SPACING],
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # ── 3. Типографика ────────────────────────────────────────────────
        section_header("Типографика · TYPE_SCALE", "type"),
        rx.box(
            *[_type_row(k, s, w, c, sh) for k, s, w, c, sh in _TYPE_SAMPLES],
            rx.box(height=SPACING["sm"]),
            rx.flex(
                rx.text("FONTS['sans']", size="1", font_family="monospace",
                        color=rx.color("gray", 9), min_width="160px"),
                rx.text(FONTS["sans"], size="1", color=rx.color("gray", 11), flex="1"),
                gap=SPACING["md"],
                padding=f"{SPACING['xs']} 0",
            ),
            rx.flex(
                rx.text("FONTS['mono']", size="1", font_family="monospace",
                        color=rx.color("gray", 9), min_width="160px"),
                rx.text(FONTS["mono"], size="1",
                        style={"font_family": FONTS["mono"]},
                        color=rx.color("gray", 11), flex="1"),
                gap=SPACING["md"],
                padding=f"{SPACING['xs']} 0",
            ),
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # ── 4. Layout & Border ────────────────────────────────────────────
        section_header("Layout & Border", "layout-template"),
        rx.box(
            _const_row("PAGE_MAX_WIDTH",      PAGE_MAX_WIDTH,       "Стандартная ширина контента"),
            _const_row("PAGE_MAX_WIDTH_WIDE", PAGE_MAX_WIDTH_WIDE,  "Широкие таблицы (backlog, kanban)"),
            _const_row("SIDEBAR_WIDTH",       SIDEBAR_WIDTH,        "Ширина боковой навигации"),
            _const_row("BORDER",              BORDER,               "Стандартная рамка — добавь + rx.color(...)"),
            _const_row("BORDER_WIDTH",        BORDER_WIDTH,         "Только толщина"),
            padding=f"{SPACING['sm']} {SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # ── 5. Компоненты ─────────────────────────────────────────────────
        section_header("Компоненты · components/", "package"),
        rx.grid(
            _component_card(
                "stat_card",
                "Карточка с метрикой",
                stat_card_row(
                    stat_card("Заметок", "304", trend="+96%", trend_direction="good", icon="file-text"),
                    stat_card("IP-блоков", "96", icon="shield-off"),
                ),
            ),
            _component_card(
                "progress_bar",
                "Горизонтальный бар с pct%",
                rx.flex(
                    progress_bar(pct=72, color="teal"),
                    progress_bar(pct=30, color="amber"),
                    progress_bar(pct=10, color="tomato"),
                    direction="column",
                    gap=SPACING["sm"],
                ),
            ),
            _component_card(
                "color_legend",
                "Цветные точки + метки",
                color_legend([
                    ("teal",   "Real data"),
                    ("amber",  "Mock data"),
                    ("tomato", "Gap / Error"),
                    ("blue",   "Coming soon"),
                ]),
            ),
            _component_card(
                "empty_state",
                "Честная заглушка с объяснением",
                empty_state(
                    "Нет данных",
                    "Этот блок смоделирован — реальных данных нет.",
                    icon="inbox",
                    mode="demo_only",
                ),
            ),
            columns="2",
            gap=SPACING["lg"],
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # ── 6. Источник ───────────────────────────────────────────────────
        section_header("Источник · design_tokens.json", "file-json"),
        rx.callout(
            "Все токены хранятся в tokens/design_tokens.json (W3C Design Tokens format). "
            "tokens/tokens.py читает JSON при импорте — меняешь JSON, изменение применяется везде. "
            "Для синка с Figma: плагин Tokens Studio → укажи путь к design_tokens.json.",
            icon="info",
            color_scheme="teal",
            variant="soft",
            size="1",
            margin_top=SPACING["sm"],
        ),

        padding=_PAD,
        max_width=_MAX,
        margin="0 auto",
    )


# ---------------------------------------------------------------------------
# Sub-view 2 — DS rules (стандарты работы с дизайн-системой, research фазы 1)
# ---------------------------------------------------------------------------

def _bullet(text: str) -> rx.Component:
    return rx.flex(
        rx.text("•", size="2", color=rx.color("teal", 9),
                flex_shrink="0", line_height="1.5"),
        rx.text(text, size="2", color=rx.color("gray", 11), line_height="1.5"),
        gap=SPACING["sm"],
        align="start",
    )


def _rule_card(title: str, icon: str, color: str, items: list[str]) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.icon(icon, size=16, color=rx.color(color, 9), flex_shrink="0"),
            rx.text(title, size="2", weight="bold", color=rx.color("gray", 12)),
            align="center",
            gap=SPACING["sm"],
            margin_bottom=SPACING["md"],
        ),
        rx.flex(
            *[_bullet(i) for i in items],
            direction="column",
            gap=SPACING["xs"],
        ),
        padding=SPACING["lg"],
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        background=rx.color("gray", 1),
        flex="1",
        min_width="280px",
    )


def _quote(text: str, source: str) -> rx.Component:
    return rx.flex(
        rx.box(width="3px", flex_shrink="0",
               background=rx.color("teal", 6), border_radius="2px"),
        rx.flex(
            rx.text(f"«{text}»", size="1", color=rx.color("gray", 11),
                    line_height="1.5", style={"font_style": "italic"}),
            rx.text(f"— {source}", size="1", weight="medium",
                    color=rx.color("gray", 9)),
            direction="column",
            gap="2px",
        ),
        gap=SPACING["sm"],
        align="stretch",
    )


def _rules_view() -> rx.Component:
    return rx.box(

        rx.callout(
            "Стандарты работы с дизайн-системой — конспект research фазы 1 (подготовка к тесту "
            "HTML → Figma). Источники: Figma Learn, Figma best-practices, LogRocket, atomic design "
            "(Brad Frost). Конкретику Бычкова / Ефремова веб-поиск не отдаёт — сверять у них напрямую.",
            icon="info", color_scheme="teal", variant="soft", size="1",
            margin_bottom=SPACING["xl"],
        ),

        # ── 1. Мастер-компонент vs variant set ────────────────────────────
        section_header(
            "Мастер-компонент vs variant set",
            subtitle="Когда достаточно набора вариантов, а когда нужен отдельный мастер",
        ),
        rx.callout(
            "Решение — не «мастер или варианты», а выбор из 5 инструментов: отдельный мастер · "
            "variant set · boolean · instance swap · text. Variants и properties — слои одного "
            "решения, не конкуренты.",
            icon="lightbulb", color_scheme="gray", variant="surface", size="1",
            margin_bottom=SPACING["md"],
        ),
        rx.flex(
            _rule_card("Variant set — когда все условия", "layers", "teal", [
                "Одно назначение / роль — «одна и та же вещь в разных обличьях»",
                "Общая анатомия — сопоставимый скелет слоёв (иначе переключение ломается)",
                "Взаимоисключающие состояния вдоль именованной оси (Type, Size, State)",
                "Пользователь переключается «на месте», не пересобирая макет",
            ]),
            _rule_card("Отдельный мастер — когда", "lock", "amber", [
                "Разное назначение / семантика (navbar vs footer, button vs input)",
                "Несводимая анатомия (нужны пустые слои-заглушки → это два мастера)",
                "У подтипов разные оси состояний (набор начинает «протекать»)",
            ]),
            direction="row", wrap="wrap", gap=SPACING["lg"],
        ),
        rx.box(height=SPACING["md"]),
        rx.callout(
            "Оси должны быть ортогональны: раздельные свойства Type + Size, а не одно свойство "
            "Style со значениями «Primary-Large» — так работает mix-and-match (Figma Learn).",
            icon="info", color_scheme="teal", variant="soft", size="1",
        ),

        rx.box(height=SPACING["2xl"]),

        # ── 2. Base-компонент vs плоский variant set ──────────────────────
        section_header(
            "Base-компонент vs плоский variant set",
            subtitle="Почему иногда сначала делают отдельный компонент, а потом из него variant set",
        ),
        rx.callout(
            "«Variant set без мастера» не существует: component set — контейнер, который может "
            "содержать только компоненты, поэтому каждый вариант внутри сета сам по себе "
            "main-компонент. Реальная развилка — две архитектуры одной и той же вещи.",
            icon="info", color_scheme="amber", variant="soft", size="1",
            margin_bottom=SPACING["md"],
        ),
        rx.flex(
            _rule_card("Плоский variant set", "layers", "gray", [
                "Варианты строишь напрямую; общая анатомия продублирована в каждом варианте",
                "Figma синхронит через multi-edit по совпадающим именам слоёв",
                "Дефолт, пока анатомия тривиальна, а различия — только состояния / косметика",
            ]),
            _rule_card("Base-компонент → потом variant set", "lock", "teal", [
                "Сначала отдельный base с общей анатомией → его инстанс вложен в каждый вариант",
                "Variant set несёт только различия; base = единый источник правды по структуре",
                "Это и есть «сначала мастер, из него variant set»",
            ]),
            direction="row", wrap="wrap", gap=SPACING["lg"],
        ),
        rx.box(height=SPACING["md"]),
        rx.text("Когда выносить base-компонент — триггеры из источников:",
                size="2", weight="medium", color=rx.color("gray", 12),
                margin_bottom=SPACING["sm"]),
        rx.flex(
            _quote(
                "changing the button shape, I can simply go back and edit the original component "
                "and the change affects all of the components which are based off of it",
                "Figma best-practices · Component architecture",
            ),
            _quote(
                "when you want to change the hierarchy or add new elements to all variants… "
                "you'll quickly find yourself duplicating efforts across every variant",
                "LogRocket · Nesting Figma components",
            ),
            _quote(
                "separate that property into its own variant and then nest it back… "
                "reduce complexity significantly",
                "LogRocket · Nesting Figma components",
            ),
            direction="column",
            gap=SPACING["md"],
            padding=SPACING["md"],
            background=rx.color("gray", 1),
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
        ),
        rx.box(height=SPACING["md"]),
        rx.callout(
            "Решение: плоско, пока анатомия тривиальна; как только скелет сложный и обязан быть "
            "идентичен во всех вариантах / вариантов много и предвидятся глобальные правки "
            "структуры / ось раздувает матрицу → base-компонент, вложенный в варианты. Это НЕ "
            "«другое назначение» — base для той же вещи, ради источника правды по анатомии.",
            icon="circle-check", color_scheme="teal", variant="soft", size="1",
        ),

        rx.box(height=SPACING["2xl"]),

        # ── 3. Что делать компонентом, а что нет ──────────────────────────
        section_header(
            "Что делать компонентом, а что нет",
            subtitle="Критерии, чтобы не переусложнять — «переиспользуемое» ≠ «компонент»",
        ),
        rx.flex(
            _rule_card("Делать компонентом", "circle-check", "teal", [
                "Переиспользуется 3+ (правило трёх) или заведомо будет",
                "Нужен single source of truth — изменил раз, применилось везде",
                "Несёт именованную семантику (Button, Card, Toast)",
                "Инкапсулирует состояния и отступы, дорогие для ручной пересборки",
            ]),
            _rule_card("НЕ делать — сигналы переусложнения", "circle-x", "tomato", [
                "One-off, нет горизонта переиспользования (YAGNI)",
                "Это на самом деле токен / стиль: цвет → variable, шрифт → text style, тень → effect style",
                "Это просто расстановка → auto-layout, не компонент",
                "Паттерн ещё не стабилизировался — рано абстрагировать",
                "Обёртка над одним примитивом без добавленного смысла",
            ]),
            direction="row", wrap="wrap", gap=SPACING["lg"],
        ),
        rx.box(height=SPACING["md"]),
        rx.callout(
            "Atomic design (Brad Frost) — ментальная модель, не догма: правильно применённый даёт "
            "меньше компонентов, а не больше. Воронка кандидата: токен / стиль? → только расстановка "
            "(auto-layout)? → 3+ или single source of truth? → что осью варианта, а что property? → "
            "паттерн стабилен?",
            icon="lightbulb", color_scheme="gray", variant="surface", size="1",
        ),

        rx.box(height=SPACING["2xl"]),

        # ── 4. Карантин при импорте (staging) ─────────────────────────────
        section_header(
            "Карантин при импорте (staging)",
            subtitle="Сырой вход не касается канона DS, пока не отревизован и не нормализован",
        ),
        rx.flex(
            _rule_card("Разделение по локации", "lock", "amber", [
                "Подписанное — отдельно от WIP (иначе «wrong asset in production»)",
                "Отдельная страница под file-specific элементы (не в глобальную DS)",
                "Отдельная team под DS — чтобы unvetted-компоненты не загрязняли канон",
                "Нумерация страниц (00 Foundations → 10 Core → 99 Docs); Playground read-only; устаревшее → Archive",
            ]),
            _rule_card("Ветвление (Figma Branching)", "layers", "teal", [
                "Ветка = изолированная среда: правишь библиотеку, не трогая оригинал",
                "Всё активное — в ветке, независимо от размера правки",
                "Merge в main только после peer-review (как код-PR)",
            ]),
            _rule_card("На тесте: сырой HTML-макет", "lightbulb", "gray", [
                "Вход → отдельная staging-страница («🚧 Import / Incoming / Sandbox»)",
                "Там нормализуешь под токены и существующие компоненты",
                "В канон — только после ревизии; иначе чужие радиусы / цвета ломают консистентность",
            ]),
            direction="row", wrap="wrap", gap=SPACING["lg"], margin_top=SPACING["sm"],
        ),
        rx.box(height=SPACING["md"]),
        rx.flex(
            _quote(
                "keep everything that has been signed off and shipped in a separate location from "
                "work in progress files — you don't want to use the wrong asset in production!",
                "Figma best-practices · Team & file organization",
            ),
            _quote(
                "Branches are controlled environments that allow you to explore changes to designs, "
                "prototypes, and libraries, without editing the original file",
                "Figma · Best practices for branching",
            ),
            direction="column",
            gap=SPACING["md"],
            padding=SPACING["md"],
            background=rx.color("gray", 1),
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
        ),

        rx.box(height=SPACING["2xl"]),

        # ── 5. Документация DS: дизайнеры vs фронтендеры ───────────────────
        section_header(
            "Документация DS: дизайнеры vs фронтендеры",
            subtitle="Разные инструменты, один принцип — single source of truth, не дрейфовать",
        ),
        rx.flex(
            _rule_card("Дизайнеры", "pen-tool", "teal", [
                "Внутри Figma: cover, Getting Started, component descriptions, do/don't",
                "Doc-платформы: zeroheight (синкается с Figma) vs Notion (гибко, но дрейфует)",
                "Страница компонента: анатомия · варианты / состояния · do/don't с РЕАЛЬНЫМИ скринами",
            ]),
            _rule_card("Фронтендеры", "hammer", "teal", [
                "Storybook — стандарт (Polaris, Carbon, Lightning)",
                "MDX + Doc Blocks: авто prop-таблицы из TypeScript / PropTypes",
                "Доки живут в коде → не дрейфуют; Code Connect = мост Figma ↔ код",
            ]),
            direction="row", wrap="wrap", gap=SPACING["lg"], margin_top=SPACING["sm"],
        ),
        rx.box(height=SPACING["md"]),
        rx.flex(
            _quote(
                "Stories are executable, testable, and remain in sync with production code",
                "Storybook · docs",
            ),
            _quote(
                "dead links and deprecated guidelines erode trust faster than incomplete documentation",
                "zeroheight · documentation best practices",
            ),
            direction="column",
            gap=SPACING["md"],
            padding=SPACING["md"],
            background=rx.color("gray", 1),
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
        ),
        rx.box(height=SPACING["md"]),
        rx.callout(
            "Мост миров: токены = единый источник (design_tokens.json W3C ✅) · дизайн-доки = «когда / "
            "зачем», код-доки = «как» (API, props), связывать не дублировать · наш Reflex (Python) → "
            "Storybook / Code Connect неприменимы, аналог wiki = design_system_canon.md + эта вкладка.",
            icon="info", color_scheme="teal", variant="soft", size="1",
        ),

        rx.box(height=SPACING["2xl"]),

        # ── Источники ─────────────────────────────────────────────────────
        section_header("Источники", subtitle="На чём основан конспект"),
        _rule_card("Ссылки", "list", "gray", [
            "Figma Learn — Create and use variants, component sets (help.figma.com)",
            "Figma best-practices — Component architecture, Team & file organization, Branching",
            "LogRocket — Nesting Figma components; component properties (blog.logrocket.com)",
            "Brad Frost — Atomic Design, методология (atomicdesign.bradfrost.com)",
            "zeroheight — documentation best practices; Storybook — docs / MDX",
            "Бычков (alexeybychkov.study, t.me/a1exeybychkov) и Ефремов (t.me/dushnyj_design) — "
            "сверять напрямую: веб-поиск их конкретику не индексирует",
        ]),

        padding=_PAD,
        max_width=_MAX,
        margin="0 auto",
    )


# ---------------------------------------------------------------------------
# Section switcher (segmented control) + main tab
# ---------------------------------------------------------------------------

_SECTIONS = [
    ("tokens", "Токены и компоненты",
     "Живая справка: цвета, отступы, типографика, компоненты"),
    ("rules", "DS rules",
     "Стандарты: мастер vs variant set, что делать компонентом"),
]


def _section_button(section: str, label: str, sub: str) -> rx.Component:
    is_active = DsState.section == section
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
        min_width="240px",
        background=rx.cond(is_active, rx.color("teal", 3), rx.color("gray", 2)),
        border=rx.cond(
            is_active,
            f"{BORDER} {rx.color('teal', 7)}",
            f"{BORDER} {rx.color('gray', 4)}",
        ),
        _hover={"background": rx.cond(is_active, rx.color("teal", 3), rx.color("gray", 3))},
        on_click=DsState.set_section(section),
    )


def _section_switcher() -> rx.Component:
    return rx.box(
        rx.flex(
            *[_section_button(s, l, sub) for s, l, sub in _SECTIONS],
            direction="row",
            wrap="wrap",
            gap=SPACING["sm"],
            width="100%",
        ),
        padding=f"{SPACING['md']} {SPACING['xl']} 0",
        max_width=_MAX,
        margin="0 auto",
    )


def ds_tab() -> rx.Component:
    return rx.box(
        _section_switcher(),
        rx.box(height=SPACING["lg"]),
        rx.match(
            DsState.section,
            ("tokens", _tokens_view()),
            ("rules", _rules_view()),
            _tokens_view(),
        ),
    )
