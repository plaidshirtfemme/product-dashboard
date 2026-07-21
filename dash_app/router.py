"""Tab router — maps NavState.active_tab → the right component.

Each entry in _TAB_ENTRIES is (tab_id, component). The list is processed
into a nested rx.cond chain at import time — same runtime structure as
before, but readable as a flat list instead of 16-level nesting.
"""

import reflex as rx
from .states import NavState, ProjectState
from .components.empty_state import empty_state
from .pages.about import about_tab
from .pages.motif_about import motif_about_tab
from .pages.overview import overview_tab
from .pages.backlog import backlog_tab
from .pages.kanban import kanban_tab, dash_kanban_tab
from .pages.research import research_tab
from .pages.analytics import analytics_tab
from .pages.analysis import analysis_tab
from .pages.design import design_tab
from .pages.growth import growth_tab
from .pages.architecture import architecture_tab
from .pages.dev import dev_tab
from .pages.quality import quality_tab
from .pages.release import release_tab
from .pages.monitoring import monitoring_tab
from .pages.info import info_tab
from .pages.ds import ds_tab
from .pages.real_overview import real_overview_tab
from .pages.real_architecture import real_architecture_tab
from .pages.real_dev import real_dev_tab
from .pages.real_quality import real_quality_tab
from .pages.real_release import real_release_tab
from .pages.real_monitoring import real_monitoring_tab
from .pages.real_research import real_research_tab
from .pages.real_design import real_design_tab
from .pages.roadmap import roadmap_tab
from .pages.dash_discover import dash_discover_tab
from .pages.dash_define import dash_define_tab
from .pages.dash_develop import dash_develop_tab
from .pages.dash_deliver import dash_deliver_tab

_WIP = rx.box(
    rx.text("В разработке", color=rx.color("gray", 9), size="3"),
    padding="4rem",
    text_align="center",
)


def _by_project(
    motif: rx.Component,
    kp: rx.Component,
    dash: rx.Component | None = None,
) -> rx.Component:
    dash_component = dash if dash is not None else _coming_soon(
        "Product Dashboard",
        "Данные по этому проекту появятся в следующей итерации.",
        "layout-dashboard",
    )
    return rx.cond(
        ProjectState.project_mode == "demo",
        motif,
        rx.cond(ProjectState.project_mode == "real", kp, dash_component),
    )


def _demo_only(title: str, reason: str, icon: str) -> rx.Component:
    return empty_state(title, reason, icon=icon, mode="demo_only")


def _coming_soon(title: str, reason: str, icon: str) -> rx.Component:
    return empty_state(title, reason, icon=icon, mode="coming_soon")


def _build_page_content() -> rx.Component:
    """Build a nested rx.cond chain from a flat list of (tab_id, component) entries."""
    entries: list[tuple[str, rx.Component]] = [
        ("about", _by_project(
            motif=motif_about_tab(),
            kp=about_tab(),
            dash=about_tab(),
        )),
        ("kanban", _by_project(
            motif=kanban_tab(),
            kp=_demo_only(
                "Kanban / Командная доска",
                "В соло-проекте нет командного Jira-процесса. "
                "Канбан смоделирован для демонстрации Scrumban-методологии "
                "и навыков работы с бэклогом.",
                "kanban",
            ),
            dash=dash_kanban_tab(),
        )),
        ("backlog", _by_project(
            motif=backlog_tab(),
            kp=_demo_only(
                "Беклог",
                "Реальный беклог Knowledge Pipeline не структурирован "
                "в системе задач — это соло-проект без формального "
                "sprint-планирования. Беклог смоделирован для демонстрации "
                "навыков приоритизации и груминга.",
                "list",
            ),
            dash=backlog_tab(),
        )),
        ("overview",      _by_project(motif=overview_tab(),      kp=real_overview_tab())),
        ("research",      _by_project(motif=research_tab(),      kp=real_research_tab())),
        ("analytics",     _by_project(
            motif=analytics_tab(),
            kp=_demo_only(
                "Analytics · PA",
                "У Knowledge Pipeline нет внешней аудитории пользователей. "
                "Воронки активации, когортное удержание и A/B-тесты применимы "
                "только к продуктам с реальными пользователями. "
                "Вкладка демонстрирует аналитические компетенции PA на "
                "синтетических данных.",
                "bar-chart-2",
            ),
        )),
        ("architecture",  _by_project(motif=architecture_tab(),  kp=real_architecture_tab())),
        ("analysis",      _by_project(
            motif=analysis_tab(),
            kp=_demo_only(
                "Requirements · BA/SA",
                "В соло-проекте не было внешних стейкхолдеров и "
                "формального хендоффа требований от BA к разработчику. "
                "Вкладка смоделирована для демонстрации роли.",
                "file-text",
            ),
        )),
        ("design",        _by_project(motif=design_tab(),        kp=real_design_tab())),
        ("dev",           _by_project(motif=dev_tab(),           kp=real_dev_tab())),
        ("quality",       _by_project(motif=quality_tab(),       kp=real_quality_tab())),
        ("release",       _by_project(motif=release_tab(),       kp=real_release_tab())),
        ("monitoring",    _by_project(motif=monitoring_tab(),    kp=real_monitoring_tab())),
        ("growth",        _by_project(
            motif=growth_tab(),
            kp=_demo_only(
                "Growth & Эксперименты",
                "У соло-пайплайна для личных заметок нет аудитории роста "
                "и монетизации. Вкладка смоделирована для демонстрации "
                "компетенций Growth PM — приоритизация экспериментов, "
                "North Star метрика, ICE-скоринг.",
                "trending-up",
            ),
        )),
        ("roadmap", _by_project(
            motif=_coming_soon(
                "Roadmap",
                "Roadmap этого дашборда доступен только в режиме Product Dashboard. "
                "Переключитесь на 'Product Dashboard' в селекторе проекта.",
                "map",
            ),
            kp=_coming_soon(
                "Roadmap",
                "Roadmap Knowledge Pipeline в разработке.",
                "map",
            ),
            dash=roadmap_tab(),
        )),
        ("ds",   ds_tab()),
        ("discover", _by_project(
            motif=_coming_soon(
                "Discover",
                "Discover-этап дизайн-процесса доступен только в режиме Product Dashboard. "
                "Переключитесь на 'Product Dashboard' в селекторе проекта.",
                "search",
            ),
            kp=_coming_soon(
                "Discover",
                "Discover-этап дизайн-процесса доступен только в режиме Product Dashboard.",
                "search",
            ),
            dash=dash_discover_tab(),
        )),
        ("define", _by_project(
            motif=_coming_soon(
                "Define",
                "Define-этап дизайн-процесса доступен только в режиме Product Dashboard. "
                "Переключитесь на 'Product Dashboard' в селекторе проекта.",
                "target",
            ),
            kp=_coming_soon(
                "Define",
                "Define-этап дизайн-процесса доступен только в режиме Product Dashboard.",
                "target",
            ),
            dash=dash_define_tab(),
        )),
        ("develop", _by_project(
            motif=_coming_soon(
                "Develop",
                "Develop-этап дизайн-процесса доступен только в режиме Product Dashboard. "
                "Переключитесь на 'Product Dashboard' в селекторе проекта.",
                "hammer",
            ),
            kp=_coming_soon(
                "Develop",
                "Develop-этап дизайн-процесса доступен только в режиме Product Dashboard.",
                "hammer",
            ),
            dash=dash_develop_tab(),
        )),
        ("deliver", _by_project(
            motif=_coming_soon(
                "Deliver",
                "Deliver-этап дизайн-процесса доступен только в режиме Product Dashboard. "
                "Переключитесь на 'Product Dashboard' в селекторе проекта.",
                "rocket",
            ),
            kp=_coming_soon(
                "Deliver",
                "Deliver-этап дизайн-процесса доступен только в режиме Product Dashboard.",
                "rocket",
            ),
            dash=dash_deliver_tab(),
        )),
        ("info", info_tab()),
    ]

    result: rx.Component = _WIP
    for tab_id, component in reversed(entries):
        result = rx.cond(NavState.active_tab == tab_id, component, result)
    return result


# Build once at import time — same as before, just generated from a list.
page_content = _build_page_content()
