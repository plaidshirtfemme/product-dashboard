"""Develop tab (dash-mode only) — Double Diamond, этап 3.

Часть DASH-60. Интерактивный воркбенч (карточки команды с drag-and-drop, личные банки,
таймлайн/спайн, экспорт раскладки) перенесён из About project (19-20.07, решение Guzel:
весь инструмент сборки истории — тоже часть дизайн-процесса, не только его текстовый
результат). Это рабочий прототип: демонстрирует interaction design и state management,
а не просто диаграмму. User flows (DASH-59) — следующий шаг.
"""

import reflex as rx

from ..tokens import SPACING, PAGE_MAX_WIDTH
from ..components import section_header
from .motif_about import _team_block, _factors_block, _layout_export, _placeholder

_MAX = PAGE_MAX_WIDTH


def dash_develop_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Develop",
            subtitle="Double Diamond · этап 3 — прототип: интерактивный воркбенч сборки истории",
        ),
        _team_block(),
        rx.box(height=SPACING["xl"]),
        _factors_block(),
        rx.box(height=SPACING["xl"]),
        _layout_export(),
        rx.box(height=SPACING["xl"]),
        _placeholder("User flows по пользователям (DASH-59) — следующий шаг сегодня."),
        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
