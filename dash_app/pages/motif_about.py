"""About project — Motif-режим: рабочий стол сборки истории команды (DASH-128).

Порядок разделов (ТЗ Guzel, мокап 15.07):
  About → Команда (карточки + личные банки) → JTBD → RACI → GOALS → Артефакты →
  Расписание (2 нед) → Факторы и история (таймлайн + сюжетные банки) →
  Дневники → Цитаты → Сценарий.

Фаза 1 (эта): структура, новые разделы, двухколоночная Команда (скроллится левый
блок карточек), скелет таймлайна с дорожками-банками и нижней дорожкой СПАЙНА.
Фазы 2-3 (далее): drag-n-drop строк банка на карточки и на таймлайн.

Интерактив сейчас: клик по ячейке банка → зелёная подсветка; клик по заголовку →
свернуть; выбор и свёрнутость персистятся (rx.LocalStorage).
"""
from __future__ import annotations

import reflex as rx

from ..tokens import SPACING, BORDER
from ..components import section_header
from ..data.motif_world import (
    ABOUT, CAST, BANKS, ARTIFACTS,
    SCHEDULE_CEREMONIES, SCHEDULE_WEEKS, SCHEDULE_COMMENTARY,
    SPINE, STORY_BANK_IDS, PERSONAL_BANK_IDS, TIMELINE_DAYS,
    GOALS_OKR, RACI, DIARIES, QUOTES, TRAITS_GROUPS, TRAITS_INDEX,
    GRADES, INVESTOR, MOTIF_MVP, MOTIF_SPRINT, A1_SCRIPT_FINAL, BACKSTORY_BRIEF,
)

_DIR_GLYPH = {"out": "→", "in": "←", "both": "↔"}
_DIR_COLOR = {"out": "teal", "in": "iris", "both": "amber"}
_BANK_BY_ID = {b["id"]: b for b in BANKS}

class _DragDiv(rx.el.Div):
    """<div> с drag-n-drop триггерами — Reflex 0.9.x не даёт их на стандартных компонентах."""

    on_drag_start: rx.EventHandler[lambda e: []]
    on_drag_over: rx.EventHandler[lambda e: []]
    on_drop: rx.EventHandler[lambda e: []]


_drag_div = _DragDiv.create


# Плоский текст строк банков (для чипов на карточках / блоков на таймлайне) — cell_id → текст
_PERSONAL_CELL_TEXT = {
    f"{bid}:{i}": (f"{cat} · {text}" if cat else text)
    for bid in PERSONAL_BANK_IDS
    for i, (cat, text) in enumerate(_BANK_BY_ID[bid]["cells"])
}
_STORY_CELL_TEXT = {
    f"{bid}:{i}": (f"{cat} · {text}" if cat else text)
    for bid in STORY_BANK_IDS
    for i, (cat, text) in enumerate(_BANK_BY_ID[bid]["cells"])
}
_CELL_ACCENT = {
    f"{bid}:{i}": _BANK_BY_ID[bid]["accent"]
    for bid in STORY_BANK_IDS
    for i in range(len(_BANK_BY_ID[bid]["cells"]))
}
_CARD_ROLE = {c["name"]: c["role"] for c in CAST}
# cid'ы банка ЛИЧНЫХ СОБЫТИЙ (только он даёт авто-блок на таймлайне при дропе на карточку)
_PERSONAL_EVENT_IDS = {f"personal:{i}"
                       for i in range(len(_BANK_BY_ID["personal"]["cells"]))}
_PERSONAL_ACCENT = _BANK_BY_ID["personal"]["accent"]
_N_DAYS = len(TIMELINE_DAYS)          # 14 (с выходными)
_COLW = 100.0 / _N_DAYS               # процент ширины на один день
_LANES_DEFAULT = 8
_LANES_MAX = 20

# Костяк A1 «Потеря арта» (под спайном; перенесено из раздела Сценарий)
_A1_BEATS = [
    "Бит 1 · Ставка — выкатить model-sheets v2 → поднять удержание → раунд + найм. "
    "Команда сообща задвигает safety-UX (историю версий) под сроком.",
    "Бит 2 · Нарастание — миграция под давлением, тонкое тест-покрытие; тихий фон без бэкап-UX.",
    "Бит 3 · Кризис — миграция побила проекты, у Нур и юзеров пропал арт; Ким хочет замять.",
    "Бит 4 · Развязка — blameless-постмортем, восстановление, человечный recovery-UX, "
    "радикальная прозрачность; на демо честность → доверие инвестора растёт.",
    "Бит 5 · Послевкусие — раунд открывается; version-history как принцип; storming→norming.",
]


def _day_label(i: int) -> str:
    """Индекс дня 0..13 → «Пн н.1» (с номером недели)."""
    lbl = TIMELINE_DAYS[i]["label"].replace(" 🔒", "")
    return f"{lbl} н.{i // 7 + 1}"


# ---------------------------------------------------------------------------
# State — выбор ячеек + свёрнутые блоки, персистентно в браузере
# ---------------------------------------------------------------------------

class MotifAboutState(rx.State):
    collapsed: str = rx.LocalStorage("")        # "sid,sid,…"
    dragging: str = ""                          # transient: "bank|cid"|"chip|card|cid"|"sbank|cid"|"move|ref"
    card_assignments: str = rx.LocalStorage("") # "card|cid,card|cid,…" (личный банк → карточка)
    timeline_items: str = rx.LocalStorage("")   # "kind|lane|ref|start|len,…"  kind s(story)/p(personal)

    @rx.var
    def collapsed_list(self) -> list[str]:
        return [x for x in self.collapsed.split(",") if x]

    @rx.var
    def assignments_map(self) -> dict[str, list[list[str]]]:
        """card_name → список [cell_id, текст] назначенных строк (для чипов на карточках)."""
        result: dict[str, list[list[str]]] = {c["name"]: [] for c in CAST}
        for entry in self.card_assignments.split(","):
            if not entry:
                continue
            card, _, cid = entry.partition("|")
            if card in result:
                result[card].append([cid, _PERSONAL_CELL_TEXT.get(cid, cid)])
        return result

    def _placed(self) -> dict:
        """lane_idx(int) → [kind, ref, start, len]. ref: story=cid, personal='card~cid'."""
        placed = {}
        for e in self.timeline_items.split(","):
            if not e:
                continue
            p = e.split("|")
            if len(p) != 5:
                continue
            kind, lane, ref, s, l = p
            placed[int(lane)] = [kind, ref, int(s), int(l)]
        return placed

    def _save_placed(self, placed: dict):
        self.timeline_items = ",".join(
            f"{v[0]}|{ln}|{v[1]}|{v[2]}|{v[3]}" for ln, v in placed.items())

    def _first_free_lane(self, placed: dict) -> int:
        occ = set(placed.keys())
        i = 0
        while i in occ and i < _LANES_MAX:
            i += 1
        return i

    def _n_lanes(self, occupied: set) -> int:
        max_idx = max(occupied) if occupied else -1
        return max(_LANES_DEFAULT, max_idx + 1)

    @rx.var
    def can_add_lane(self) -> bool:
        """Показать зону «+ новая дорожка»: все текущие заняты и есть запас до максимума."""
        occ = set(self._placed().keys())
        n = self._n_lanes(occ)
        return n < _LANES_MAX and all(i in occ for i in range(n))

    @rx.var
    def next_lane(self) -> int:
        return self._n_lanes(set(self._placed().keys()))

    @rx.var
    def layout_summary(self) -> str:
        """Читаемый текст всей раскладки (таймлайн + карточки) — для сборки сценария."""
        lines = ["=== ТАЙМЛАЙН (дорожки сверху вниз) ==="]
        placed = self._placed()
        if not placed:
            lines.append("(пусто)")
        for lane in sorted(placed.keys()):
            kind, ref, s, l = placed[lane]
            if kind == "p":
                card, _, cid = ref.partition("~")
                text = f"{card} — {_PERSONAL_CELL_TEXT.get(cid, cid)}"
            else:
                text = _STORY_CELL_TEXT.get(ref, ref)
            span = _day_label(s) if l == 1 else f"{_day_label(s)}–{_day_label(s + l - 1)}"
            lines.append(f"Дорожка {lane + 1}: «{text}» · {span} ({l} дн.)")
        lines += ["", "=== КАРТОЧКИ (черты + личные события) ==="]
        by_card: dict = {}
        for e in self.card_assignments.split(","):
            if not e:
                continue
            card, _, cid = e.partition("|")
            by_card.setdefault(card, []).append(_PERSONAL_CELL_TEXT.get(cid, cid))
        for c in CAST:
            items = by_card.get(c["name"], [])
            lines.append(f"{c['name']} ({c['role']}): " + (", ".join(items) if items else "—"))
        return "\n".join(lines)

    @rx.var
    def lanes(self) -> list[list]:
        """Дорожки: [lane, kind|'', ref, текст, accent, start, len].
        8 по умолчанию; лишних пустых нет — новая появляется только при дропе в зону «+ новая дорожка».
        Один фактор на дорожку."""
        placed = self._placed()
        occupied = set(placed.keys())
        n = self._n_lanes(occupied)
        rows = []
        for lane in range(n):
            if lane in placed:
                kind, ref, s, l = placed[lane]
                if kind == "p":
                    card, _, cid = ref.partition("~")
                    text = f"{card} · {_CARD_ROLE.get(card, '')} — {_PERSONAL_CELL_TEXT.get(cid, cid)}"
                    accent = _PERSONAL_ACCENT
                else:
                    text = _STORY_CELL_TEXT.get(ref, ref)
                    accent = _CELL_ACCENT.get(ref, "gray")
                rows.append([lane, kind, ref, text, accent, s, l])
            else:
                rows.append([lane, "", "", "", "gray", 0, 1])
        return rows

    # ── drag-n-drop: личный банк → карточка героя ──
    def start_drag_bank(self, cell_id: str):
        self.dragging = "bank|" + cell_id

    def start_drag_chip(self, card: str, cell_id: str):
        self.dragging = "chip|" + card + "|" + cell_id

    def drop_on_card(self, card: str):
        if self.dragging.startswith("bank|"):
            cid = self.dragging[5:]
            entry = card + "|" + cid
            items = [x for x in self.card_assignments.split(",") if x]
            if entry not in items:
                items.append(entry)
                self.card_assignments = ",".join(items)
            # личное СОБЫТИЕ → авто-блок на таймлайне (свободная дорожка, понедельник)
            if cid in _PERSONAL_EVENT_IDS:
                ref = card + "~" + cid
                placed = self._placed()
                if not any(v[1] == ref for v in placed.values()):
                    free = self._first_free_lane(placed)
                    if free < _LANES_MAX:
                        placed[free] = ["p", ref, 0, 1]
                        self._save_placed(placed)
        self.dragging = ""

    def drop_on_bank(self):
        """Чип с карточки обратно в банк = снять. Для личного события — снять и с таймлайна."""
        if self.dragging.startswith("chip|"):
            _, card, cid = self.dragging.split("|", 2)
            entry = card + "|" + cid
            items = [x for x in self.card_assignments.split(",") if x and x != entry]
            self.card_assignments = ",".join(items)
            ref = card + "~" + cid
            placed = {ln: v for ln, v in self._placed().items() if v[1] != ref}
            self._save_placed(placed)
        self.dragging = ""

    # ── drag-n-drop: сюжетный банк → дорожка таймлайна ──
    def start_drag_sbank(self, cell_id: str):
        self.dragging = "sbank|" + cell_id

    def start_drag_move(self, ref: str):
        self.dragging = "move|" + ref

    def drop_on_cell(self, lane: int, day: int):
        """Положить сюжетный фактор из банка / переместить блок на (дорожка, день).
        Один фактор на дорожку: занятую чужим — не трогаем."""
        d, self.dragging = self.dragging, ""
        n = len(TIMELINE_DAYS)
        placed = self._placed()
        if d.startswith("sbank|"):
            cid = d[6:]
            if lane in placed and placed[lane][1] != cid:
                return
            placed = {ln: v for ln, v in placed.items() if v[1] != cid}
            placed[lane] = ["s", cid, min(day, n - 1), 1]
            self._save_placed(placed)
        elif d.startswith("move|"):
            ref = d[5:]
            if lane in placed and placed[lane][1] != ref:
                return
            cur = next(((ln, v) for ln, v in placed.items() if v[1] == ref), None)
            if cur is None:
                return
            old_ln, v = cur
            del placed[old_ln]
            st = min(day, n - 1)
            placed[lane] = [v[0], ref, st, min(v[3], n - st)]
            self._save_placed(placed)

    def drop_on_story_bank(self):
        """Блок из таймлайна обратно в банк = снять. Личное событие — снять и с карточки."""
        if self.dragging.startswith("move|"):
            ref = self.dragging[5:]
            placed = self._placed()
            target = next(((ln, v) for ln, v in placed.items() if v[1] == ref), None)
            if target:
                old_ln, v = target
                del placed[old_ln]
                self._save_placed(placed)
                if v[0] == "p":
                    card, _, cid = ref.partition("~")
                    items = [x for x in self.card_assignments.split(",")
                             if x and x != f"{card}|{cid}"]
                    self.card_assignments = ",".join(items)
        self.dragging = ""

    def _resize_item(self, ref: str, delta: int):
        n = len(TIMELINE_DAYS)
        placed = self._placed()
        for ln, v in placed.items():
            if v[1] == ref:
                v[3] = max(1, min(v[3] + delta, n - v[2]))
        self._save_placed(placed)

    def grow_item(self, ref: str):
        self._resize_item(ref, 1)

    def shrink_item(self, ref: str):
        self._resize_item(ref, -1)

    # ── reorder дорожек (грип → дроп на грип другой дорожки) ──
    def start_drag_lane(self, lane: int):
        self.dragging = "lane|" + str(lane)

    def drop_reorder(self, target: int):
        if self.dragging.startswith("lane|"):
            src = int(self.dragging[5:])
            placed = self._placed()
            n = self._n_lanes(set(placed.keys()))
            if src != target and 0 <= src < n and 0 <= target < n:
                order = list(range(n))
                order.remove(src)
                order.insert(target, src)
                new_placed = {}
                for new_lane, old_lane in enumerate(order):
                    if old_lane in placed:
                        new_placed[new_lane] = placed[old_lane]
                self._save_placed(new_placed)
        self.dragging = ""

    def toggle_section(self, sid: str):
        items = [x for x in self.collapsed.split(",") if x]
        if sid in items:
            items.remove(sid)
        else:
            items.append(sid)
        self.collapsed = ",".join(items)


# ---------------------------------------------------------------------------
# Сворачиваемый блок (заголовок кликабелен)
# ---------------------------------------------------------------------------

def _section_head(sid: str, title: str, subtitle: str | None, accent: str) -> rx.Component:
    is_collapsed = MotifAboutState.collapsed_list.contains(sid)
    return rx.flex(
        rx.icon(
            rx.cond(is_collapsed, "chevron-right", "chevron-down"),
            size=18, color=rx.color(accent, 9),
        ),
        rx.text(title, size="4", weight="bold", color=rx.color("gray", 12)),
        rx.cond(
            subtitle is not None,
            rx.text(subtitle or "", size="1", color=rx.color("gray", 9)),
            rx.box(),
        ),
        gap="8px", align="center",
        cursor="pointer",
        on_click=MotifAboutState.toggle_section(sid),
        padding_y="8px",
        border_bottom=f"{BORDER} {rx.color(accent, 4)}",
        margin_bottom=SPACING["md"],
        flex_shrink="0",
    )


def _collapsible(sid: str, title: str, *children,
                 subtitle: str | None = None, accent: str = "gray") -> rx.Component:
    is_collapsed = MotifAboutState.collapsed_list.contains(sid)
    body = rx.cond(is_collapsed, rx.box(), rx.box(*children))
    return rx.box(_section_head(sid, title, subtitle, accent), body,
                  margin_bottom=SPACING["xl"])


def _vh_section(sid: str, title: str, body_row: rx.Component,
                subtitle: str | None = None, accent: str = "gray") -> rx.Component:
    """Секция высотой 100vh (когда развёрнута): тело растягивается flex:1/min-height:0,
    внутренние колонки скроллятся сами — без магических пикселей."""
    is_collapsed = MotifAboutState.collapsed_list.contains(sid)
    return rx.flex(
        _section_head(sid, title, subtitle, accent),
        rx.cond(is_collapsed, rx.box(), body_row),
        direction="column",
        height=rx.cond(is_collapsed, "auto", "100vh"),
        margin_bottom=SPACING["xl"],
    )


def _placeholder(text: str, accent: str = "amber") -> rx.Component:
    return rx.box(
        rx.flex(
            rx.icon("hammer", size=15, color=rx.color(accent, 9)),
            rx.text(text, size="2", color=rx.color("gray", 10), line_height="1.6"),
            gap="8px", align="start",
        ),
        padding=SPACING["md"],
        background=rx.color(accent, 2),
        border=f"{BORDER} {rx.color(accent, 4)}",
        border_radius="var(--radius-3)",
    )


def _bullets(items, accent: str = "teal") -> rx.Component:
    return rx.flex(
        *[rx.flex(
            rx.box(width="5px", height="5px", border_radius="50%",
                   background=rx.color(accent, 8), flex_shrink="0", margin_top="9px"),
            rx.text(t, size="2", color=rx.color("gray", 11), line_height="1.7"),
            gap="10px", align="start",
        ) for t in items],
        direction="column", gap="8px",
    )


# ---------------------------------------------------------------------------
# About project
# ---------------------------------------------------------------------------

def _fact(label: str, value: str, accent: str = "gray") -> rx.Component:
    return rx.box(
        rx.text(label, size="1", weight="bold",
                color=rx.color(accent, 11), text_transform="uppercase",
                letter_spacing="0.04em", margin_bottom="4px"),
        rx.text(value, size="2", color=rx.color("gray", 11), line_height="1.7"),
    )


def _about_block() -> rx.Component:
    return _collapsible(
        "about", "About project",
        rx.box(
            rx.text(ABOUT["name"], size="6", weight="bold", color=rx.color("teal", 11)),
            rx.text(ABOUT["tagline"], size="3", color=rx.color("gray", 11),
                    line_height="1.6", margin_top="4px", margin_bottom=SPACING["lg"]),
            rx.flex(
                _fact("Стадия", ABOUT["stage"], "teal"),
                _fact("Для кого", ABOUT["audience"], "teal"),
                _fact("Финансирование", ABOUT["financing"], "amber"),
                _fact("Ценности", ABOUT["values"], "grass"),
                direction="column", gap=SPACING["md"],
            ),
            rx.box(
                rx.flex(
                    rx.text("🔥", size="4"),
                    rx.box(
                        rx.text("Центральное напряжение", size="2", weight="bold",
                                color=rx.color("tomato", 11), margin_bottom="4px"),
                        rx.text(ABOUT["central_tension"], size="2",
                                color=rx.color("gray", 11), line_height="1.7"),
                    ),
                    gap="10px", align="start",
                ),
                padding=SPACING["lg"],
                background=rx.color("tomato", 2),
                border=f"{BORDER} {rx.color('tomato', 5)}",
                border_radius="var(--radius-3)",
                margin_top=SPACING["lg"],
            ),
            rx.flex(
                rx.box(
                    rx.text("В MVP уже есть", size="1", weight="bold", color=rx.color("teal", 11),
                            text_transform="uppercase", letter_spacing="0.04em", margin_bottom="4px"),
                    _bullets(MOTIF_MVP, "teal"),
                    flex="1", min_width="260px",
                ),
                rx.box(
                    rx.text("Спринт (2 недели)", size="1", weight="bold", color=rx.color("amber", 11),
                            text_transform="uppercase", letter_spacing="0.04em", margin_bottom="4px"),
                    _bullets(MOTIF_SPRINT, "amber"),
                    flex="1", min_width="260px",
                ),
                gap=SPACING["lg"], wrap="wrap", margin_top=SPACING["lg"],
            ),
        ),
        accent="teal",
    )


# ---------------------------------------------------------------------------
# Команда — карточки (скроллятся) + личные банки справа
# ---------------------------------------------------------------------------

# ── drag-n-drop примитивы ──

def _bank_dnd_row(bank_id: str, idx: int, cat: str | None, text: str,
                  story: bool) -> rx.Component:
    """Перетаскиваемая строка банка (raw div — Radix Box не даёт drag-триггеры).
    story=True → на таймлайн (start_drag_sbank), иначе → на карточку (start_drag_bank)."""
    cid = f"{bank_id}:{idx}"
    on_start = (MotifAboutState.start_drag_sbank(cid) if story
                else MotifAboutState.start_drag_bank(cid))
    return _drag_div(
        rx.text((f"{cat} · {text}" if cat else text),
                size="1", color=rx.color("gray", 11)),
        draggable=True,
        on_drag_start=on_start,
        style={
            "cursor": "grab", "padding": "4px 8px",
            "background": rx.color("gray", 1),
            "border": f"1px solid {rx.color('gray', 4)}",
            "borderRadius": "var(--radius-2)",
            "_hover": {"background": rx.color("gray", 3)},
        },
    )


def _personal_bank_block(bank: dict) -> rx.Component:
    rows = [_bank_dnd_row(bank["id"], i, cat, text, story=False)
            for i, (cat, text) in enumerate(bank["cells"])]
    list_box = _drag_div(
        *rows,
        on_drag_over=rx.prevent_default,
        on_drop=MotifAboutState.drop_on_bank(),
        style={"display": "flex", "flexDirection": "column", "gap": "4px",
               "padding": "4px", "minHeight": "40px"},
    )
    return _collapsible(
        bank["id"], bank["title"],
        rx.text(bank["note"], size="1", color=rx.color("gray", 9),
                line_height="1.5", margin_bottom="4px"),
        rx.text("↔ Тащи строку на карточку героя; строку с карточки — сюда, чтобы снять.",
                size="1", color=rx.color(bank["accent"], 10), margin_bottom="6px"),
        list_box,
        accent=bank["accent"],
    )


def _trait_chip(text: str) -> rx.Component:
    """Перетаскиваемая черта (по TRAITS_INDEX → cell_id 'traits:idx')."""
    idx = TRAITS_INDEX.get(text)
    if idx is None:
        return rx.box()
    return _drag_div(
        rx.text(text, size="1", color=rx.color("gray", 11),
                style={"whiteSpace": "nowrap", "overflow": "hidden", "textOverflow": "ellipsis"}),
        draggable=True,
        on_drag_start=MotifAboutState.start_drag_bank(f"traits:{idx}"),
        title=text,
        style={"cursor": "grab", "padding": "2px 7px", "flex": "1", "minWidth": "0",
               "background": rx.color("gray", 1),
               "border": f"1px solid {rx.color('gray', 4)}",
               "borderRadius": "var(--radius-2)",
               "_hover": {"background": rx.color("gray", 3)}},
    )


def _traits_bank_block(bank: dict) -> rx.Component:
    """Банк черт: группы, внутри — 2-столбцовые пары + списки-варианты + одиночки. Всё draggable."""
    acc = bank["accent"]
    groups = []
    for g in TRAITS_GROUPS:
        parts = [rx.text(g["name"], size="1", weight="bold",
                         color=rx.color(acc, 11), margin_top="8px", margin_bottom="3px")]
        for label, items in g["sublists"]:
            if label:
                parts.append(rx.text(label, size="1", color=rx.color("gray", 9)))
            parts.append(rx.flex(*[_trait_chip(t) for t in items],
                                 wrap="wrap", gap="3px", margin_bottom="3px"))
        for label, pairs in g["pairgroups"]:
            if label:
                parts.append(rx.text(label, size="1", color=rx.color("gray", 9)))
            for l, r in pairs:
                parts.append(rx.flex(_trait_chip(l), _trait_chip(r),
                                     gap="3px", width="100%", margin_bottom="2px"))
        if g["singles"]:
            parts.append(rx.text("прочее", size="1", color=rx.color("gray", 8), margin_top="2px"))
            parts.append(rx.flex(*[_trait_chip(t) for t in g["singles"]], wrap="wrap", gap="3px"))
        groups.append(rx.box(*parts, margin_bottom="6px"))
    list_box = _drag_div(
        *groups,
        on_drag_over=rx.prevent_default,
        on_drop=MotifAboutState.drop_on_bank(),
        style={"padding": "4px", "minHeight": "40px"},
    )
    return _collapsible(
        bank["id"], bank["title"],
        rx.text(bank["note"], size="1", color=rx.color("gray", 9),
                line_height="1.5", margin_bottom="4px"),
        rx.text("↔ Тащи черту на карточку героя; чип с карточки — сюда, чтобы снять.",
                size="1", color=rx.color(acc, 10), margin_bottom="6px"),
        list_box,
        accent=acc,
    )


def _card_chip(card: str, cell_id, text) -> rx.Component:
    """Назначенная строка на карточке — перетаскиваемая (обратно в банк = снять)."""
    return _drag_div(
        rx.text(text, size="1", color=rx.color("grass", 11)),
        draggable=True,
        on_drag_start=MotifAboutState.start_drag_chip(card, cell_id),
        style={"cursor": "grab", "padding": "2px 7px",
               "background": rx.color("grass", 3),
               "border": f"1px solid {rx.color('grass', 5)}",
               "borderRadius": "var(--radius-2)"},
    )


def _cast_card(m: dict, compact: bool = False) -> rx.Component:
    """Карточка персонажа — компонент с 2 вариантами (по аналогии с Figma variants):
    full (по умолчанию, Develop) — вся информация + чипсы назначенных черт из банков;
    compact (Define) — та же карточка, но чипсы скрыты (усечённый вид под персону)."""
    initials = m["name"][:2]
    return _drag_div(
        rx.flex(
            rx.box(
                rx.text(m["name"], size="3", weight="bold", color=rx.color("gray", 12)),
                rx.text(m["role"], size="1", weight="medium", color=rx.color("teal", 11)),
                rx.text(GRADES.get(m["name"], ""), size="1", color=rx.color("gray", 9),
                        margin_bottom="8px"),
                rx.text(m["character"], size="2", color=rx.color("gray", 11), line_height="1.6"),
                rx.text(m["image"], size="1", color=rx.color("gray", 9),
                        font_style="italic", margin_top="8px"),
                flex="1",
            ),
            rx.flex(
                rx.text(initials, size="4", weight="bold", color=rx.color("gray", 8)),
                width="64px", height="64px", flex_shrink="0",
                align="center", justify="center",
                background=rx.color("gray", 3),
                border=f"{BORDER} {rx.color('gray', 5)}",
                border_radius="var(--radius-3)",
            ),
            gap=SPACING["md"], align="start",
        ),
        rx.fragment() if compact else rx.flex(
            rx.foreach(
                MotifAboutState.assignments_map[m["name"]],
                lambda p: _card_chip(m["name"], p[0], p[1]),
            ),
            wrap="wrap", gap="4px", margin_top="8px",
        ),
        on_drag_over=rx.prevent_default,
        on_drop=MotifAboutState.drop_on_card(m["name"]),
        style={"padding": SPACING["md"], "background": rx.color("gray", 1),
               "border": f"{BORDER} {rx.color('gray', 4)}",
               "borderRadius": "var(--radius-3)"},
    )


def _team_cards_grid(compact: bool = False) -> rx.Component:
    """Общий грид карточек персонажей — единый источник для Develop (full) и Define (compact)."""
    return rx.grid(*[_cast_card(m, compact=compact) for m in CAST],
                    columns="3", gap=SPACING["md"], width="100%")


def _investor_card() -> rx.Component:
    return rx.box(
        rx.flex(
            rx.text(INVESTOR["name"], size="3", weight="bold", color=rx.color("amber", 11)),
            rx.badge("внешний стейкхолдер", color_scheme="amber", variant="soft", size="1"),
            gap="8px", align="center",
        ),
        rx.text(INVESTOR["role"], size="1", weight="medium", color=rx.color("amber", 11),
                margin_bottom="6px"),
        rx.text("Хочет: " + INVESTOR["wants"], size="2", color=rx.color("gray", 11),
                line_height="1.6"),
        rx.text(INVESTOR["character"], size="1", color=rx.color("gray", 10),
                line_height="1.6", margin_top="6px"),
        padding=SPACING["md"], margin_top=SPACING["md"],
        background=rx.color("amber", 2),
        border=f"{BORDER} {rx.color('amber', 5)}",
        border_radius="var(--radius-3)",
    )


def _team_block() -> rx.Component:
    left = rx.box(
        _team_cards_grid(),
        _investor_card(),
        flex="2", min_width="420px",
        overflow_y="auto", min_height="0", padding_right="6px",
    )
    right = rx.flex(
        rx.text("Личные банки — перетаскивай на карточки",
                size="1", color=rx.color("gray", 9), margin_bottom="4px", flex_shrink="0"),
        _traits_bank_block(_BANK_BY_ID["traits"]),
        _personal_bank_block(_BANK_BY_ID["personal"]),
        direction="column", flex="1", min_width="300px",
        overflow_y="auto", min_height="0",
    )
    body = rx.flex(
        left, right,
        gap=SPACING["lg"], align="stretch",
        flex="1", min_height="0", width="100%",
    )
    return _vh_section(
        "team", "Команда", body,
        subtitle="11 человек · ансамбль (обе колонки скроллятся)", accent="iris",
    )


# ---------------------------------------------------------------------------
# JTBD / RACI / GOALS
# ---------------------------------------------------------------------------

def _jtbd_block() -> rx.Component:
    return _collapsible(
        "jtbd", "JTBD",
        rx.text("Jobs To Be Done — ради чего юзеры «нанимают» Motif:",
                size="1", color=rx.color("gray", 9), margin_bottom="8px"),
        _bullets(ABOUT["jtbd"], "teal"),
        accent="teal",
    )


def _raci_block() -> rx.Component:
    header = rx.table.row(
        *[rx.table.column_header_cell(
            c, style={"font_size": "11px", "color": rx.color("gray", 9),
                      "text_transform": "uppercase"})
          for c in ["Активность", "R", "A", "C", "I"]]
    )
    rows = [
        rx.table.row(
            rx.table.cell(rx.text(x["act"], size="2", weight="medium")),
            rx.table.cell(rx.text(x["r"], size="1", color=rx.color("gray", 11))),
            rx.table.cell(rx.badge(x["a"], color_scheme="plum", variant="soft", size="1")),
            rx.table.cell(rx.text(x["c"], size="1", color=rx.color("gray", 10))),
            rx.table.cell(rx.text(x["i"], size="1", color=rx.color("gray", 10))),
        )
        for x in RACI
    ]
    return _collapsible(
        "raci", "RACI",
        rx.text("R — делает · A — отвечает (одна на строку) · C — консультирует · I — информируют.",
                size="1", color=rx.color("gray", 9), margin_bottom="8px"),
        rx.table.root(rx.table.header(header), rx.table.body(*rows),
                      variant="surface", size="1", width="100%"),
        accent="plum",
    )


def _goals_block() -> rx.Component:
    return _collapsible(
        "goals", "GOALS",
        rx.text("Objective", size="1", weight="bold", color=rx.color("teal", 11),
                text_transform="uppercase", letter_spacing="0.04em"),
        rx.text(GOALS_OKR["objective"], size="2", color=rx.color("gray", 11),
                line_height="1.6", margin_bottom="10px"),
        rx.text("Key Results", size="1", weight="bold", color=rx.color("teal", 11),
                text_transform="uppercase", letter_spacing="0.04em", margin_bottom="4px"),
        _bullets(GOALS_OKR["krs"], "teal"),
        rx.box(height="10px"),
        rx.text("Бизнес-контекст", size="1", weight="bold", color=rx.color("amber", 11),
                text_transform="uppercase", letter_spacing="0.04em", margin_bottom="4px"),
        _bullets(GOALS_OKR["business"], "amber"),
        accent="amber",
    )


# ---------------------------------------------------------------------------
# Артефакты обмена
# ---------------------------------------------------------------------------

# Роль контрагента по имени — из самих ARTIFACTS (DRY). Составные "Лея / Марко"
# разбиваем и мапим каждого; generic ("Вся команда", "Продукт") — сами себе роль.
_ART_ROLE_BY_NAME: dict[str, str] = {m["name"]: m["role"] for m in ARTIFACTS}


def _with_role_text(with_str: str) -> str:
    parts = [p.strip() for p in with_str.split("/")]
    return " / ".join(_ART_ROLE_BY_NAME.get(p, p) for p in parts)


def _spoke(sp: dict, compact: bool = False) -> rx.Component:
    role_text = _with_role_text(sp["with"])
    is_generic = role_text == sp["with"]   # generic-контрагент: имя == роль, не дублируем
    return rx.flex(
        rx.text(_DIR_GLYPH[sp["dir"]], size="3", weight="bold",
                color=rx.color(_DIR_COLOR[sp["dir"]], 10), width="20px",
                flex_shrink="0", text_align="center"),
        rx.text(sp["artifact"], size="2", color=rx.color("gray", 11), flex="1", min_width="0"),
        # full: бейдж имени; роль текстом (в обоих вариантах, у generic — только текст)
        rx.fragment() if compact else rx.badge(sp["with"], variant="soft",
                                               color_scheme="gray", size="1", flex_shrink="0"),
        rx.fragment() if (not compact and is_generic) else rx.text(
            role_text, size="1", color=rx.color("gray", 9),
            flex_shrink="0", text_align="right", max_width="180px",
        ),
        gap="8px", align="center", width="100%",
    )


def _artifact_hub(m: dict, compact: bool = False) -> rx.Component:
    """Хаб обмена артефактами — вариант компонента (как Figma variants):
    full (Motif/About) — с именами персонажей; compact (Dash/Discover) — только роли,
    имена (m['name'] и sp['with']) скрыты, т.к. Discover про домен, не про историю."""
    header = (
        rx.flex(
            rx.text(m["role"], size="2", weight="bold", color=rx.color(m["accent"], 11)),
            align="center", margin_bottom="10px",
        )
        if compact else
        rx.flex(
            rx.badge(m["name"], variant="solid", color_scheme=m["accent"], size="2"),
            rx.text(m["role"], size="1", color=rx.color("gray", 9)),
            gap="8px", align="center", margin_bottom="10px",
        )
    )
    return rx.box(
        header,
        rx.flex(*[_spoke(sp, compact) for sp in m["spokes"]], direction="column", gap="6px"),
        padding=SPACING["md"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color(m['accent'], 4)}",
        border_radius="var(--radius-3)",
    )


def _artifacts_block(compact: bool = False) -> rx.Component:
    intro = (
        "Кто какими артефактами обменивается по ролям: что роль даёт (→), получает (←) "
        "или двусторонне (↔)."
        if compact else
        "Кто чем обменивается: участник в центре, спицы — что даёт (→), "
        "получает (←) или двусторонне (↔) и с кем."
    )
    return _collapsible(
        "artifacts_compact" if compact else "artifacts", "Артефакты обмена",
        rx.text(intro, size="1", color=rx.color("gray", 9), margin_bottom=SPACING["md"]),
        rx.grid(*[_artifact_hub(m, compact) for m in ARTIFACTS],
                columns="2", gap=SPACING["md"], width="100%"),
        accent="violet",
    )


# ---------------------------------------------------------------------------
# Расписание — 2 недели (церемонии)
# ---------------------------------------------------------------------------

def _ceremony_chip(key: str) -> rx.Component:
    c = SCHEDULE_CEREMONIES[key]
    return rx.box(
        rx.text(c["name"], size="1", weight="medium", color=rx.color(c["color"], 11)),
        padding="3px 7px",
        background=rx.color(c["color"], 3),
        border=f"{BORDER} {rx.color(c['color'], 5)}",
        border_radius="var(--radius-2)",
        margin_bottom="4px",
    )


def _sched_day(day: dict) -> rx.Component:
    is_protected = "🔒" in day["day"]
    return rx.box(
        rx.text(day["day"], size="1", weight="bold",
                color=rx.color("gray", 9 if not is_protected else 7),
                margin_bottom="6px"),
        rx.cond(
            len(day["items"]) == 0,
            rx.text("—", size="1", color=rx.color("gray", 6)),
            rx.box(*[_ceremony_chip(k) for k in day["items"]]),
        ),
        padding=SPACING["sm"],
        background=rx.color("gray", 2 if not is_protected else 3),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-2)",
        flex="1", min_width="120px",
    )


def _sched_week(week: dict) -> rx.Component:
    return rx.box(
        rx.text(week["label"], size="2", weight="bold",
                color=rx.color("blue", 11), margin_bottom="8px"),
        rx.flex(*[_sched_day(d) for d in week["days"]], gap="8px", wrap="wrap"),
        margin_bottom=SPACING["md"],
    )


def _schedule_block() -> rx.Component:
    why = _collapsible(
        "schedule_why", "Почему так составлено",
        rx.box(
            _bullets(SCHEDULE_COMMENTARY, "blue"),
            padding=SPACING["lg"],
            background=rx.color("blue", 2),
            border=f"{BORDER} {rx.color('blue', 4)}",
            border_radius="var(--radius-3)",
        ),
        accent="blue",
    )
    return _collapsible(
        "schedule", "Расписание команды · 2 недели",
        *[_sched_week(w) for w in SCHEDULE_WEEKS],
        why,
        accent="blue",
    )


# ---------------------------------------------------------------------------
# Факторы и история — таймлайн (скелет Фазы 1) + сюжетные банки
# ---------------------------------------------------------------------------

def _tl_daycell(lane_idx, i: int) -> rx.Component:
    """Ячейка (дорожка, день) — drop-цель. lane_idx — Var (индекс дорожки)."""
    kind = TIMELINE_DAYS[i]["kind"]
    bg = rx.color("gray", 4 if kind == "weekend" else (3 if kind == "protected" else 2))
    return _drag_div(
        on_drag_over=rx.prevent_default,
        on_drop=MotifAboutState.drop_on_cell(lane_idx, i),
        style={"flex": "1", "background": bg,
               "borderRight": ("none" if i == _N_DAYS - 1
                               else f"1px solid {rx.color('gray', 5)}")},
    )


def _tl_block(item) -> rx.Component:
    """Блок-фактор: абс. позиция по start/len, цвет от банка (accent-Var), −/＋, перетаскиваемый."""
    ref, text, accent, start, length = item[2], item[3], item[4], item[5], item[6]
    return _drag_div(
        rx.text(text, size="1", weight="bold",
                style={"whiteSpace": "nowrap", "overflow": "hidden",
                       "textOverflow": "ellipsis", "flex": "1",
                       "color": rx.color(accent, 11)}),
        rx.el.button("−", on_click=MotifAboutState.shrink_item(ref),
                     style={"cursor": "pointer", "padding": "0 5px", "fontWeight": "bold",
                            "background": "transparent", "border": "none",
                            "color": rx.color(accent, 11)}),
        rx.el.button("＋", on_click=MotifAboutState.grow_item(ref),
                     style={"cursor": "pointer", "padding": "0 5px", "fontWeight": "bold",
                            "background": "transparent", "border": "none",
                            "color": rx.color(accent, 11)}),
        draggable=True,
        on_drag_start=MotifAboutState.start_drag_move(ref),
        title=text,   # нативная подсказка при hover — полное имя фактора
        style={"position": "absolute", "top": "2px", "bottom": "2px",
               "left": (start.to(float) * _COLW).to_string() + "%",
               "width": (length.to(float) * _COLW).to_string() + "%",
               "background": rx.color(accent, 4),
               "borderWidth": "1px", "borderStyle": "solid",
               "borderColor": rx.color(accent, 7),
               "borderRadius": "var(--radius-2)", "padding": "1px 4px",
               "cursor": "grab", "overflow": "hidden", "zIndex": "2",
               "display": "flex", "alignItems": "center", "gap": "2px"},
    )


def _lane_handle(lane) -> rx.Component:
    """Грип дорожки: drag-источник + drop-цель reorder (перетащить дорожку и бросить на грип другой)."""
    return _drag_div(
        rx.text("⋮⋮", size="1", color=rx.color("gray", 9),
                style={"pointerEvents": "none", "lineHeight": "1", "userSelect": "none"}),
        draggable=True,
        on_drag_start=MotifAboutState.start_drag_lane(lane),
        on_drag_over=rx.prevent_default,
        on_drop=MotifAboutState.drop_reorder(lane),
        title="Перетащить дорожку (бросить на грип другой)",
        style={"width": "16px", "flexShrink": "0", "cursor": "grab",
               "display": "flex", "alignItems": "center", "justifyContent": "center",
               "background": rx.color("gray", 3), "borderRadius": "var(--radius-1)"},
    )


def _tl_row(item) -> rx.Component:
    """Дорожка: [грип][14 ячеек-дней (drop-цели) + блок, если занята]."""
    lane = item[0]
    cells = rx.box(
        rx.flex(*[_tl_daycell(lane, i) for i in range(_N_DAYS)],
                width="100%", height="28px", align_items="stretch"),
        rx.cond(item[1] != "", _tl_block(item), rx.box()),
        position="relative", flex="1", min_width="0",
    )
    return rx.flex(
        _lane_handle(lane), cells,
        gap="2px", align="stretch", width="100%", margin_bottom="2px",
    )


def _tl_addzone() -> rx.Component:
    """Тонкая зона «+ новая дорожка» — видна только когда все дорожки заняты (can_add_lane)."""
    cells = rx.box(
        rx.flex(*[_tl_daycell(MotifAboutState.next_lane, i) for i in range(_N_DAYS)],
                width="100%", height="16px", align_items="stretch", opacity="0.55"),
        rx.el.div("＋ бросить фактор сюда для новой дорожки",
                  style={"position": "absolute", "left": "6px", "top": "1px",
                         "fontSize": "10px", "color": rx.color("gray", 8),
                         "pointerEvents": "none"}),
        position="relative", flex="1", min_width="0",
    )
    return rx.cond(
        MotifAboutState.can_add_lane,
        rx.flex(
            rx.box(width="16px", flex_shrink="0"),   # спейсер под грип
            cells,
            gap="2px", align="stretch", width="100%", margin_top="2px",
        ),
        rx.box(),
    )


def _timeline_lanes() -> rx.Component:
    return rx.box(
        rx.foreach(MotifAboutState.lanes, _tl_row),
        _tl_addzone(),
        width="100%",
    )


def _story_bank_block(bank: dict) -> rx.Component:
    rows = [_bank_dnd_row(bank["id"], i, cat, text, story=True)
            for i, (cat, text) in enumerate(bank["cells"])]
    list_box = _drag_div(
        *rows, on_drag_over=rx.prevent_default,
        on_drop=MotifAboutState.drop_on_story_bank(),
        style={"display": "flex", "flexDirection": "column", "gap": "4px",
               "padding": "4px", "minHeight": "40px"},
    )
    return _collapsible(
        bank["id"], bank["title"],
        rx.text(bank["note"], size="1", color=rx.color("gray", 9),
                line_height="1.5", margin_bottom="4px"),
        rx.text("↔ Тащи строку на дорожку этого банка в таймлайне; блок из таймлайна сюда — снять.",
                size="1", color=rx.color(bank["accent"], 10), margin_bottom="6px"),
        list_box,
        accent=bank["accent"],
    )


def _spine_track() -> rx.Component:
    """Куски спайна с ИНДИВИДУАЛЬНЫМИ длинами (абс. позиция по дням; неравные)."""
    segs = [
        rx.box(
            rx.text(s["name"], size="1", weight="bold",
                    color=rx.color(s["color"], 11), text_align="center",
                    style={"whiteSpace": "nowrap", "overflow": "hidden",
                           "textOverflow": "ellipsis"}),
            style={"position": "absolute", "top": "0", "bottom": "0",
                   "left": f"{s['start'] * _COLW}%", "width": f"{s['len'] * _COLW}%",
                   "background": rx.color(s["color"], 4),
                   "border": f"1px solid {rx.color(s['color'], 7)}",
                   "borderRadius": "var(--radius-2)", "display": "flex",
                   "alignItems": "center", "justifyContent": "center"},
        )
        for s in SPINE
    ]
    return rx.box(*segs, position="relative", width="100%", height="26px", margin_top="8px")


def _timeline_daxis() -> rx.Component:
    """Ось дней СНИЗУ — 14 подписей, выходные затенены, границы дней видны."""
    labels = []
    for i, d in enumerate(TIMELINE_DAYS):
        is_wknd = d["kind"] == "weekend"
        labels.append(rx.box(
            rx.text(d["label"], size="1", weight="bold",
                    color=rx.color("gray", 8 if is_wknd else 10), text_align="center"),
            flex="1", padding_y="3px",
            background=rx.color("gray", 3) if is_wknd else "transparent",
            border_right=("none" if i == _N_DAYS - 1
                          else f"1px solid {rx.color('gray', 5)}"),
        ))
    return rx.flex(
        *labels, width="100%", margin_top="4px",
        border=f"1px solid {rx.color('gray', 5)}",
        border_radius="var(--radius-2)", overflow="hidden",
    )


def _yaxis_label() -> rx.Component:
    """Вертикальная подпись оси Y — «нити»."""
    return rx.box(
        rx.text("нити", size="1", weight="bold", color=rx.color("gray", 9),
                style={"writingMode": "vertical-rl", "transform": "rotate(180deg)"}),
        width="20px", flex_shrink="0",
        display="flex", align_items="center", justify_content="center",
    )


def _freytag_caption() -> rx.Component:
    return rx.text(
        "Классическая драматическая дуга / пирамида Фрайтага "
        "(экспозиция → нарастание → кульминация → спад → развязка)",
        size="1", color=rx.color("gray", 9), font_style="italic", margin_top="6px",
    )


def _a1_beats_block() -> rx.Component:
    """Компактный костяк A1 — под спайном, чтобы влезал с таймлайном в один экран."""
    return rx.box(
        rx.text("Костяк A1 «Потеря арта» (ансамблевая плетёнка со спайном):",
                size="1", weight="bold", color=rx.color("gray", 11),
                margin_top="18px", margin_bottom="2px"),
        rx.flex(
            *[rx.text(b, size="1", color=rx.color("gray", 11), line_height="1.35")
              for b in _A1_BEATS],
            direction="column", gap="1px",
        ),
    )


def _timeline() -> rx.Component:
    return rx.box(
        rx.flex(
            _yaxis_label(),
            _timeline_lanes(),
            gap="4px", align="stretch", width="100%",
        ),
        rx.box(
            _spine_track(),
            _timeline_daxis(),
            _freytag_caption(),
            _a1_beats_block(),
            margin_left="42px",   # нити(20)+gap(4)+грип(16)+gap(2) — выровнять с ячейками дней
        ),
    )


def _layout_export() -> rx.Component:
    """Панель «Раскладка текстом» — читаемый дамп раскладки (для сценария), можно копировать."""
    return _collapsible(
        "layout_export", "📋 Раскладка текстом (для сценария)",
        rx.text("Выдели и скопируй (или заскринь) и пришли мне — соберу сценарий по дням. "
                "Отражает всё, что ты разложила (включая короткие 1-дневные факторы).",
                size="1", color=rx.color("gray", 9), margin_bottom="6px"),
        rx.box(
            rx.text(MotifAboutState.layout_summary,
                    style={"whiteSpace": "pre-wrap", "fontFamily": "monospace",
                           "fontSize": "12px", "userSelect": "text"}),
            padding=SPACING["md"],
            background=rx.color("gray", 2),
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
        ),
        accent="gray",
    )


def _factors_block() -> rx.Component:
    left = rx.box(
        _timeline(),
        flex="1", min_width="0",
    )
    right = rx.flex(
        rx.text("Сюжетные банки — перетаскивай на таймлайн",
                size="2", weight="bold", color=rx.color("gray", 12),
                margin_bottom="6px", flex_shrink="0"),
        *[_story_bank_block(_BANK_BY_ID[bid]) for bid in STORY_BANK_IDS],
        direction="column", flex_shrink="0", width="240px",
        overflow_y="auto", min_height="0",
    )
    body = rx.flex(
        left, right,
        gap=SPACING["lg"], align="stretch",
        flex="1", min_height="0", width="100%",
    )
    return _vh_section("factors", "Факторы и история", body, accent="grass")


# ---------------------------------------------------------------------------
# Дневники / Цитаты / Сценарий
# ---------------------------------------------------------------------------

def _diaries_block() -> rx.Component:
    subs = [
        _collapsible(f"diary_{i}", d["who"],
                     _bullets(d["entries"], "cyan"), accent="cyan")
        for i, d in enumerate(DIARIES)
    ]
    return _collapsible(
        "diaries", "Дневники",
        rx.text("Черновик — поменяется под финальный сценарий A1 и раскладку факторов. "
                "По одному сворачиваемому дневнику на роль (пока — PM).",
                size="1", color=rx.color("gray", 9), margin_bottom="8px"),
        *subs,
        accent="cyan",
    )


def _quote_card(q: dict) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.badge(q["name"], variant="soft", color_scheme="pink", size="1"),
            rx.text(q["role"], size="1", color=rx.color("gray", 9)),
            gap="8px", align="center", margin_bottom="4px",
        ),
        rx.text("« " + q["quote"] + " »", size="2", color=rx.color("gray", 11),
                font_style="italic", line_height="1.5"),
        padding=SPACING["md"],
        background=rx.color("gray", 1),
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
    )


def _quotes_block() -> rx.Component:
    return _collapsible(
        "quotes", "Цитаты",
        rx.text("Черновик — уточним под черты героев и финальный сценарий.",
                size="1", color=rx.color("gray", 9), margin_bottom="8px"),
        rx.grid(*[_quote_card(q) for q in QUOTES],
                columns="2", gap=SPACING["md"], width="100%"),
        accent="pink",
    )


def _backstory_block() -> rx.Component:
    rows = [
        rx.flex(
            rx.text(b["name"], size="2", weight="bold", color=rx.color("iris", 11),
                    width="80px", flex_shrink="0"),
            rx.text(b["text"], size="2", color=rx.color("gray", 11), line_height="1.6", flex="1"),
            gap="10px", align="start",
            padding_y="6px",
            border_bottom=f"{BORDER} {rx.color('gray', 3)}",
        )
        for b in BACKSTORY_BRIEF
    ]
    return _collapsible(
        "backstory", "Бэкстори",
        rx.text("Кратко: мотивация · почему тут · где живёт/заземляется (полное — в world-bible §2N).",
                size="1", color=rx.color("gray", 9), margin_bottom="8px"),
        *rows,
        accent="iris",
    )


def _script_block() -> rx.Component:
    rows = [
        rx.flex(
            rx.text(day, size="1", weight="bold", color=rx.color("grass", 11),
                    width="170px", flex_shrink="0"),
            rx.text(text, size="2", color=rx.color("gray", 11), line_height="1.6", flex="1"),
            gap="10px", align="start",
            padding_y="6px",
            border_bottom=f"{BORDER} {rx.color('gray', 3)}",
        )
        for day, text in A1_SCRIPT_FINAL
    ]
    return _collapsible(
        "script", "Сценарий · A1 «Потеря арта» (финал, по раскладке Guzel)",
        rx.text("Ансамблевая плетёнка со спайном: главный A1 + слои (переезд Дэна, выгорание Леи, "
                "удачи, награда Нура). Причинная цепочка: техдолг → слабый QA → миграция (бэкенд-дыра).",
                size="1", color=rx.color("gray", 9), margin_bottom="8px"),
        *rows,
        accent="grass",
    )


# ---------------------------------------------------------------------------
# Вкладка
# ---------------------------------------------------------------------------

def motif_about_tab() -> rx.Component:
    # Инструменты дизайн-процесса (карточки команды, JTBD, RACI, карта артефактов,
    # интерактивный воркбенч) переехали в Discover/Define/Develop (аккордеон Design,
    # решение Guzel 20.07) — эта вкладка теперь чистый нарратив про Motif.
    # Наполнение "как должно быть для самой команды" — отдельная задача, не сегодня.
    return rx.box(
        section_header(
            "About project",
            subtitle="Команда Motif · история проекта",
        ),
        _about_block(),
        _goals_block(),
        _artifacts_block(),          # полный вариант (с именами персонажей) — история Motif
        _schedule_block(),
        _diaries_block(),
        _quotes_block(),
        _backstory_block(),
        _script_block(),
        padding=SPACING["xl"],
        max_width="1240px",
        margin="0 auto",
    )
