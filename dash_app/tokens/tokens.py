"""
Design tokens for the Knowledge Pipeline dashboard.

Single source of truth: design_tokens.json (W3C Design Tokens format).
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

TYPE_SCALE: dict[str, str] = {
    "label":      _val("typography.size-label"),
    "body":       _val("typography.size-body"),
    "value":      _val("typography.size-value"),
    "heading":    _val("typography.size-heading"),
    "page_title": _val("typography.size-page-title"),
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
