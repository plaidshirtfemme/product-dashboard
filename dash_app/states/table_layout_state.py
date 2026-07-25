"""
Общий стейт раскладки таблиц (DASH-114).

Один стейт на ВСЕ таблицы дашборда: пользовательский порядок колонок и их ширина,
персистентно в браузере (rx.LocalStorage, ключ = table_id).

Дефолты живут не в стейте, а в модульном реестре `_REG` (заполняется
`register_table()` при импорте страницы с таблицей). Стейт держит ТОЛЬКО оверрайды
пользователя, поэтому изменение кода (новая колонка) не ломает сохранённую
раскладку: eff_* мёржит сохранённое с актуальным набором колонок.

Тип rx.LocalStorage — только str, поэтому раскладку сериализуем в JSON.

Единый минимум ширины: он объявлен в реестре (`min_w` колонки) и применяется И на
клиенте (JS не даёт увести направляющую левее), И здесь при коммите. Раньше было три
разных порога (JS / dataclass / `max(50, …)`) — колонка «отпрыгивала» от того места,
где её отпустили (находка код-ревью 25.07).
"""

from __future__ import annotations

import json

import reflex as rx

# ---------------------------------------------------------------------------
# Модульный реестр колонок (не стейт): table_id → {col_id: (default_w, min_w)}.
# Порядок колонок по умолчанию = порядок ключей (dict сохраняет вставку), поэтому
# отдельный реестр порядка не нужен — он был второй копией того же списка.
# ---------------------------------------------------------------------------

_REG: dict[str, dict[str, tuple[int, int]]] = {}


def register_table(table_id: str, cols: list[tuple[str, int, int]]) -> None:
    """Зарегистрировать колонки таблицы: список (col_id, default_width, min_width)."""
    new = {cid: (w, mw) for cid, w, mw in cols}
    old = _REG.get(table_id)
    if old is not None and set(old) != set(new):
        # Один table_id на две разные таблицы — раскладка одной затрёт другую, и
        # таблица отрендерится пустыми ячейками (rx.match уйдёт в fallback).
        # Не рушим приложение, но громко предупреждаем.
        print(
            f"[reorderable_table] ВНИМАНИЕ: table_id '{table_id}' уже "
            f"зарегистрирован с другим набором колонок "
            f"({sorted(set(old) ^ set(new))} расходятся). Дайте таблицам разные table_id."
        )
    _REG[table_id] = new


def default_order(table_id: str) -> list[str]:
    return list(_REG.get(table_id, {}))


def _merge_order(saved: list[str], default: list[str]) -> list[str]:
    """Сохранённый порядок, отфильтрованный до актуальных колонок + новые в хвост."""
    kept = [c for c in saved if c in default]
    kept += [c for c in default if c not in kept]
    return kept or list(default)


# ---------------------------------------------------------------------------
# Стейт
# ---------------------------------------------------------------------------

class TableLayoutState(rx.State):

    # Персистентные оверрайды пользователя (JSON: {table_id: [...]} / {table_id: {col: px}})
    orders_raw: str = rx.LocalStorage("{}", name="rt_orders")
    widths_raw: str = rx.LocalStorage("{}", name="rt_widths")

    # ── парсинг сохранённого (обычные хелперы, не rx.var: их результат
    # мутируется обработчиками, а derived-state мутировать нельзя) ───────────
    def _saved_orders(self) -> dict[str, list[str]]:
        return _loads_dict(self.orders_raw)

    def _saved_widths(self) -> dict[str, dict[str, int]]:
        return _loads_dict(self.widths_raw)

    # ── эффективная раскладка для ВСЕХ зарегистрированных таблиц ────────────
    # dict[table_id] → результат; компонент индексирует по литеральному table_id.
    @rx.var
    def eff_orders(self) -> dict[str, list[str]]:
        saved = _loads_dict(self.orders_raw)
        return {
            tid: _merge_order(saved.get(tid) or [], list(cols))
            for tid, cols in _REG.items()
        }

    @rx.var
    def eff_widths(self) -> dict[str, dict[str, int]]:
        saved = _loads_dict(self.widths_raw)
        out: dict[str, dict[str, int]] = {}
        for tid, cols in _REG.items():
            merged = {cid: w for cid, (w, _mw) in cols.items()}
            for cid, w in (saved.get(tid) or {}).items():
                if cid in cols:                      # неизвестные ключи не применяем
                    merged[cid] = max(int(w), cols[cid][1])
            out[tid] = merged
        return out

    @rx.var
    def customized(self) -> dict[str, bool]:
        """table_id → есть ли пользовательская правка (для показа кнопки сброса)."""
        o, w = _loads_dict(self.orders_raw), _loads_dict(self.widths_raw)
        return {tid: bool(o.get(tid) or w.get(tid)) for tid in _REG}

    # ── reorder: payload "table|src|tgt|side", side = before|after ──────────
    def commit_reorder(self, payload: str):
        parts = (payload or "").split("|")
        if len(parts) != 4:
            return
        table_id, src, tgt, side = parts
        if not src or not tgt or src == tgt or table_id not in _REG:
            return
        order = _merge_order(self._saved_orders().get(table_id) or [],
                             default_order(table_id))
        if src not in order or tgt not in order:
            return
        order.remove(src)
        idx = order.index(tgt) + (1 if side == "after" else 0)
        order.insert(idx, src)
        d = self._saved_orders()
        d[table_id] = order
        self.orders_raw = json.dumps(d)

    # ── resize: payload "table|col|width" ──────────────────────────────────
    def commit_width(self, payload: str):
        parts = (payload or "").split("|")
        if len(parts) != 3:
            return
        table_id, col_id, raw_w = parts
        cols = _REG.get(table_id)
        if not cols or col_id not in cols:            # не пишем мусорные ключи
            return
        try:
            new_w = max(int(float(raw_w)), cols[col_id][1])
        except (TypeError, ValueError):
            return
        d = self._saved_widths()
        d.setdefault(table_id, {})[col_id] = new_w
        self.widths_raw = json.dumps(d)

    # ── сброс раскладки одной таблицы ──────────────────────────────────────
    def reset_layout(self, table_id: str):
        o, w = self._saved_orders(), self._saved_widths()
        o.pop(table_id, None)
        w.pop(table_id, None)
        self.orders_raw = json.dumps(o)
        self.widths_raw = json.dumps(w)


def _loads_dict(raw: str) -> dict:
    try:
        d = json.loads(raw or "{}")
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}
