import os

import reflex as rx

NAV_TABS: list[tuple[str, str, str]] = [
    ("about",         "About project",             "info"),
    ("info",          "Practices & Rules",         "book-open"),
    ("kanban",        "Kanban",                    "kanban"),
    ("backlog",       "Backlog",                   "table-2"),
    ("roadmap",       "Roadmap",                   "map"),
    ("overview",      "Overview / PM",             "layout-dashboard"),
    ("research",      "Research",                  "microscope"),
    ("analytics",     "Analytics · PA",            "bar-chart-2"),
    ("architecture",  "Architecture",              "git-branch"),
    ("analysis",      "Requirements · BA/SA",       "file-text"),
    ("design",        "Design",                    "pen-tool"),
    ("ds",            "Design System",             "palette"),
    ("discover",      "Discover",                  "search"),
    ("define",        "Define",                    "target"),
    ("develop",       "Develop",                   "hammer"),
    ("deliver",       "Deliver",                   "rocket"),
    ("dev",           "Dev & Pipeline",            "file-code-2"),
    ("quality",       "Quality",                   "shield-check"),
    ("release",       "Instructions & Release",    "package"),
    ("monitoring",    "Monitoring & Support",      "activity"),
    ("growth",        "Growth",                    "trending-up"),
]

BUILT_TABS = {"about", "roadmap", "overview", "backlog", "kanban", "research", "analytics", "analysis", "design", "growth", "architecture", "dev", "quality", "release", "monitoring", "ds", "info", "discover", "define", "develop", "deliver"}


# ── Project visibility (DASH-162) ──────────────────────────────────────────
# Публичность задаётся на уровне ПРОЕКТА (project_mode), а не отдельного файла.
#   "public" → уезжает на публичный сайт (Reflex Cloud)
#   "local"  → доступен только при локальном `reflex run`
# Knowledge Pipeline ("kp") закрыт от публики: его данные не уезжают в архив
# (scripts/deploy.py), а вкладки не собираются в публичный фронтенд.
PROJECT_VISIBILITY: dict[str, str] = {
    "motif": "public",   # Motif — вымышленная демо-команда
    "kp": "local",    # Knowledge Pipeline — только локально
    "dash": "public",   # Product Dashboard — этот дашборд
}


def is_public(mode: str) -> bool:
    """Относится ли режим проекта к публичной витрине."""
    return PROJECT_VISIBILITY.get(mode, "public") == "public"


# Публичная сборка полностью исключает local-проекты. scripts/deploy.py ставит
# PUBLIC_BUILD=1 на время компиляции при деплое; локальный `reflex run` его не
# выставляет — поэтому локально видны все проекты.
PUBLIC_BUILD: bool = os.environ.get("PUBLIC_BUILD") == "1"


def show_mode(mode: str) -> bool:
    """Доступен ли режим проекта в текущей сборке.

    Локальная сборка → все режимы. Публичная → только публичные.
    """
    return is_public(mode) or not PUBLIC_BUILD


class NavState(rx.State):
    active_tab: str = "kanban"
    design_open: bool = False
    analysis_open: bool = False

    def set_tab(self, tab: str):
        if tab in BUILT_TABS:
            self.active_tab = tab
            if tab == "ds":
                self.design_open = True

    def toggle_design(self):
        self.design_open = not self.design_open
        self.active_tab = "design"

    def toggle_analysis(self):
        self.analysis_open = not self.analysis_open
        self.active_tab = "analysis"


class ProjectState(rx.State):
    """Global project mode: motif (Motif) | kp (KP) | dash (this dashboard)."""
    project_mode: str = "motif"   # "motif" | "kp" | "dash"

    def set_kp(self):
        self.project_mode = "kp"

    def set_motif(self):
        self.project_mode = "motif"

    def set_dash(self):
        self.project_mode = "dash"
