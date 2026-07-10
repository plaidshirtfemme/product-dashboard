"""Info tab — wiki о процессах команды и логике дашборда."""

import reflex as rx
from ..tokens import SPACING, BORDER
from ..components import section_header, data_source_badge


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _bullet(text: str) -> rx.Component:
    return rx.flex(
        rx.box(width="5px", height="5px", border_radius="50%",
               background=rx.color("gray", 8), flex_shrink="0", margin_top="8px"),
        rx.text(text, size="2", color=rx.color("gray", 11), line_height="1.7"),
        gap="10px", align="start",
    )


def _subsection(title: str, *children) -> rx.Component:
    return rx.box(
        rx.text(title, weight="bold", size="2",
                color=rx.color("gray", 11), margin_bottom="8px"),
        *children,
    )


def _wiki_card(title: str, accent: str, *children) -> rx.Component:
    return rx.box(
        rx.box(
            rx.text(title, weight="bold", size="3", color=rx.color(accent, 11)),
            border_left=f"3px solid {rx.color(accent, 7)}",
            padding_left="12px",
            margin_bottom=SPACING["md"],
        ),
        rx.flex(*children, direction="column", gap=SPACING["md"]),
        padding=SPACING["lg"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        flex="1",
        min_width="260px",
    )


# ---------------------------------------------------------------------------
# Блок 1 — Команда и процесс
# ---------------------------------------------------------------------------

def _team_and_process() -> rx.Component:
    return rx.box(
        rx.box(
            rx.text(
                "Продуктовая команда из ~10 ролей (часть ролей представляет подкоманды: "
                "дизайнеры, разработчики, QA). Работает по модели ",
                rx.text.span("Scrumban", weight="bold"),
                " с непрерывной доставкой через ",
                rx.text.span("CI/CD.", weight="bold"),
                " Среды защищены от встреч — время для глубокой работы.",
                size="2", color=rx.color("gray", 11), line_height="1.7",
            ),
            padding=SPACING["lg"],
            background=rx.color("teal", 1),
            border=f"{BORDER} {rx.color('teal', 4)}",
            border_radius="var(--radius-3)",
            margin_bottom=SPACING["lg"],
        ),
        rx.flex(
            _wiki_card(
                "Scrumban", "teal",
                _subsection(
                    "Как устроена работа:",
                    _bullet("Kanban-доска с WIP-лимитами — основной инструмент управления потоком"),
                    _bullet("Спринты как временные маркеры для церемоний (планирование, ретро), без жёсткого commitment"),
                    _bullet("Работа поступает и завершается непрерывно, не батчами в конце спринта"),
                    _bullet("Приоритизация через регулярный replenishment meeting"),
                ),
            ),
            _wiki_card(
                "CI/CD", "violet",
                _subsection(
                    "Как устроена доставка:",
                    _bullet("Каждый merge в main проходит автоматические проверки — gate перед продом"),
                    _bullet("Деплой в production автоматический после прохождения всех gates"),
                    _bullet("Команда может выпускать несколько раз в день"),
                    _bullet("QA фокусируется на автотестах, а не на ручной регрессии перед релизом"),
                ),
            ),
            _wiki_card(
                "Культура", "amber",
                _subsection(
                    "Принципы работы:",
                    _bullet("Async-first: синхронные встречи — исключение, а не норма. Прежде чем созвониться — документ, вопрос письменно, время на ответ"),
                    _bullet("Решения фиксируются письменно всегда — даже если обсудили устно. Контекст живёт в документах, не в головах людей"),
                    _bullet("Jira + Confluence поддерживают культуру, но не заменяют её"),
                    _bullet("Среда — защищённый день без встреч"),
                    _bullet("Архитектурные решения фиксируются в ADR"),
                ),
            ),
            gap=SPACING["lg"], wrap="wrap",
        ),
        rx.box(
            rx.text("Почему это важно для дашборда",
                    weight="bold", size="2",
                    color=rx.color("gray", 11), margin_bottom="8px"),
            rx.flex(
                _bullet("Метрики потока (Cycle Time, Lead Time, Flow Efficiency) релевантнее спринтовых"),
                _bullet("Release tab — мониторинг того что идёт в прод, а не планирование"),
                _bullet("Backlog всегда актуален и приоритизирован — спринт не единственный инструмент фокуса"),
                direction="column", gap="6px",
            ),
            padding=SPACING["lg"],
            background=rx.color("gray", 2),
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            margin_top=SPACING["lg"],
        ),
    )


# ---------------------------------------------------------------------------
# Блок 2 — Календарь церемоний
# ---------------------------------------------------------------------------

_CEREMONIES: dict[str, dict] = {
    "standup":       {"name": "Standup",                "color": "teal",   "duration": "15 мин",    "participants": "Вся команда",                  "description": "Обход доски: что заблокировано, что застряло"},
    "squad_standup": {"name": "Squad Standup",           "color": "blue",   "duration": "15 мин",    "participants": "Подкоманда (dev / design / QA)", "description": "Внутренний синхрон подкоманды — детали и блокеры на уровне подкоманды. Проводится до или после общего Standup"},
    "planning":      {"name": "Sprint Planning",         "color": "amber",  "duration": "60–90 мин", "participants": "PM + BA + SA + лиды",          "description": "Наполнение очереди, расстановка приоритетов. Без жёсткого commitment"},
    "grooming":      {"name": "Backlog Refinement",      "color": "iris",   "duration": "45–60 мин", "participants": "PM + BA + dev-лиды",            "description": "Детализация и оценка задач следующего спринта. Проводится накануне Sprint Planning"},
    "sdr":           {"name": "Service Delivery Review", "color": "violet", "duration": "30–45 мин", "participants": "PM + лиды",                    "description": "Метрики потока: Cycle Time, Throughput, WIP. Поиск узких мест"},
    "demo":          {"name": "Demo / Sprint Review",    "color": "grass",  "duration": "45–60 мин", "participants": "Вся команда + стейкхолдеры",   "description": "Показывают что завершено, собирают фидбек"},
    "retro":         {"name": "Retrospective",           "color": "orange", "duration": "45–60 мин", "participants": "Вся команда",                  "description": "Что мешает потоку, что улучшаем в процессе. Перенесена на пятницу — четверг разгружен"},
    "arch":          {"name": "Architecture Review",     "color": "plum",   "duration": "60 мин",    "participants": "Architect + PM + dev-лиды",    "description": "ADR, тех-долг, решения с долгосрочными последствиями"},
    "soundcheck":    {"name": "Soundcheck",              "color": "cyan",   "duration": "30 мин",    "participants": "Вся компания",                 "description": "Продуктовые апдейты, общая синхронизация"},
}

# 4 недели × 7 дней (Пн=0 … Вс=6), Ср=2 защищена
_CALENDAR: list[list[str]] = [
    ["planning", "standup", "squad_standup"], [],  [], ["standup", "squad_standup"], ["sdr"],                [], [],  # Нед. 1
    ["standup", "squad_standup"],             [],  [], ["standup", "squad_standup", "demo"], ["retro", "grooming"], [], [],  # Нед. 2
    ["planning", "standup", "squad_standup"], [],  [], ["standup", "squad_standup"], ["sdr"],                [], [],  # Нед. 3
    ["standup", "squad_standup"],             [],  [], ["standup", "squad_standup", "demo", "soundcheck"], ["retro", "grooming", "arch"], [], [],  # Нед. 4
]

_DAY_NAMES  = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
_WEEK_NAMES = ["Неделя 1 · Спринт 1 начало", "Неделя 2 · Спринт 1 конец",
               "Неделя 3 · Спринт 2 начало", "Неделя 4 · Спринт 2 конец"]
_PROTECTED  = {2, 9, 16, 23}
_WEEKEND    = {5, 6, 12, 13, 19, 20, 26, 27}


class CeremonyState(rx.State):
    selected_day: int = -1
    selected_label: str = ""

    def select_day(self, day: int):
        if day in _PROTECTED or day in _WEEKEND:
            return
        self.selected_day = day
        week = day // 7
        self.selected_label = f"{_WEEK_NAMES[week]} · {_DAY_NAMES[day % 7]}"

    @rx.var
    def selected_ceremonies(self) -> list[dict]:
        if self.selected_day < 0:
            return []
        return [_CEREMONIES[k] for k in _CALENDAR[self.selected_day]]

    @rx.var
    def has_selection(self) -> bool:
        return self.selected_day >= 0

    @rx.var
    def day_is_empty(self) -> bool:
        if self.selected_day < 0:
            return False
        return len(_CALENDAR[self.selected_day]) == 0


# ── Calendar cell ────────────────────────────────────────────────────────────

def _day_cell(day_idx: int) -> rx.Component:
    keys        = _CALENDAR[day_idx]
    is_protected = day_idx in _PROTECTED
    is_weekend   = day_idx in _WEEKEND
    is_clickable = not is_protected and not is_weekend

    strips = [
        rx.box(height="12px",
               background=rx.color(_CEREMONIES[k]["color"], 7),
               width="100%")
        for k in keys
    ]

    cell_bg     = rx.color("gray", 3) if is_protected else rx.color("gray", 2)
    cell_border = rx.cond(
        CeremonyState.selected_day == day_idx,
        "2px solid var(--teal-8)",
        "1px solid var(--gray-4)",
    ) if is_clickable else "1px solid var(--gray-4)"

    return rx.box(
        rx.box(*strips, width="100%"),
        rx.icon("lock", size=10, color=rx.color("gray", 6),
                margin_top="6px", margin_x="auto", display="block") if is_protected else rx.box(),
        width="52px",
        height="52px",
        background=cell_bg,
        border_radius="var(--radius-2)",
        border=cell_border,
        overflow="hidden",
        cursor="pointer" if is_clickable else "default",
        on_click=CeremonyState.select_day(day_idx) if is_clickable else None,
        flex_shrink="0",
        transition="border 0.1s",
    )


# ── Calendar week row ────────────────────────────────────────────────────────

def _calendar_week(week_idx: int) -> rx.Component:
    start = week_idx * 7
    return rx.flex(
        rx.text(_WEEK_NAMES[week_idx], size="1", color=rx.color("gray", 9),
                width="180px", flex_shrink="0", padding_top="16px"),
        rx.flex(
            *[_day_cell(start + d) for d in range(7)],
            gap="6px",
        ),
        align="start",
        gap=SPACING["md"],
    )


# ── Legend ───────────────────────────────────────────────────────────────────

def _legend() -> rx.Component:
    items = [
        rx.flex(
            rx.box(width="12px", height="12px", border_radius="2px",
                   background=rx.color(v["color"], 7), flex_shrink="0"),
            rx.text(v["name"], size="1", color=rx.color("gray", 10)),
            gap="6px", align="center",
        )
        for v in _CEREMONIES.values()
    ]
    items.append(
        rx.flex(
            rx.box(width="12px", height="12px", border_radius="2px",
                   background=rx.color("gray", 3), flex_shrink="0"),
            rx.text("Среда — без встреч", size="1", color=rx.color("gray", 10)),
            gap="6px", align="center",
        )
    )
    return rx.flex(*items, gap=SPACING["md"], wrap="wrap", margin_top=SPACING["md"])


# ── Detail table ─────────────────────────────────────────────────────────────

def _detail_row(c: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.badge(c["name"], color_scheme=c["color"], variant="soft", size="1")
        ),
        rx.table.cell(rx.text(c["duration"],     size="2")),
        rx.table.cell(rx.text(c["participants"], size="2", color=rx.color("gray", 10))),
        rx.table.cell(rx.text(c["description"],  size="2", color=rx.color("gray", 10))),
    )


def _detail_panel() -> rx.Component:
    return rx.box(
        rx.cond(
            CeremonyState.has_selection,
            rx.box(
                rx.text(CeremonyState.selected_label,
                        size="2", weight="bold",
                        color=rx.color("gray", 11),
                        margin_bottom="10px"),
                rx.cond(
                    CeremonyState.day_is_empty,
                    rx.text("В этот день встреч нет", size="2",
                            color=rx.color("gray", 8)),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                *[rx.table.column_header_cell(
                                    col,
                                    style={"font_size": "11px",
                                           "color": rx.color("gray", 9),
                                           "text_transform": "uppercase"})
                                  for col in ["Встреча", "Время", "Участники", "О чём"]]
                            )
                        ),
                        rx.table.body(
                            rx.foreach(CeremonyState.selected_ceremonies, _detail_row)
                        ),
                        variant="surface", width="100%", size="1",
                    ),
                ),
            ),
            rx.text("Выберите день в календаре ↑",
                    size="2", color=rx.color("gray", 7)),
        ),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        min_height="72px",
        margin_top=SPACING["md"],
    )


# ── Calendar section ─────────────────────────────────────────────────────────

def _ceremony_calendar() -> rx.Component:
    # Day-name header
    header = rx.flex(
        rx.box(width="180px", flex_shrink="0"),
        rx.flex(
            *[rx.text(d, size="1", weight="medium",
                      color=rx.color("gray", 9 if d != "Ср" else 7),
                      width="52px", text_align="center")
              for d in _DAY_NAMES],
            gap="6px",
        ),
        align="center",
        gap=SPACING["md"],
        margin_bottom="6px",
    )

    return rx.box(
        header,
        rx.flex(
            *[_calendar_week(w) for w in range(4)],
            direction="column",
            gap=SPACING["md"],
        ),
        _legend(),
        _detail_panel(),
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def info_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Info",
            subtitle="Опорный документ: процессы команды, роли, логика дашборда",
            action=data_source_badge("real"),
        ),

        # ── Блок 1 ──────────────────────────────────────────────────────────
        rx.text("Команда и процесс",
                size="4", weight="bold",
                color=rx.color("gray", 12),
                margin_bottom=SPACING["md"]),
        _team_and_process(),

        rx.box(height=SPACING["xl"]),

        # ── Блок 2 ──────────────────────────────────────────────────────────
        rx.text("Календарь церемоний",
                size="4", weight="bold",
                color=rx.color("gray", 12),
                margin_bottom="4px"),
        rx.text("2-недельный спринт · Standup пн + чт · Среда защищена",
                size="2", color=rx.color("gray", 9),
                margin_bottom=SPACING["md"]),
        _ceremony_calendar(),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
