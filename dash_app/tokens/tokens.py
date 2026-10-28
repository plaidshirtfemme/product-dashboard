"""
Design tokens for the Knowledge Pipeline dashboard.

Single source of truth: design_tokens.json (DTCG — Design Tokens Community Group format).
This module reads the JSON at import time and exposes typed Python dicts
for use in Reflex components.

Figma sync: use Tokens Studio plugin with design_tokens.json.
Claude Design: "Create using Claude Code" reads components directly.
"""

import json
import reflex as rx
from pathlib import Path

# ---------------------------------------------------------------------------
# Load JSON
# ---------------------------------------------------------------------------

_TOKENS_FILE = Path(__file__).parent / "design_tokens.json"
_t: dict = json.loads(_TOKENS_FILE.read_text(encoding="utf-8"))


def _val(dot_path: str) -> str:
    """Return $value at a dot-separated path, e.g. 'spacing.md'."""
    node = _t
    for key in dot_path.split("."):
        node = node[key]
    return node["$value"]


# ---------------------------------------------------------------------------
# Core theme configuration (feeds rx.theme(), i.e. Radix Themes)
# ---------------------------------------------------------------------------

THEME_CONFIG: dict = {
    "appearance": "light",
    "accent_color": _val("theme.accent"),
    "gray_color":   _val("theme.gray"),
    "radius":       _val("theme.radius"),
    "scaling":      "100%",
    "has_background": True,
}

# ---------------------------------------------------------------------------
# Semantic status colors
# Values are Radix color names; shade picked per-usage via rx.color().
# ---------------------------------------------------------------------------

STATUS_COLORS: dict[str, str] = {
    k: _val(f"color.status.{k}")
    for k in ("success", "warning", "danger", "info", "neutral")
}

# Epic-type accent colors (Radix names). Single source for the type badge/chip
# across Roadmap Timeline and Backlog Epics view. Порядок/сам тип эпика —
# доменные данные, живут в data/jira_mock_raw.py (EPIC_TYPES); здесь только цвет.
EPIC_TYPE_COLORS: dict[str, str] = {
    "business":  "teal",
    "enabler":   "amber",
    "component": "gray",
}

# ---------------------------------------------------------------------------
# Semantic color roles (component-level) → Radix (scale, step).
# Encodes WHICH Radix step plays WHICH role, so code stops hardcoding steps and
# the role-map lives in tokens, not scattered comments. This is the semantic /
# component layer on top of the Radix Colors primitive scale.
# NB: текущая конвенция светлее канона Radix (текст шаг 9 против канона 11-12,
# бордер шаг 4 против 6-8). Сближение с каноном — DASH-142, решение за Guzel.
#
# 16.09.2026: вариант text-secondary = gray.11 был собран и показан — ОТКЛОНЁН,
# вернулись на gray.9. Заодно выяснилось, что мерить надо не тем: Radix даёт
# гарантию в APCA (Lc 60 для шага 11, Lc 90 для 12, на фоне ШАГА 2 своей шкалы),
# а не в WCAG 2. Замер APCA на живой теме (прибор сверен на эталонах W3C):
# slate-9 = Lc 56.91, slate-10 = Lc 61.90, slate-11 = Lc 76.21, slate-12 = Lc 99.84.
# Порог годности в APCA НЕ сверен с источником — без него числа решения не дают.
# Выбор метрики и порога — DASH-150, исполнитель Guzel.
# ---------------------------------------------------------------------------

_ROLE_NAMES = (
    "text-primary", "text-secondary", "text-muted",
    "border-default", "border-subtle", "bg-card", "bg-subtle",
)


def _role_pair(name: str) -> tuple[str, int]:
    scale, step = _val(f"color.role.{name}").split(".")
    return scale, int(step)


# name -> (radix_scale, step) — for showcase / introspection
COLOR_ROLE: dict[str, tuple[str, int]] = {n: _role_pair(n) for n in _ROLE_NAMES}

# name -> rx.color(...) Var — ready to drop straight into component props
ROLE: dict = {n: rx.color(s, st) for n, (s, st) in COLOR_ROLE.items()}

# ---------------------------------------------------------------------------
# Цвет сущности (DASH-151, 16.09.2026). Не статус и не роль в интерфейсе,
# а вид объекта Jira. Purple — осознанное исключение из темы (accent teal,
# gray slate): teal уже означает «ссылка/интерактив», и красить им сущность
# значит смешать два разных смысла. Обоснование целиком — в design_tokens.json,
# color.entity. НЕ ПУТАТЬ с EPIC_TYPE_COLORS: там тип эпика, здесь сущность.
# ---------------------------------------------------------------------------

_ENTITY_NAMES = ("epic",)


def _entity_pair(name: str) -> tuple[str, int]:
    scale, step = _val(f"color.entity.{name}").split(".")
    return scale, int(step)


COLOR_ENTITY: dict[str, tuple[str, int]] = {n: _entity_pair(n) for n in _ENTITY_NAMES}
ENTITY: dict = {n: rx.color(s, st) for n, (s, st) in COLOR_ENTITY.items()}

# ---------------------------------------------------------------------------
# Interaction states (hover / selected) → Radix (scale, step).
# Заведено 08.09.2026. До этого цвета состояний писались прямо в компонентах
# (rx.color("gray", 3) в navigation.py, rx.color("gray", 2) в таблицах) — то есть
# состояния в продукте были, а в системе токенов их не было. Это нарушало
# собственное правило проекта «никогда не хардкодить, только через токены».
# Значения сняты с фактического употребления, не назначены заново.
#
# Focus и disabled отсутствуют по РАЗНЫМ причинам — уточнено замером 09.09:
#   focus    — снять неоткуда: `_focus` / `:focus` / `focus_visible` дают
#              ноль вхождений по всем файлам вне .web. Но НЕ повод опустить
#              состояние: у Material focus — одно из пяти обязательных,
#              а Radix публикует шаг 7 как "UI element border and focus
#              rings", то есть источник значения документирован.
#              Заводить — решением по канону, с пометкой, что значение
#              принято, а не снято с употребления (см. DASH-152).
#              Отдельно и важнее: у 24 rx.select, 5 rx.button и 1 rx.link
#              фокус даёт Radix Themes и он работает; а свои кликабельные
#              (20 on_click, 7 мест с cursor="pointer") при НУЛЕ tab_index
#              и НУЛЕ role с клавиатуры недостижимы вообще — фокус туда
#              не встаёт. Это дефект доступности, и кольцо его не чинит.
#   disabled — состояние ЕСТЬ, значение снимается: navigation.py, непостроенная
#              вкладка = color gray.7 (против gray.10), cursor default,
#              _hover={}, on_click=None, тултип «В разработке».
#              Не заведено пока не решён DASH-152 — нужно ли продукту.
# ---------------------------------------------------------------------------

_STATE_NAMES = (
    "hover-bg", "hover-bg-subtle", "hover-text",
    "selected-bg", "selected-text",
)


def _state_pair(name: str) -> tuple[str, int]:
    scale, step = _val(f"color.state.{name}").split(".")
    return scale, int(step)


# name -> (radix_scale, step) — for showcase / introspection
COLOR_STATE: dict[str, tuple[str, int]] = {n: _state_pair(n) for n in _STATE_NAMES}

# name -> rx.color(...) Var — ready to drop straight into _hover / _active props
STATE: dict = {n: rx.color(s, st) for n, (s, st) in COLOR_STATE.items()}

# ---------------------------------------------------------------------------
# Spacing scale — use for gap, padding, margin.
# ---------------------------------------------------------------------------

SPACING: dict[str, str] = {
    k: _val(f"spacing.{k}")
    for k in ("2xs", "xs", "sm", "md", "lg", "xl", "2xl")
}

# ---------------------------------------------------------------------------
# Border helpers
# BORDER = "1px solid" — compose with rx.color():
#   border=f"{BORDER} {rx.color('gray', 4)}"
# ---------------------------------------------------------------------------

BORDER: str = f"{_val('border.width')} {_val('border.style')}"
BORDER_WIDTH: str = _val("border.width")

# ---------------------------------------------------------------------------
# Radius scale (px) — for contexts that don't inherit Radix Theme radius
# (e.g. inside rx.recharts). Prefer var(--radius-N) in regular components.
# ---------------------------------------------------------------------------

RADIUS: dict[str, str] = {
    k: _val(f"radius.{k}")
    for k in ("sm", "md", "lg", "full")
}

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

PAGE_MAX_WIDTH: str      = _val("layout.page-max-width")
PAGE_MAX_WIDTH_WIDE: str = _val("layout.page-max-width-wide")
SIDEBAR_WIDTH: str       = _val("layout.sidebar-width")

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONTS: dict[str, str] = {
    "sans": _val("typography.font-sans"),
    "mono": _val("typography.font-mono"),
}

# Три размера, и все три совпадают с шагами шкалы Radix (1, 6, 4).
# 09.09.2026 удалены два мёртвых токена: size-body (14px) и
# size-page-title (22px) — не потреблялись ни одним компонентом,
# жили только на странице документации. 22px к тому же лежал вне шкалы
# Radix, между шагами 5 (20px) и 6 (24px).
#
# ОСТАЮЩИЙСЯ ДОЛГ (DASH-154): три места потребляют эти значения через
# style={"font_size": ...}, минуя rx.text(size="N"). Из-за этого текст
# не получает парных line-height и letter-spacing, которые Radix отдаёт
# вместе с шагом. Переход на size="N" — визуальная правка, нужен глаз.
TYPE_SCALE: dict[str, str] = {
    "label":      _val("typography.size-label"),
    "value":      _val("typography.size-value"),
    "heading":    _val("typography.size-heading"),
}

# ---------------------------------------------------------------------------
# Chart palette — Reflex-specific (rx.color calls), stays in Python.
# Kept to 3 categorical colors + gray ("2-3 colors max" rule).
# ---------------------------------------------------------------------------

CHART_COLORS: list = [
    rx.color("teal", 8),
    rx.color("iris", 8),
    rx.color("amber", 8),
    rx.color("slate", 6),
]
