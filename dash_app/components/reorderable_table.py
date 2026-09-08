"""
reorderable_table — переиспользуемая таблица с перетаскиванием и ресайзом колонок
(DASH-114). Раскладка (порядок + ширина) персистится на клиенте через
TableLayoutState (rx.LocalStorage), по одному ключу на table_id.

Модель: колонки = Column(id, label, cell, width); строки — реактивный Var
(list[dict]). Рендер data-driven: rx.foreach(порядок) → rx.match(id).

DnD — POINTER-события, НЕ HTML5 drag (решение DASH-114 + ресёрч: dnd-kit /
TanStack / Atlassian Pragmatic DnD). Нативный DnD внутри <table>/<th> не работает
(хотя тот же паттерн живой в div-таймлайне motif_about), а draggable-заголовок
дрался за события с грипом ресайза.

Устройство (переработано после код-ревью 25.07):
- ДВЕ JS-процедуры объявлены ОДИН раз в module-level rx.script как
  window.__rtReorder / __rtResize; в заголовке колонки — только короткий вызов
  через rx.call_script. Раньше полная копия ~2.9 КБ вставлялась в КАЖДУЮ колонку
  (шапка Issues весила 91 КБ против 11 КБ тела).
- Идентификаторы уходят в JS через json.dumps → кавычка/бэкслеш в id не ломает скрипт.
- Ширину колонки рисует ТОЛЬКО стейт. JS во время тяги двигает направляющую линию и
  НЕ пишет th.style.width: инлайн-стиль перебивал стейт, из-за чего «Сбросить
  раскладку» не возвращал ширины до перезагрузки.
- Вставка при reorder — before/after по тому, в какой половине заголовка отпустили.
  Только before не давал поставить колонку в конец, а drop на правого соседа был no-op.
- Рамки заголовков кэшируются на pointerdown, подсветка меняется только при смене
  цели: раньше каждый pointermove писал стили во все th и звал elementFromPoint →
  принудительный reflow всей таблицы (~120 раз/с).
- Минимум ширины объявлен в Column.min_width и применяется и в JS, и при коммите
  (раньше три разных порога, колонка «отпрыгивала» от места отпускания).
- Ресайз больших таблиц — направляющая линия, ширина применяется на отпускание:
  live-resize перекладывал 118×16 ячеек с переносом текста на каждый mousemove.
- НИКАКОГО requestAnimationFrame: он не тикает в фоновых вкладках и оставлял захват
  «залипшим». Снятие захвата продублировано на pointercancel + window.blur.

table-layout: fixed нельзя отдать через style у rx.table.root — Reflex/Radix кладут
props на внешний <div>, а реальный <table> остаётся auto (проверено в браузере).
Поэтому правило вешается CSS-ом на .rt-TableRootTable внутри [data-rt].
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

import reflex as rx

from ..tokens import SPACING, BORDER, STATE
from ..states.table_layout_state import TableLayoutState, register_table

# Ширина зоны захвата ресайза (грип) — она же зазор справа у ярлыка заголовка.
_GRIP_W = 9
# Запас к измеренной ширине ярлыка при расчёте минимума (padding ячейки + грип).
_LABEL_PAD = 26


# ---------------------------------------------------------------------------
# CSS: применяется к РЕАЛЬНОМУ <table> внутри Radix-обёртки + константные стили
# ячеек/заголовков (раньше инлайн-объект на каждую из ~1900 ячеек → Emotion
# сериализовал их заново на каждый рендер).
# ---------------------------------------------------------------------------

_RT_CSS = f"""
[data-rt] .rt-TableRootTable {{ table-layout: fixed; width: max-content; min-width: 100%; }}
.rt-cell {{ overflow: hidden; white-space: normal; word-break: break-word; vertical-align: top; }}
.rt-head {{ position: relative; overflow: hidden; user-select: none; vertical-align: middle; }}
.rt-grab {{ cursor: grab; width: 100%; height: 100%; padding-right: {_GRIP_W}px;
           overflow: hidden; display: flex; align-items: center; }}
.rt-grip {{ position: absolute; top: 0; right: 0; height: 100%; width: {_GRIP_W}px;
           cursor: col-resize; user-select: none; z-index: 2; touch-action: none; }}
.rt-grip:hover {{ background: var(--accent-6); }}
.rt-label {{ font-size: 11px; color: var(--gray-10); text-transform: uppercase;
            letter-spacing: 0.03em; white-space: nowrap; }}
"""

# ---------------------------------------------------------------------------
# Описание колонки
# ---------------------------------------------------------------------------

class _PointerDiv(rx.el.Div):
    """<div> с on_pointer_down — Reflex 0.9.x не даёт pointer-триггеры на базовых
    компонентах (есть только on_mouse_down и Radix-специфичный
    on_pointer_down_outside). Тот же приём, что _DragDiv в pages/motif_about.py.

    Почему именно pointer, а не mouse: на тач-экране эмулированный mousedown
    приходит ПОСЛЕ pointerup, поэтому слушатели навешивались на уже завершённый
    жест — захват «залипал», а следующий тап резолвил старое обещание и
    переставлял колонку, которую никто не трогал (находка код-ревью 25.07).
    """

    on_pointer_down: rx.EventHandler[lambda e: []]


_pointer_div = _PointerDiv.create


@dataclass
class Column:
    id: str
    label: str
    cell: Callable[[Any], rx.Component]      # row_var -> содержимое ячейки (без rx.table.cell)
    width: int = 120                          # дефолтная ширина, px
    min_width: int = 44                       # ниже неё ресайз не пускает


def table_runtime() -> rx.Component:
    """JS-рантайм перетаскивания/ресайза — подключать в rx.App(head_components=[…]).

    Код живёт в assets/reorderable_table.js, а не инлайном: Reflex 0.9.x не отдаёт
    инлайн-скрипт в DOM ни из дерева компонентов, ни из head_components (проверено —
    тег просто не появляется, window.__rtReorder остаётся undefined). Статический
    ассет грузится обычным путём и кэшируется, объявление одно на всё приложение.

    Тег — именно `rx.el.script` (обычный DOM-элемент), НЕ `rx.script`: последний
    возвращает Helmet-компонент и в head_components не даёт тега в DOM (проверено).
    """
    return rx.el.script(src="/reorderable_table.js")


def _js_call(fn: str, *args) -> str:
    """Короткий вызов рантайм-функции; аргументы через json.dumps (кавычки безопасны)."""
    return f"window.{fn}(" + ",".join(json.dumps(a) for a in args) + ")"


def reorderable_table(
    table_id: str,
    columns: list[Column],
    rows,                                      # Var[list[dict]]
) -> rx.Component:
    """Собрать таблицу с pointer-DnD перестановкой и ресайзом колонок."""
    register_table(table_id, [(c.id, c.width, c.min_width) for c in columns])
    order = TableLayoutState.eff_orders[table_id]
    widths = TableLayoutState.eff_widths[table_id]

    # ── заголовок одной колонки ────────────────────────────────────────────
    def _header(c: Column) -> rx.Component:
        return rx.table.column_header_cell(
            _pointer_div(
                rx.el.span(c.label, class_name="rt-label"),
                class_name="rt-grab",
                on_pointer_down=rx.call_script(
                    _js_call("__rtReorder", table_id, c.id),
                    callback=TableLayoutState.commit_reorder,
                ),
                title="Потяните заголовок, чтобы поменять порядок колонок",
            ),
            _pointer_div(
                class_name="rt-grip",
                on_pointer_down=rx.call_script(
                    _js_call("__rtResize", table_id, c.id, c.min_width, _LABEL_PAD),
                    callback=TableLayoutState.commit_width,
                ),
                title="Потяните границу, чтобы изменить ширину колонки",
            ),
            custom_attrs={"data-col": c.id},
            class_name="rt-head",
            style={"width": widths[c.id].to_string() + "px",
                   "min_width": f"{c.min_width}px"},
        )

    def _switch(builder: Callable[[Column], rx.Component], fallback: rx.Component):
        """rx.match по id колонки → её вариант ячейки/заголовка."""
        return lambda cid: rx.match(cid, *[(c.id, builder(c)) for c in columns], fallback)

    header = rx.table.header(
        rx.table.row(rx.foreach(order, _switch(_header, rx.table.column_header_cell())))
    )

    def _body_row(row) -> rx.Component:
        return rx.table.row(
            rx.foreach(
                order,
                _switch(lambda c: rx.table.cell(c.cell(row), class_name="rt-cell"),
                        rx.table.cell()),
            ),
            style={"_hover": {"background": STATE["hover-bg-subtle"]}},
        )

    reset = rx.cond(
        TableLayoutState.customized[table_id],
        rx.button(
            rx.icon("rotate-ccw", size=12), "Сбросить раскладку",
            size="1", variant="ghost", color_scheme="gray",
            on_click=TableLayoutState.reset_layout(table_id),
        ),
        rx.fragment(),
    )

    return rx.box(
        rx.el.style(_RT_CSS),
        rx.flex(reset, justify="end", width="100%",
                margin_bottom=SPACING["xs"], min_height="26px"),
        rx.box(
            rx.table.root(
                header,
                rx.table.body(rx.foreach(rows, _body_row)),
                variant="surface",
                size="1",
            ),
            custom_attrs={"data-rt": table_id},
            width="100%",
            overflow_x="auto",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
        ),
        width="100%",
    )
