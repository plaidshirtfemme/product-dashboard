"""
Reactive state for the C4 architecture view (dash-mode Architecture tab).

Holds only the active C4 zoom level (Context → Container → Component).
The diagram content itself is static (declared in pages/dash_architecture.py),
so this state is intentionally tiny — one var + setter, like a segmented control.
"""

from __future__ import annotations

import reflex as rx


class DashArchState(rx.State):
    """Active C4 zoom level for the self-hosted architecture diagram."""

    # "context" | "container" | "component"
    c4_level: str = "context"

    def set_level(self, level: str):
        self.c4_level = level
