"""
Growth tab — Product Growth / Experimentation view (этап 9 MVP).

Sections:
1. Growth Health     — stat cards: experiments, B-wins, SP done, release delivery
2. Experiment Log    — A/B experiment table with result badges
3. Release Delivery  — per-release progress + slip count
4. Activation Funnel — simulated user activation steps (⚠️ no real analytics)
"""

import reflex as rx

from ..tokens import SPACING, BORDER
from ..components import (
    table_container,
    progress_bar,
    stat_card,
    stat_card_row,
    data_source_badge,
    mono_text,
    section_header,
)
from ..data.adapter import load_issues
from ..data.metrics import growth_stats, growth_experiments, growth_releases

# Simulated activation funnel (⚠️ no real user analytics)
_FUNNEL = [
    ("Установил пайплайн", 100),
    ("Первый запуск", 78),
    ("Первая заметка создана", 61),
    ("10+ заметок", 44),
    ("Регулярное использование", 29),
]


# ---------------------------------------------------------------------------
# Experiment result badge
# ---------------------------------------------------------------------------

def _result_badge(result: str | None) -> rx.Component:
    if result == "Вариант B лучше":
        return rx.badge("B лучше ✓", color_scheme="teal", variant="solid", size="1")
    if result == "Без значимой разницы":
        return rx.badge("Без разницы", color_scheme="amber", variant="soft", size="1")
    return rx.badge("Ожидает", color_scheme="gray", variant="outline", size="1")


def _decision_badge(result: str | None, status: str) -> rx.Component:
    if status != "Done":
        return rx.badge("Running", color_scheme="blue", variant="outline", size="1")
    if result == "Вариант B лучше":
        return rx.badge("▲ Scale", color_scheme="grass", variant="solid", size="1")
    if result == "Без значимой разницы":
        return rx.badge("✕ Kill", color_scheme="tomato", variant="soft", size="1")
    return rx.badge("—", color_scheme="gray", variant="outline", size="1")


# ---------------------------------------------------------------------------
# Experiment Log table
# ---------------------------------------------------------------------------

def _experiment_table(rows) -> rx.Component:
    COL = "90px 100px 180px 1fr 140px 110px"
    header = rx.grid(
        rx.text("Ключ", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Статус", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Вариант A (контроль)", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Вариант B (тест)", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Результат", size="1", weight="medium", color=rx.color("gray", 9)),
        rx.text("Решение", size="1", weight="medium", color=rx.color("gray", 9)),
        columns=COL,
        gap=SPACING["md"],
        padding=f"8px {SPACING['md']}",
        background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )

    table_rows = []
    for idx, r in enumerate(rows):
        status_color = "grass" if r.status == "Done" else "amber"
        decision = _decision_badge(r.result, r.status)
        table_rows.append(
            rx.grid(
                mono_text(r.key),
                rx.badge(
                    "Готово" if r.status == "Done" else r.status,
                    color_scheme=status_color,
                    variant="soft",
                    size="1",
                ),
                rx.text(r.variant_a, size="2", color=rx.color("gray", 10)),
                rx.text(r.variant_b, size="2", color=rx.color("gray", 12), weight="medium"),
                _result_badge(r.result),
                decision,
                columns=COL,
                gap=SPACING["md"],
                align="center",
                padding=f"10px {SPACING['md']}",
                background="white" if idx % 2 == 0 else rx.color("gray", 1),
                border_top=f"{BORDER} {rx.color('gray', 3)}",
            )
        )

    # Summary row
    b_wins = sum(1 for r in rows if r.result == "Вариант B лучше")
    kills = sum(1 for r in rows if r.status == "Done" and r.result == "Без значимой разницы")
    running = sum(1 for r in rows if r.status != "Done")
    table_rows.append(
        rx.grid(
            rx.text("", size="2"),
            rx.text("", size="2"),
            rx.text("", size="2"),
            rx.text(
                f"B выиграл в {b_wins} из {len(rows)} экспериментов",
                size="2",
                color=rx.color("teal", 11),
                weight="medium",
            ),
            rx.text("", size="2"),
            rx.flex(
                rx.text(f"▲{b_wins}", size="1", weight="bold", color=rx.color("grass", 11)),
                rx.text(f"✕{kills}", size="1", weight="bold", color=rx.color("tomato", 11)),
                rx.text(f"▶{running}", size="1", color=rx.color("blue", 11)),
                gap="6px", align="center",
            ),
            columns=COL,
            gap=SPACING["md"],
            align="center",
            padding=f"10px {SPACING['md']}",
            background=rx.color("teal", 2),
            border_top=f"2px solid {rx.color('teal', 5)}",
        )
    )

    return table_container(
        header,
        *table_rows
    )


# ---------------------------------------------------------------------------
# Release Delivery
# ---------------------------------------------------------------------------

def _release_delivery(releases) -> rx.Component:
    if not releases:
        return rx.text("Нет данных о релизах", size="2", color=rx.color("gray", 9))

    cards = []
    for r in releases:
        color = "grass" if r.done_pct == 100 else "amber" if r.slipped == 0 else "tomato"
        cards.append(
            rx.box(
                rx.flex(
                    rx.text(r.version, size="2", weight="medium", color=rx.color("gray", 12)),
                    rx.badge(
                        f"{r.slipped} просрочено" if r.slipped else "В срок",
                        color_scheme="tomato" if r.slipped else "grass",
                        variant="soft",
                        size="1",
                    ),
                    justify="between",
                    align="center",
                    margin_bottom="10px",
                ),
                rx.box(
                    rx.box(
                        height="10px",
                        background=rx.color(color, 7),
                        border_radius="var(--radius-full)",
                        width=f"{r.done_pct}%",
                    ),
                    height="10px",
                    background=rx.color("gray", 4),
                    border_radius="var(--radius-full)",
                    overflow="hidden",
                    margin_bottom="6px",
                ),
                rx.text(
                    f"{r.done} из {r.total} задач завершено ({r.done_pct}%)",
                    size="1",
                    color=rx.color("gray", 9),
                ),
                background="white",
                border=f"{BORDER} {rx.color('gray', 4)}",
                border_radius="var(--radius-3)",
                padding=SPACING["md"],
                flex="1",
            )
        )

    return rx.flex(*cards, gap=SPACING["md"], width="100%")


# ---------------------------------------------------------------------------
# Activation Funnel
# ---------------------------------------------------------------------------

def _activation_funnel() -> rx.Component:
    max_val = _FUNNEL[0][1]
    steps = []
    for i, (label, pct) in enumerate(_FUNNEL):
        drop = _FUNNEL[i - 1][1] - pct if i > 0 else 0
        color = "teal" if pct >= 60 else "amber" if pct >= 40 else "tomato"
        steps.append(
            rx.flex(
                rx.text(
                    label,
                    size="2",
                    color=rx.color("gray", 12),
                    style={"width": "220px", "flex_shrink": "0"},
                ),
                progress_bar(round(100 * pct / max_val), color, 6, height="28px"),
                rx.text(
                    f"{pct}%",
                    size="2",
                    weight="medium",
                    color=rx.color(color, 11),
                    style={"width": "44px", "text_align": "right", "flex_shrink": "0"},
                ),
                rx.text(
                    f"−{drop}%" if drop else "",
                    size="1",
                    color=rx.color("tomato", 9),
                    style={"width": "44px", "text_align": "right", "flex_shrink": "0"},
                ),
                align="center",
                gap=SPACING["sm"],
                width="100%",
            )
        )

    return rx.box(
        rx.callout(
            "Воронка симулирована — реальная аналитика активации пользователей отсутствует. "
            "Заменить на данные из product analytics при наличии.",
            icon="triangle-alert",
            color_scheme="amber",
            variant="soft",
            size="1",
            margin_bottom=SPACING["md"],
        ),
        rx.flex(
            rx.text("Шаг", size="1", weight="medium", color=rx.color("gray", 9),
                    style={"width": "220px", "flex_shrink": "0"}),
            rx.box(flex="1"),
            rx.text("% от установок", size="1", weight="medium", color=rx.color("gray", 9),
                    style={"width": "44px"}),
            rx.text("Отток", size="1", weight="medium", color=rx.color("gray", 9),
                    style={"width": "44px"}),
            gap=SPACING["sm"],
            margin_bottom="8px",
        ),
        rx.flex(*steps, direction="column", gap="10px"),
        padding=SPACING["md"],
        background=rx.color("gray", 2),
        border_radius="var(--radius-3)",
        width="100%",
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def growth_tab() -> rx.Component:
    issues = load_issues()
    s = growth_stats(issues)
    exp_rows = growth_experiments(issues)
    releases = growth_releases(issues)

    b_win_pct = round(100 * s.b_wins / s.total_experiments) if s.total_experiments else 0

    return rx.box(

        # ── Growth Health ──────────────────────────────────────────────────
        section_header(
            "Growth Health",
            subtitle="Экспериментирование и поставка · Growth squad метрики",
            action=data_source_badge("mock"),
        ),
        stat_card_row(
            stat_card(
                "Экспериментов запущено",
                str(s.total_experiments),
                tooltip="Общее число задач типа experiment в GROWTH squad за весь период MVP.",
            ),
            stat_card(
                "Вариант B победил",
                f"{s.b_wins} ({b_win_pct}%)",
                tooltip='Доля экспериментов, где result = "Вариант B лучше". Цель — как минимум 30%+ win rate, иначе гипотезы слабые.',
            ),
            stat_card(
                "Scale / Kill / Running",
                f"▲{s.b_wins} / ✕{s.inconclusive} / ▶{s.pending}",
                tooltip="Решения по экспериментам: Scale — внедряем вариант B, Kill — останавливаем, Running — ещё идёт.",
            ),
            stat_card(
                "Задач завершено",
                f"{s.tasks_done}/{s.tasks_total}",
                tooltip="Готово / всего задач в GROWTH squad. Включает эксперименты и поддерживающие таски.",
            ),
            stat_card(
                "Story Points поставлено",
                str(s.sp_done),
                tooltip="Сумма Story Points завершённых задач GROWTH squad — показатель объёма поставки команды роста.",
            ),
        ),

        rx.box(height=SPACING["xl"]),

        # ── Experiment Log ─────────────────────────────────────────────────
        section_header(
            "Experiment Log",
            subtitle="A/B эксперименты · Контроль vs Тест · результаты",
            action=data_source_badge("mock"),
        ),
        _experiment_table(exp_rows),

        rx.box(height=SPACING["xl"]),

        # ── Release Delivery ───────────────────────────────────────────────
        section_header(
            "Release Delivery",
            subtitle="Выполнение плана по релизам · просроченные задачи",
            action=data_source_badge("mock"),
        ),
        _release_delivery(releases),

        rx.box(height=SPACING["xl"]),

        # ── Activation Funnel ──────────────────────────────────────────────
        section_header(
            "Activation Funnel",
            subtitle="Воронка активации пользователей пайплайна ⚠️ симуляция",
            action=data_source_badge("mock"),
        ),
        _activation_funnel(),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
