"""
Analytics · PA tab — Product Analyst view.

Sections:
1. Funnel Analysis    — activation funnel, drop-off highlights, segment comparison
2. Cohort Retention   — week×week retention heatmap
3. A/B Significance   — experiments with n, conversion rate, p-value, CI, verdict
4. SQL Showcase       — pre-written ClickHouse queries with result tables (static mock)
"""

import math

import reflex as rx

from ..tokens import SPACING, BORDER
from ..components import section_header, data_source_badge, stat_card, stat_card_row, table_container, progress_bar
from ..data.adapter import load_issues
from ..data.metrics import growth_experiments

# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

# Funnel: (step_label, all_users_pct, new_users_pct, returning_pct)
_FUNNEL: list[tuple[str, int, int, int]] = [
    ("Установил пайплайн",    100, 100, 100),
    ("Первый запуск",          78,  72,  91),
    ("Первая заметка создана", 61,  54,  82),
    ("10+ заметок",            44,  36,  68),
    ("Регулярное использование (7d)", 29, 21, 52),
]

# Cohort: rows = weeks since signup (0..7), cols = weeks retained (0..7)
# Value = retention % at that week relative to week-0
_COHORT_WEEKS = ["W0", "W1", "W2", "W3", "W4", "W5", "W6", "W7"]
_COHORT_DATA: list[list[int | None]] = [
    [100, 68, 54, 44, 38, 33, 29, 26],   # cohort acquired W0
    [100, 65, 51, 41, 35, 30, 27, None],
    [100, 71, 56, 46, 39, 34, None, None],
    [100, 69, 53, 43, 37, None, None, None],
    [100, 73, 58, 47, None, None, None, None],
    [100, 67, 52, None, None, None, None, None],
    [100, 74, None, None, None, None, None, None],
    [100, None, None, None, None, None, None, None],
]
_COHORT_LABELS = [f"Когорта {i+1}" for i in range(8)]

# SQL showcase: (title, description, sql, columns, rows)
_SQL_CASES: list[tuple[str, str, str, list[str], list[list[str]]]] = [
    (
        "Воронка активации по неделям",
        "Считаем долю пользователей, дошедших до каждого шага, разбитую по неделям регистрации.",
        """\
SELECT
    toStartOfWeek(registered_at)       AS cohort_week,
    countIf(first_run_at IS NOT NULL)  AS ran_pipeline,
    countIf(first_note_at IS NOT NULL) AS created_note,
    count()                            AS total,
    round(100 * countIf(first_note_at IS NOT NULL)
               / count(), 1)           AS activation_pct
FROM user_events
GROUP BY cohort_week
ORDER BY cohort_week DESC
LIMIT 12""",
        ["cohort_week", "total", "ran_pipeline", "created_note", "activation_pct"],
        [
            ["2026-06-23", "412", "321", "251", "60.9%"],
            ["2026-06-16", "398", "302", "229", "57.5%"],
            ["2026-06-09", "441", "348", "278", "63.0%"],
            ["2026-06-02", "389", "298", "231", "59.4%"],
        ],
    ),
    (
        "Retention по когортам (W1 / W4 / W8)",
        "Ключевые retention-точки: W1 (первая неделя), W4 (привычка), W8 (стабильность).",
        """\
SELECT
    cohort_week,
    count()                          AS cohort_size,
    round(100 * countIf(active_w1)
               / count(), 1)         AS w1_retention,
    round(100 * countIf(active_w4)
               / count(), 1)         AS w4_retention,
    round(100 * countIf(active_w8)
               / count(), 1)         AS w8_retention
FROM user_cohorts
GROUP BY cohort_week
ORDER BY cohort_week DESC
LIMIT 8""",
        ["cohort_week", "cohort_size", "w1_ret %", "w4_ret %", "w8_ret %"],
        [
            ["2026-06-23", "412", "68%", "38%", "—"],
            ["2026-06-16", "398", "65%", "35%", "—"],
            ["2026-06-09", "441", "71%", "39%", "26%"],
            ["2026-06-02", "389", "69%", "37%", "24%"],
        ],
    ),
    (
        "Top-10 фич по влиянию на W4 retention",
        "Какие фичи использовали пользователи с retention ≥ W4, которых нет у ушедших.",
        """\
SELECT
    feature_name,
    round(100 * countIf(retained_w4) / count(), 1) AS retained_pct,
    round(100 * countIf(NOT retained_w4) / count(), 1) AS churned_pct,
    retained_pct - churned_pct                    AS lift
FROM feature_usage
JOIN user_cohorts USING (user_id)
GROUP BY feature_name
HAVING count() > 100
ORDER BY lift DESC
LIMIT 10""",
        ["feature_name", "retained %", "churned %", "lift"],
        [
            ["weekly_digest",   "74%", "31%", "+43"],
            ["tag_system",      "68%", "29%", "+39"],
            ["graph_view",      "61%", "26%", "+35"],
            ["mobile_app",      "58%", "28%", "+30"],
            ["search_advanced", "52%", "24%", "+28"],
        ],
    ),
]


# ---------------------------------------------------------------------------
# Dynamic SQL case for A/B (uses same computed data as A/B section)
# ---------------------------------------------------------------------------

def _ab_sql_case(exp_rows) -> tuple:
    done = [r for r in exp_rows if r.status == "Done"][:3]
    keys_str = ", ".join(f"'{r.key}'" for r in done) or "'—'"
    sql = f"""\
SELECT
    experiment_key,
    variant,
    count()                          AS n,
    round(100 * countIf(converted)
               / count(), 2)         AS conversion_pct,
    -- p-value через Mann-Whitney (реализован UDF)
    mannWhitneyUTest(converted)[2]   AS p_value
FROM ab_events
WHERE experiment_key IN ({keys_str})
  AND status = 'Done'
GROUP BY experiment_key, variant
ORDER BY experiment_key, variant"""
    rows = []
    for r in done:
        p_label = f"{r.p_value:.4f}" if r.p_value < 0.0001 else f"{r.p_value:.4f}"
        rows.append([r.key, "A", str(r.n_a), f"{r.conv_a * 100:.1f}%", "—"])
        rows.append([r.key, "B", str(r.n_b), f"{r.conv_b * 100:.1f}%", p_label])
    return (
        "A/B результаты с p-value",
        "Конверсия и статистическая значимость для завершённых экспериментов.",
        sql,
        ["experiment_key", "variant", "n", "conversion %", "p_value"],
        rows,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pvalue_badge(p: float, status: str) -> rx.Component:
    if status == "Running":
        return rx.badge("Running", color_scheme="blue", variant="outline", size="1")
    label = "<0.0001" if p < 0.0001 else f"{p:.4f}"
    if p < 0.05:
        return rx.badge(f"p={label} ✓", color_scheme="grass", variant="solid", size="1")
    return rx.badge(f"p={label}", color_scheme="tomato", variant="soft", size="1")


def _lift_badge(conv_a: float, conv_b: float, status: str) -> rx.Component:
    if status == "Running":
        return rx.text("—", size="2", color=rx.color("gray", 9))
    lift = round((conv_b - conv_a) / conv_a * 100, 1)
    color = "grass" if lift > 0 else "tomato"
    sign = "+" if lift > 0 else ""
    return rx.badge(f"{sign}{lift}%", color_scheme=color, variant="soft", size="1")


def _ci_text(conv: float, n: int) -> str:
    """95% confidence interval for a proportion (Wald approximation)."""
    if n == 0:
        return "—"
    z = 1.96
    margin = z * math.sqrt(conv * (1 - conv) / n)
    lo = max(0, conv - margin)
    hi = min(1, conv + margin)
    return f"{lo*100:.1f}–{hi*100:.1f}%"


# ---------------------------------------------------------------------------
# Section 1 — Funnel Analysis
# ---------------------------------------------------------------------------

def _funnel_section() -> rx.Component:
    max_all = _FUNNEL[0][1]

    rows = []
    for i, (label, all_pct, new_pct, ret_pct) in enumerate(_FUNNEL):
        drop = _FUNNEL[i-1][1] - all_pct if i > 0 else 0
        bar_color = "teal" if all_pct >= 60 else "amber" if all_pct >= 40 else "tomato"

        rows.append(
            rx.box(
                # Step label + drop-off
                rx.flex(
                    rx.text(f"{i+1}. {label}", size="2", weight="medium",
                            color=rx.color("gray", 12),
                            style={"min_width": "280px", "flex_shrink": "0"}),
                    rx.text(
                        f"−{drop}% отток" if drop else "Старт",
                        size="1",
                        color=rx.color("tomato", 10) if drop >= 15 else rx.color("gray", 9),
                        weight="medium" if drop >= 15 else "regular",
                        style={"min_width": "100px", "flex_shrink": "0"},
                    ),
                    align="center",
                    gap=SPACING["md"],
                    margin_bottom="6px",
                ),
                # Bars: All / New / Returning
                rx.flex(
                    # All users bar
                    rx.flex(
                        rx.text("Все", size="1", color=rx.color("gray", 9),
                                style={"width": "80px", "flex_shrink": "0"}),
                        progress_bar(round(100 * all_pct / max_all), bar_color, 6, height="14px"),
                        rx.text(f"{all_pct}%", size="2", weight="bold",
                                color=rx.color(bar_color, 11),
                                style={"width": "40px", "text_align": "right", "flex_shrink": "0"}),
                        align="center", gap="8px", width="100%",
                    ),
                    # New users bar
                    rx.flex(
                        rx.text("Новые", size="1", color=rx.color("gray", 9),
                                style={"width": "80px", "flex_shrink": "0"}),
                        progress_bar(round(100 * new_pct / max_all), "iris", 5, height="10px"),
                        rx.text(f"{new_pct}%", size="1", color=rx.color("iris", 11),
                                style={"width": "40px", "text_align": "right", "flex_shrink": "0"}),
                        align="center", gap="8px", width="100%",
                    ),
                    # Returning users bar
                    rx.flex(
                        rx.text("Вернувш.", size="1", color=rx.color("gray", 9),
                                style={"width": "80px", "flex_shrink": "0"}),
                        progress_bar(round(100 * ret_pct / max_all), "teal", 5, height="10px"),
                        rx.text(f"{ret_pct}%", size="1", color=rx.color("teal", 11),
                                style={"width": "40px", "text_align": "right", "flex_shrink": "0"}),
                        align="center", gap="8px", width="100%",
                    ),
                    direction="column", gap="4px", flex="1",
                ),
                padding=SPACING["md"],
                background=rx.color("tomato", 2) if drop >= 15 else "white",
                border=f"{BORDER} {rx.color('tomato', 4) if drop >= 15 else rx.color('gray', 3)}",
                border_radius="var(--radius-3)",
                border_left=f"4px solid {rx.color('tomato', 7)}" if drop >= 15 else f"4px solid {rx.color(bar_color, 5)}",
            )
        )

    # Legend
    legend = rx.flex(
        rx.flex(rx.box(width="12px", height="12px", background=rx.color("teal", 6),
                       border_radius="2px"),
                rx.text("Все пользователи", size="1", color=rx.color("gray", 10)),
                align="center", gap="6px"),
        rx.flex(rx.box(width="12px", height="10px", background=rx.color("iris", 5),
                       border_radius="2px"),
                rx.text("Новые (первая неделя)", size="1", color=rx.color("gray", 10)),
                align="center", gap="6px"),
        rx.flex(rx.box(width="12px", height="10px", background=rx.color("teal", 5),
                       border_radius="2px"),
                rx.text("Вернувшиеся", size="1", color=rx.color("gray", 10)),
                align="center", gap="6px"),
        rx.flex(rx.box(width="12px", height="12px",
                       background=rx.color("tomato", 3),
                       border=f"{BORDER} {rx.color('tomato', 5)}",
                       border_radius="2px"),
                rx.text("Критический отток (≥15%)", size="1", color=rx.color("tomato", 10)),
                align="center", gap="6px"),
        gap=SPACING["lg"],
        wrap="wrap",
        margin_bottom=SPACING["md"],
    )

    return rx.box(legend, rx.flex(*rows, direction="column", gap=SPACING["sm"]), width="100%")


# ---------------------------------------------------------------------------
# Section 2 — Cohort Retention heatmap
# ---------------------------------------------------------------------------

def _retention_color(val: int | None) -> str:
    if val is None:
        return rx.color("gray", 3)
    if val >= 60:
        return rx.color("teal", 8)
    if val >= 40:
        return rx.color("teal", 5)
    if val >= 25:
        return rx.color("amber", 5)
    if val >= 10:
        return rx.color("amber", 3)
    return rx.color("tomato", 3)


def _cohort_section() -> rx.Component:
    cell_w = "72px"
    cell_h = "36px"

    # Header row
    header = rx.flex(
        rx.box(width="110px", flex_shrink="0"),  # label column
        *[
            rx.box(
                rx.text(w, size="1", weight="medium", color=rx.color("gray", 9),
                        text_align="center"),
                width=cell_w, flex_shrink="0",
            )
            for w in _COHORT_WEEKS
        ],
        align="center",
        gap="2px",
        margin_bottom="2px",
    )

    data_rows = []
    for cohort_label, row_vals in zip(_COHORT_LABELS, _COHORT_DATA):
        cells = []
        for val in row_vals:
            bg = _retention_color(val)
            cells.append(
                rx.box(
                    rx.text(
                        f"{val}%" if val is not None else "—",
                        size="1",
                        weight="medium" if val == 100 else "regular",
                        color=rx.color("gray", 12) if val and val >= 25 else rx.color("gray", 9),
                        text_align="center",
                    ),
                    width=cell_w,
                    height=cell_h,
                    flex_shrink="0",
                    background=bg,
                    border_radius="var(--radius-1)",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                )
            )

        data_rows.append(
            rx.flex(
                rx.text(cohort_label, size="1", color=rx.color("gray", 10),
                        style={"width": "110px", "flex_shrink": "0"}),
                *cells,
                align="center",
                gap="2px",
            )
        )

    # Colour scale legend
    scale = rx.flex(
        rx.text("Retention:", size="1", color=rx.color("gray", 9)),
        *[
            rx.flex(
                rx.box(width="16px", height="14px", background=c,
                       border_radius="2px"),
                rx.text(label, size="1", color=rx.color("gray", 10)),
                align="center", gap="4px",
            )
            for c, label in [
                (rx.color("teal", 8), "≥60%"),
                (rx.color("teal", 5), "40–60%"),
                (rx.color("amber", 5), "25–40%"),
                (rx.color("amber", 3), "10–25%"),
                (rx.color("tomato", 3), "<10%"),
            ]
        ],
        gap=SPACING["sm"],
        align="center",
        wrap="wrap",
        margin_bottom=SPACING["md"],
    )

    return rx.box(
        scale,
        rx.callout(
            "Возвращающиеся пользователи удерживаются значительно лучше новых — "
            "W4 retention 52% vs 21%. Приоритет: улучшить onboarding для новых.",
            icon="lightbulb",
            color_scheme="teal",
            variant="soft",
            size="1",
            margin_bottom=SPACING["md"],
        ),
        rx.box(
            header,
            rx.flex(*data_rows, direction="column", gap="2px"),
            overflow_x="auto",
        ),
        width="100%",
    )


# ---------------------------------------------------------------------------
# Section 3 — A/B Significance
# ---------------------------------------------------------------------------

def _ab_section(exp_rows) -> rx.Component:
    COL = "80px 1fr 70px 70px 110px 110px 110px 100px"
    header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in ["Ключ", "Гипотеза", "n(A)", "n(B)", "Conv A (95% CI)",
                    "Conv B (95% CI)", "Lift", "p-value"]],
        columns=COL, gap=SPACING["sm"],
        padding=f"8px {SPACING['md']}", background=rx.color("gray", 2),
        border_radius="var(--radius-2) var(--radius-2) 0 0",
    )

    rows = []
    for idx, r in enumerate(exp_rows):
        sig = r.p_value < 0.05 and r.status == "Done"
        rows.append(rx.grid(
            rx.text(r.key, size="1", font_family="monospace",
                    color=rx.color("gray", 11)),
            rx.text(r.hypothesis, size="1", color=rx.color("gray", 12)),
            rx.text(str(r.n_a), size="1", color=rx.color("gray", 10)),
            rx.text(str(r.n_b), size="1", color=rx.color("gray", 10)),
            rx.text(_ci_text(r.conv_a, r.n_a), size="1", color=rx.color("gray", 10)),
            rx.text(_ci_text(r.conv_b, r.n_b), size="1",
                    color=rx.color("grass", 11) if sig and r.conv_b > r.conv_a
                    else rx.color("gray", 10)),
            _lift_badge(r.conv_a, r.conv_b, r.status),
            _pvalue_badge(r.p_value, r.status),
            columns=COL, gap=SPACING["sm"], align="center",
            padding=f"10px {SPACING['md']}",
            background=rx.color("grass", 1) if sig else (
                "white" if idx % 2 == 0 else rx.color("gray", 1)),
            border_top=f"{BORDER} {rx.color('gray', 3)}",
            border_left=f"3px solid {rx.color('grass', 6)}" if sig
                        else "3px solid transparent",
        ))

    note = rx.callout(
        "p < 0.05 = статистически значимый результат при α=0.05. "
        "CI рассчитан методом Wald (p ± 1.96·√(p(1-p)/n)). "
        "⚠️ Mock-данные — в проде подключить реальный A/B фреймворк (Statsig / GrowthBook).",
        icon="info",
        color_scheme="gray",
        variant="soft",
        size="1",
        margin_top=SPACING["md"],
    )

    return rx.box(
        table_container(header, *rows),
        note,
        width="100%",
    )


# ---------------------------------------------------------------------------
# Section 4 — SQL Showcase
# ---------------------------------------------------------------------------

def _sql_block(title: str, description: str, sql: str,
               columns: list[str], rows: list[list[str]]) -> rx.Component:
    # Result table
    col_template = " ".join(["1fr"] * len(columns))
    tbl_header = rx.grid(
        *[rx.text(c, size="1", weight="medium", color=rx.color("gray", 9))
          for c in columns],
        columns=col_template, gap=SPACING["sm"],
        padding=f"6px {SPACING['sm']}",
        background=rx.color("gray", 2),
    )
    tbl_rows = [
        rx.grid(
            *[rx.text(cell, size="1",
                      font_family="monospace" if col in ("cohort_week", "experiment_key") else "inherit",
                      color=rx.color("gray", 11))
              for cell, col in zip(row, columns)],
            columns=col_template, gap=SPACING["sm"],
            padding=f"6px {SPACING['sm']}",
            background="white" if i % 2 == 0 else rx.color("gray", 1),
            border_top=f"{BORDER} {rx.color('gray', 3)}",
        )
        for i, row in enumerate(rows)
    ]

    return rx.box(
        rx.flex(
            rx.text(title, size="2", weight="bold", color=rx.color("gray", 12)),
            rx.text(description, size="1", color=rx.color("gray", 10)),
            direction="column", gap="2px", margin_bottom=SPACING["sm"],
        ),
        # SQL code block
        rx.box(
            rx.code_block(
                sql,
                language="sql",
                font_size="12px",
                can_copy=True,
            ),
            margin_bottom=SPACING["sm"],
        ),
        # Result preview
        rx.box(
            rx.text("▶ Результат (mock)", size="1", weight="medium",
                    color=rx.color("gray", 9), margin_bottom="4px"),
            table_container(tbl_header, *tbl_rows),
        ),
        padding=SPACING["md"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        width="100%",
    )


# ---------------------------------------------------------------------------
# Main tab
# ---------------------------------------------------------------------------

def analytics_tab() -> rx.Component:
    issues = load_issues()
    exp_rows = growth_experiments(issues)
    sig_exp = sum(1 for r in exp_rows if r.p_value < 0.05 and r.status == "Done")
    w1_vals = [row[1] for row in _COHORT_DATA if row[1] is not None]
    avg_w1 = round(sum(w1_vals) / len(w1_vals)) if w1_vals else 0
    drops = [(label, _FUNNEL[i-1][1] - pct) for i, (label, pct, _, _) in enumerate(_FUNNEL) if i > 0]
    worst_step, worst_drop = max(drops, key=lambda x: x[1])

    return rx.box(

        # ── Stat cards ────────────────────────────────────────────────────────
        stat_card_row(
            stat_card("A/B экспериментов", str(len(exp_rows)),
                      tooltip="Всего экспериментов типа experiment в Jira-моке."),
            stat_card("Значимых результатов",
                      f"{sig_exp}/{len(exp_rows)}",
                      tooltip="Эксперименты с p < 0.05 — статистически значимый результат."),
            stat_card("W1 retention (avg)", f"{avg_w1}%",
                      tooltip="Средний retention на первой неделе по всем когортам."),
            stat_card("Крит. отток воронки",
                      f"−{worst_drop}% · шаг 4",
                      tooltip=f"Наибольший единовременный отток: {worst_step}"),
        ),

        rx.box(height=SPACING["xl"]),

        # ── Funnel Analysis ───────────────────────────────────────────────────
        section_header(
            "Funnel Analysis",
            subtitle="Активация пользователей · сегменты: новые vs вернувшиеся · красный = критический отток",
            action=data_source_badge("mock"),
        ),
        _funnel_section(),

        rx.box(height=SPACING["xl"]),

        # ── Cohort Retention ──────────────────────────────────────────────────
        section_header(
            "Cohort Retention",
            subtitle="Удержание пользователей по когортам · неделя регистрации × неделя после",
            action=data_source_badge("mock"),
        ),
        _cohort_section(),

        rx.box(height=SPACING["xl"]),

        # ── A/B Significance ──────────────────────────────────────────────────
        section_header(
            "A/B Significance",
            subtitle="Эксперименты · конверсия, 95% CI, p-value · зелёный = значимый результат",
            action=data_source_badge("mock"),
        ),
        _ab_section(exp_rows),

        rx.box(height=SPACING["xl"]),

        # ── SQL Showcase ──────────────────────────────────────────────────────
        section_header(
            "SQL Showcase",
            subtitle="ClickHouse-запросы PA · статические примеры с результатами",
            action=data_source_badge("mock"),
        ),
        rx.callout(
            "Реальное подключение к ClickHouse не реализовано — запросы и результаты статические. "
            "В production: подключить через ClickHouse HTTP API или dbt.",
            icon="triangle-alert",
            color_scheme="amber",
            variant="soft",
            size="1",
            margin_bottom=SPACING["md"],
        ),
        rx.flex(
            *[_sql_block(title, desc, sql, cols, rows)
              for title, desc, sql, cols, rows in _SQL_CASES + [_ab_sql_case(exp_rows)]],
            direction="column",
            gap=SPACING["lg"],
            width="100%",
        ),

        padding=SPACING["xl"],
        max_width="1100px",
        margin="0 auto",
    )
