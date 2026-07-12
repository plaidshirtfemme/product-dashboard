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
    ("dev",           "Dev & Pipeline",            "file-code-2"),
    ("quality",       "Quality",                   "shield-check"),
    ("release",       "Instructions & Release",    "package"),
    ("monitoring",    "Monitoring & Support",      "activity"),
    ("growth",        "Growth",                    "trending-up"),
]

BUILT_TABS = {"about", "roadmap", "overview", "backlog", "kanban", "research", "analytics", "analysis", "design", "growth", "architecture", "dev", "quality", "release", "monitoring", "ds", "info"}


class NavState(rx.State):
    active_tab: str = "kanban"
    design_open: bool = False

    def set_tab(self, tab: str):
        if tab in BUILT_TABS:
            self.active_tab = tab
            if tab == "ds":
                self.design_open = True

    def toggle_design(self):
        self.design_open = not self.design_open
        self.active_tab = "design"


class ProjectState(rx.State):
    """Global project mode: demo (Motif) | real (KP) | dash (this dashboard)."""
    project_mode: str = "demo"   # "demo" | "real" | "dash"

    def set_real(self):
        self.project_mode = "real"

    def set_demo(self):
        self.project_mode = "demo"

    def set_dash(self):
        self.project_mode = "dash"
