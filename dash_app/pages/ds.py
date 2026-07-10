"""Design System tab — живая документация токенов и компонентов.

Читает значения напрямую из tokens/ и components/ —
любое изменение design_tokens.json автоматически отражается здесь.
"""

import reflex as rx
from ..tokens import (
    SPACING, STATUS_COLORS, TYPE_SCALE, FONTS,
    BORDER, BORDER_WIDTH, RADIUS,
    PAGE_MAX_WIDTH, PAGE_MAX_WIDTH_WIDE, SIDEBAR_WIDTH,
)
from ..components import section_header, stat_card, stat_card_row, progress_bar, color_legend
from ..components.empty_state import empty_state

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
# Main tab
# ---------------------------------------------------------------------------

def ds_tab() -> rx.Component:
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
