"""Define tab (dash-mode only) — Double Diamond, этап 2.

Часть DASH-60. JTBD и RACI перенесены из About project (19-20.07). Персоны для этого
дашборда — две реальные (рекрутер, друг-тестировщик) и одна design-device (роли легенды
Motif, использованные как приём для рассуждений об архитектуре — не формальное research;
их интерактивные карточки живут во вкладке Develop, не здесь).
"""

import reflex as rx

from ..tokens import SPACING, PAGE_MAX_WIDTH
from ..components import section_header
from .motif_about import _jtbd_block, _raci_block, _bullets, _team_cards_grid

_MAX = PAGE_MAX_WIDTH


def _real_personas_block() -> rx.Component:
    return rx.box(
        rx.text(
            "Реальные персоны",
            size="2", weight="bold", color=rx.color("gray", 12),
            margin_bottom="8px",
        ),
        _bullets(
            [
                "Рекрутер — реальная, целевая персона; критерии из вакансий Muse Group и SilentRoom.",
                "Друг-тестировщик — реальная; даёт фидбек по интерфейсу (DASH-68, usability).",
            ],
            "iris",
        ),
        padding=SPACING["md"],
        background=rx.color("iris", 2),
        border=f"1px solid {rx.color('iris', 4)}",
        border_radius="var(--radius-3)",
        margin_bottom=SPACING["xl"],
    )


def _team_personas_block() -> rx.Component:
    return rx.box(
        rx.text(
            "Команда — design-device",
            size="2", weight="bold", color=rx.color("gray", 12),
            margin_bottom="4px",
        ),
        rx.text(
            "Роли легенды Motif использованы как приём, чтобы рассуждать об информационной "
            "архитектуре дашборда, а не формальное research. Карточки в усечённом виде — вариант "
            "компонента без чипсов назначенных черт (полный интерактивный вариант — во вкладке Develop).",
            size="1", color=rx.color("gray", 9), margin_bottom=SPACING["md"], line_height="1.6",
        ),
        _team_cards_grid(compact=True),
        margin_bottom=SPACING["xl"],
    )


def dash_define_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Define",
            subtitle="Double Diamond · этап 2 — для кого проектируем, роли и ответственность",
        ),
        _real_personas_block(),
        _team_personas_block(),
        _jtbd_block(),
        rx.box(height=SPACING["xl"]),
        _raci_block(),
        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
