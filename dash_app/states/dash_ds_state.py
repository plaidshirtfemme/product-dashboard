"""
Reactive state for the Design System tab's inner sections.

The Design System tab has two sub-views switched by a segmented control:
"tokens" (живая справка по токенам/компонентам) and "rules" (стандарты работы
с DS — мастер vs variant set, что делать компонентом). Like DashArchState,
this is intentionally tiny — one var + setter.
"""

from __future__ import annotations

import reflex as rx


class DsState(rx.State):
    """Active sub-section of the Design System tab."""

    # "tokens" | "rules"
    section: str = "tokens"

    def set_section(self, section: str):
        self.section = section
