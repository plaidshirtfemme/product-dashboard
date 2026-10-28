"""Requirements · BA/SA в режиме Product Dashboard — конспект из .md-файлов.

Страница показывает один раздел. Список разделов — в левом меню группой
«Requirements · BA/SA», как пять подвкладок у Design (см. components/
navigation.py). Текст приходит из `dash_app/content/ba-sa/` через BaSaState.

`_MD_MAP` — почему он нужен: базовый component_map у rx.markdown покрывает
только заголовки, абзацы, списки, ссылки и код. Таблицы, картинки и цитаты
в нём отсутствуют и рендерятся голыми тегами с дефолтами браузера. Здесь они
собраны на тех же компонентах и токенах, что и остальной дашборд.
Атрибуты (src таблицы, alt картинки) markdown подставляет сам — их не видно
в Python, они расходятся по элементу на стороне JS.
"""

from __future__ import annotations

import reflex as rx

from ..components.empty_state import empty_state
from ..components.section_header import section_header
from ..states.ba_sa_state import BaSaState
from ..tokens import BORDER, PAGE_MAX_WIDTH, ROLE, SPACING

_MD_MAP = {
    "table": lambda *c, **p: rx.box(
        rx.table.root(*c, variant="surface", size="1"),
        overflow_x="auto",
        width="100%",
        margin=f"{SPACING['md']} 0",
    ),
    "thead": lambda *c, **p: rx.table.header(*c),
    "tbody": lambda *c, **p: rx.table.body(*c),
    "tr": lambda *c, **p: rx.table.row(*c),
    "th": lambda *c, **p: rx.table.column_header_cell(*c),
    "td": lambda *c, **p: rx.table.cell(*c),
    "img": lambda *c, **p: rx.image(
        max_width="100%",
        height="auto",
        border_radius="var(--radius-3)",
        border=f"{BORDER} {ROLE['border-subtle']}",
        margin=f"{SPACING['md']} 0",
    ),
    "blockquote": lambda *c, **p: rx.box(
        *c,
        border_left=f"3px solid {rx.color('teal', 7)}",
        padding_left=SPACING["md"],
        margin=f"{SPACING['md']} 0",
        color=ROLE["text-secondary"],
    ),
}


def _content() -> rx.Component:
    return rx.box(
        rx.markdown(BaSaState.content, component_map=_MD_MAP),
        width="100%",
        background=ROLE["bg-card"],
        border=f"{BORDER} {ROLE['border-default']}",
        border_radius="var(--radius-3)",
        padding=SPACING["lg"],
    )


def ba_sa_tab() -> rx.Component:
    return rx.box(
        section_header(
            rx.cond(BaSaState.active_title != "", BaSaState.active_title, "Конспект BA/SA"),
            subtitle="Конспект BA/SA · подготовка к собеседованиям аналитика",
        ),
        rx.cond(
            BaSaState.sections,
            _content(),
            empty_state(
                "Конспект BA/SA",
                "Материалы разделов держатся локально и не публикуются, "
                "пока не будут готовы.",
                icon="file-text",
                mode="no_data",
            ),
        ),
        padding=SPACING["xl"],
        max_width=PAGE_MAX_WIDTH,
        margin="0 auto",
    )
