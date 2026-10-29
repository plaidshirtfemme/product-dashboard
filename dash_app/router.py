"""Tab router — maps NavState.active_tab → the right component.

Each entry in _TAB_ENTRIES is (tab_id, component). The list is processed
into a nested rx.cond chain at import time — same runtime structure as
before, but readable as a flat list instead of 16-level nesting.
"""

import reflex as rx
from .states import NavState, ProjectState, show_mode
from .tokens import ROLE
from .components.empty_state import empty_state
from .pages.dash_about import dash_about_tab
from .pages.motif_about import motif_about_tab
from .pages.motif_overview import motif_overview_tab
from .pages.backlog import backlog_tab
from .pages.kanban import kanban_tab
from .pages.motif_research import motif_research_tab
from .pages.motif_analytics import motif_analytics_tab
from .pages.motif_analysis import motif_analysis_tab
from .pages.ba_sa import ba_sa_tab
from .pages.motif_design import motif_design_tab
from .pages.motif_growth import motif_growth_tab
from .pages.motif_architecture import motif_architecture_tab
from .pages.motif_dev import motif_dev_tab
from .pages.motif_quality import motif_quality_tab
from .pages.motif_release import motif_release_tab
from .pages.motif_monitoring import motif_monitoring_tab
from .pages.info import info_tab
from .pages.dash_ds import dash_ds_tab
from .pages.dash_architecture import dash_architecture_tab
from .pages.dash_design import dash_design_tab

# ── Knowledge Pipeline tabs gated by build visibility (DASH-162) ───────────
# Локально импортируем real_* как раньше. В публичной сборке режим "kp"
# закрыт: его данные (dash_app/data/kp/) не уезжают, поэтому импорт либо
# пропускается (show_mode), либо падает ImportError — и тогда на месте
# KP-вкладок ставится заглушка, а бэкенд не падает.
_SHOW_KP = show_mode("kp")
if _SHOW_KP:
    try:
        from .pages.kp_overview import kp_overview_tab
        from .pages.kp_architecture import kp_architecture_tab
        from .pages.kp_dev import kp_dev_tab
        from .pages.kp_quality import kp_quality_tab
        from .pages.kp_release import kp_release_tab
        from .pages.kp_monitoring import kp_monitoring_tab
        from .pages.kp_research import kp_research_tab
    except ImportError:
        _SHOW_KP = False

if not _SHOW_KP:
    def _kp_local_only() -> rx.Component:
        return empty_state(
            "Knowledge Pipeline",
            "Этот проект собирается только в локальной сборке.",
            icon="lock",
            mode="demo_only",
        )

    kp_overview_tab = kp_architecture_tab = kp_dev_tab = kp_quality_tab = (
        kp_release_tab
    ) = kp_monitoring_tab = kp_research_tab = _kp_local_only
from .pages.dash_roadmap import dash_roadmap_tab
from .pages.dash_discover import dash_discover_tab
from .pages.dash_define import dash_define_tab
from .pages.dash_develop import dash_develop_tab
from .pages.dash_deliver import dash_deliver_tab

_WIP = rx.box(
    rx.text("В разработке", color=ROLE["text-secondary"], size="3"),
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
        ProjectState.project_mode == "motif",
        motif,
        rx.cond(ProjectState.project_mode == "kp", kp, dash_component),
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
            kp=_coming_soon(
                "О проекте",
                "Описание проекта Knowledge Pipeline появится в следующей итерации.",
                "info",
            ),
            dash=dash_about_tab(),
        )),
        ("kanban", kanban_tab()),
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
        ("overview",      _by_project(motif=motif_overview_tab(),      kp=kp_overview_tab())),
        ("research",      _by_project(motif=motif_research_tab(),      kp=kp_research_tab())),
        ("analytics",     _by_project(
            motif=motif_analytics_tab(),
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
        ("architecture",  _by_project(motif=motif_architecture_tab(),  kp=kp_architecture_tab(), dash=dash_architecture_tab())),
        ("analysis",      _by_project(
            motif=motif_analysis_tab(),
            kp=_demo_only(
                "Requirements · BA/SA",
                "В соло-проекте не было внешних стейкхолдеров и "
                "формального хендоффа требований от BA к разработчику. "
                "Вкладка смоделирована для демонстрации роли.",
                "file-text",
            ),
            dash=ba_sa_tab(),
        )),
        ("design", _by_project(
            motif=motif_design_tab(),
            kp=_coming_soon(
                "Design",
                "Дизайн-решения Knowledge Pipeline появятся в следующей итерации.",
                "pen-tool",
            ),
            dash=dash_design_tab(),
        )),
        ("dev",           _by_project(motif=motif_dev_tab(),           kp=kp_dev_tab())),
        ("quality",       _by_project(motif=motif_quality_tab(),       kp=kp_quality_tab())),
        ("release",       _by_project(motif=motif_release_tab(),       kp=kp_release_tab())),
        ("monitoring",    _by_project(motif=motif_monitoring_tab(),    kp=kp_monitoring_tab())),
        ("growth",        _by_project(
            motif=motif_growth_tab(),
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
            dash=dash_roadmap_tab(),
        )),
        ("ds", _by_project(
            motif=_coming_soon(
                "Design System",
                "Design System этого дашборда доступна только в режиме Product Dashboard. "
                "Переключитесь на 'Product Dashboard' в селекторе проекта.",
                "palette",
            ),
            kp=_coming_soon(
                "Design System",
                "Design System этого дашборда доступна только в режиме Product Dashboard.",
                "palette",
            ),
            dash=dash_ds_tab(),
        )),
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
