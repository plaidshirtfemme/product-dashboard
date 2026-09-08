"""Define tab (dash-mode only) — Double Diamond, этап 2.

Часть DASH-60. Персоны и JTBD пользователей ДАШБОРДА — явный артефакт (DASH-143):
две персоны-читателя (рекрутер-скринер и дизайн-лид) с JTBD «Когда…я хочу…чтобы…»
и картой «требование вакансии → где ответ». Объект оценки у обеих — и портфолио,
и сам дашборд (решение Guzel 25.07).

⚠️ Ниже на вкладке есть ВТОРОЙ JTBD-блок — художников, пользователей выдуманного
Motif. Это другой продукт, блоки намеренно разделены и подписаны.

Персоны команды Motif — design-device (приём для рассуждений об информационной
архитектуре), не формальное research; их интерактивные карточки живут во Develop.
"""

import reflex as rx

from ..tokens import SPACING, PAGE_MAX_WIDTH, BORDER
from ..components import section_header, data_table
from ..data.dash_personas import (
    READER_PERSONAS, TEAM_PERSONAS, REQUIREMENT_MAP, STATUS_META,
)
from .motif_about import _jtbd_block, _raci_block, _team_cards_grid

_MAX = PAGE_MAX_WIDTH


# ---------------------------------------------------------------------------
# Провенанс: откуда персоны взялись и чего в них нет
# ---------------------------------------------------------------------------

def _provenance_block() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.icon("info", size=14, color=rx.color("amber", 11)),
            rx.text("Прото-персоны, не результат интервью", size="2", weight="bold",
                    color=rx.color("gray", 12)),
            gap=SPACING["sm"], align="center", margin_bottom=SPACING["sm"],
        ),
        rx.text(
            "Собраны из текстов вакансий (Company 1, Company 2) и анализа аудитории в "
            "USER_STORIES.md. Интервью с рекрутерами и наблюдений за ними не было — это "
            "вторичный desk research, и подаётся именно так. Валидация запланирована: "
            "usability с IT-друзьями (DASH-68 — они не рекрутеры, journey рекрутера ими не "
            "валидируется) и реальная аналитика навигации после публикации (DASH-125).",
            size="1", color=rx.color("gray", 11), line_height="1.6",
        ),
        padding=SPACING["md"],
        background=rx.color("amber", 2),
        border=f"{BORDER} {rx.color('amber', 5)}",
        border_left=f"3px solid {rx.color('amber', 8)}",
        border_radius="var(--radius-3)",
        margin_bottom=SPACING["xl"],
    )


# ---------------------------------------------------------------------------
# Карточка персоны
# ---------------------------------------------------------------------------

def _bullet_list(items: list[str], accent: str) -> rx.Component:
    return rx.flex(
        *[
            rx.flex(
                rx.box(
                    width="5px", height="5px", flex_shrink="0",
                    margin_top="7px",
                    background=rx.color(accent, 8),
                    border_radius="var(--radius-full)",
                ),
                rx.text(t, size="1", color=rx.color("gray", 11), line_height="1.6"),
                gap=SPACING["sm"], align="start",
            )
            for t in items
        ],
        direction="column", gap="4px",
    )


def _sub(title: str, accent: str, body: rx.Component) -> rx.Component:
    return rx.box(
        rx.text(title, size="1", weight="bold", color=rx.color(accent, 11),
                style={"text_transform": "uppercase", "letter_spacing": "0.04em"},
                margin_bottom="4px"),
        body,
        margin_bottom=SPACING["md"],
    )


def _jtbd_row(job: tuple[str, str, str], accent: str) -> rx.Component:
    """Одна работа в каноничной форме «Когда … я хочу … чтобы …»."""
    when, want, so_that = job
    def _part(label: str, text: str) -> rx.Component:
        return rx.flex(
            rx.text(label, size="1", weight="bold", color=rx.color(accent, 11),
                    flex_shrink="0", style={"min_width": "58px"}),
            rx.text(text, size="1", color=rx.color("gray", 11), line_height="1.6"),
            gap=SPACING["sm"], align="start",
        )
    return rx.box(
        _part("Когда", when),
        _part("я хочу", want),
        _part("чтобы", so_that),
        padding=SPACING["sm"],
        background=rx.color(accent, 2),
        border_left=f"2px solid {rx.color(accent, 7)}",
        border_radius=f"0 var(--radius-2) var(--radius-2) 0",
        margin_bottom="6px",
    )


def _persona_card(p: dict) -> rx.Component:
    accent = p["accent"]
    return rx.box(
        # шапка
        rx.flex(
            rx.flex(
                rx.icon(p["icon"], size=18, color="white"),
                width="34px", height="34px", flex_shrink="0",
                align="center", justify="center",
                background=rx.color(accent, 9),
                border_radius="var(--radius-2)",
            ),
            rx.box(
                rx.flex(
                    rx.text(p["label"], size="3", weight="bold", color=rx.color("gray", 12)),
                    # природа персоны: приём для рассуждений vs прото-персона из вакансий
                    rx.badge(p["nature"], color_scheme=accent, variant="outline", size="1")
                    if p.get("nature") else rx.fragment(),
                    gap=SPACING["sm"], align="center", wrap="wrap",
                ),
                rx.text(p["tagline"], size="1", color=rx.color(accent, 11), line_height="1.5"),
                flex="1", min_width="0",
            ),
            gap=SPACING["md"], align="center", margin_bottom=SPACING["md"],
        ),
        rx.text(p["context"], size="1", color=rx.color("gray", 11),
                line_height="1.6", margin_bottom=SPACING["md"]),
        rx.separator(margin_bottom=SPACING["md"]),
        _sub("Цели", accent, _bullet_list(p["goals"], accent)),
        _sub("Поведение", accent, _bullet_list(p["behaviour"], accent)),
        _sub("Боли", accent, _bullet_list(p["pains"], accent)),
        _sub("Jobs To Be Done", accent,
             rx.box(*[_jtbd_row(j, accent) for j in p["jtbd"]])),
        rx.flex(
            rx.icon("book-open", size=12, color=rx.color("gray", 8)),
            rx.text(p["source"], size="1", color=rx.color("gray", 9), line_height="1.5"),
            gap="6px", align="start",
            padding_top=SPACING["sm"],
            border_top=f"1px solid {rx.color('gray', 4)}",
        ),
        padding=SPACING["lg"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color(accent, 5)}",
        border_top=f"3px solid {rx.color(accent, 8)}",
        border_radius="var(--radius-3)",
        min_width="0",
    )


def _persona_grid(personas: list[dict]) -> rx.Component:
    """Сетка карточек. Именно grid, а не flex: при 9 карточках flex делил ширину
    на всех и текст схлопывался в колонку по букве. minmax даёт карточке пол
    и переносит остальные на следующий ряд."""
    return rx.box(
        *[_persona_card(p) for p in personas],
        display="grid",
        grid_template_columns="repeat(auto-fill, minmax(340px, 1fr))",
        gap=SPACING["md"],
        align_items="stretch",
        width="100%",
    )


def _readers_block() -> rx.Component:
    return rx.box(
        rx.text("Кто читает портфолио", size="4", weight="bold",
                color=rx.color("gray", 12), margin_bottom="4px"),
        rx.text(
            "Два разных читателя с разными работами. Различение не придумано задним числом: "
            "правило приоритизации проекта с самого начала спрашивает «это увидит рекрутер за "
            "30 секунд, или это глубина для дизайн-лида на ревью?» — персоны делают его явным. "
            "Отсюда двухслойность дашборда: сводки сверху, глубина внутри вкладок.",
            size="1", color=rx.color("gray", 9), line_height="1.6",
            margin_bottom=SPACING["md"],
        ),
        _persona_grid(READER_PERSONAS),
        margin_bottom=SPACING["xl"],
    )


# ---------------------------------------------------------------------------
# Требование вакансии → где ответ (объект оценки: и портфолио, и сам дашборд)
# ---------------------------------------------------------------------------

def _status_chip(status: str) -> rx.Component:
    m = STATUS_META[status]
    return rx.box(
        rx.text(f"{m['glyph']} {m['label']}", size="1", weight="medium",
                color=rx.color(m["color"], 11), white_space="nowrap"),
        background=rx.color(m["color"], 3),
        padding="1px 8px",
        border_radius="var(--radius-full)",
        display="inline-block",
    )


def _requirements_block() -> rx.Component:
    rows = [
        [
            rx.box(
                rx.text(r["req"], size="1", color=rx.color("gray", 12),
                        line_height="1.5", font_style="italic"),
                rx.badge(r["src"], color_scheme="violet", variant="soft", size="1",
                         margin_top="3px"),
            ),
            rx.text(r["where"], size="1", color=rx.color("teal", 11), line_height="1.5"),
            _status_chip(r["status"]),
            rx.text(r["note"], size="1", color=rx.color("gray", 10), line_height="1.5"),
        ]
        for r in REQUIREMENT_MAP
    ]
    return rx.box(
        rx.text("Требование вакансии → где ответ", size="4", weight="bold",
                color=rx.color("gray", 12), margin_bottom="4px"),
        rx.text(
            "Чеклист, по которому персона-скринер сверяет кандидата. Объект оценки — не только "
            "портфолио, но и сам дашборд: колонка «где ответ» ведёт внутрь него. Требования — "
            "формулировками из вакансий; статусы честные, включая пробелы.",
            size="1", color=rx.color("gray", 9), line_height="1.6",
            margin_bottom=SPACING["md"],
        ),
        data_table(
            columns=["Требование", "Где ответ", "Статус", "Комментарий"],
            rows=rows,
        ),
        margin_bottom=SPACING["xl"],
    )


# ---------------------------------------------------------------------------
# Команда Motif как design-device + JTBD ДРУГОГО продукта (явно подписан)
# ---------------------------------------------------------------------------

def _team_personas_block() -> rx.Component:
    return rx.box(
        rx.text("Команда Motif — пользователи дашборда", size="4", weight="bold",
                color=rx.color("gray", 12), margin_bottom="4px"),
        rx.text(
            "Провенанс здесь другой, чем у читателей выше: это не прото-персоны из вакансий, а "
            "design-device — роли выдуманной команды, через которые проверяется информационная "
            "архитектура («кому нужна эта вкладка и зачем»). Реальных людей за ними нет, "
            "формальным research это не является. Покрыты все девять продуктовых ролей команды; "
            "Ли (Community Manager) и Нур (Artist-in-Residence) намеренно вне набора — они не "
            "пользователи этого инструмента.",
            size="1", color=rx.color("gray", 9), line_height="1.6",
            margin_bottom=SPACING["md"],
        ),
        rx.box(
            _persona_grid(TEAM_PERSONAS),
            margin_bottom=SPACING["lg"],
        ),
        rx.text("Полный состав легенды", size="2", weight="bold",
                color=rx.color("gray", 11), margin_bottom="4px"),
        rx.text(
            "Карточки в усечённом виде — полный интерактивный вариант во вкладке Develop.",
            size="1", color=rx.color("gray", 9), margin_bottom=SPACING["sm"],
        ),
        _team_cards_grid(compact=True),
        margin_bottom=SPACING["xl"],
    )


def _motif_jtbd_block() -> rx.Component:
    """JTBD пользователей Motif — ДРУГОЙ продукт, не дашборд. Подпись обязательна:
    без неё блок читается как JTBD дашборда (та же ошибка, что «KP ≠ дашборд»)."""
    return rx.box(
        rx.flex(
            rx.icon("triangle-alert", size=13, color=rx.color("gray", 9)),
            rx.text(
                "Ниже — JTBD художников, пользователей выдуманного продукта Motif. Это другой "
                "продукт: не путать с JTBD читателей дашборда выше.",
                size="1", color=rx.color("gray", 9), line_height="1.6",
            ),
            gap="6px", align="start", margin_bottom=SPACING["sm"],
        ),
        _jtbd_block(),
    )


def dash_define_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Define",
            subtitle="Double Diamond · этап 2 — для кого проектируем: персоны, JTBD, чеклист требований",
        ),
        _provenance_block(),
        _readers_block(),
        _requirements_block(),
        _team_personas_block(),
        _motif_jtbd_block(),
        rx.box(height=SPACING["xl"]),
        _raci_block(),
        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
