/*
 * Рантайм перетаскивания и ресайза колонок таблиц (DASH-114).
 * Подключается один раз через rx.App(head_components=[table_runtime()]) —
 * см. dash_app/components/reorderable_table.py.
 *
 * Почему отдельным файлом, а не инлайном: Reflex 0.9.x не отдаёт инлайн-скрипт в
 * DOM ни из дерева компонентов, ни из head_components (тег просто не появляется).
 * Статический ассет грузится браузером обычным путём и кэшируется, а объявление
 * остаётся ОДНО на всё приложение — в заголовке колонки только короткий вызов
 * (раньше полная копия ~2.9 КБ вставлялась в каждую колонку: шапка Issues весила
 * 91 КБ против 11 КБ тела).
 *
 * Обе процедуры возвращают Promise: фронтенд Reflex его awaits и передаёт
 * результат-строку в Python-колбэк (TableLayoutState.commit_*). Пустая строка =
 * «ничего не делать» (не тащили / отпустили там же).
 */

window.__rtCleanup = function (mv, done) {
  document.removeEventListener('pointermove', mv);
  document.removeEventListener('pointerup', done);
  document.removeEventListener('pointercancel', done);
  window.removeEventListener('blur', done);
  document.body.style.userSelect = '';
  document.body.style.cursor = '';
};

// Снятие захвата продублировано на pointercancel и blur — иначе drag «залипает»
// при потере фокуса окна.
window.__rtBind = function (mv, done) {
  document.addEventListener('pointermove', mv);
  document.addEventListener('pointerup', done);
  document.addEventListener('pointercancel', done);
  window.addEventListener('blur', done);
  document.body.style.userSelect = 'none';
};

/* Перестановка колонок. Возвращает "table|src|target|side", side = before|after:
   вставка только «перед» не давала поставить колонку в конец, а сброс на правого
   соседа был no-op. */
window.__rtReorder = function (tid, cid) {
  return new Promise(function (res) {
    var tbl = document.querySelector('[data-rt="' + tid + '"]');
    if (!tbl) { res(''); return; }
    var cells = Array.prototype.slice.call(tbl.querySelectorAll('th[data-col]'));
    // Рамки снимаем ОДИН раз: колонки не двигаются во время тяги. Раньше каждый
    // pointermove звал elementFromPoint и писал стили во все th → принудительный
    // reflow всей таблицы ~120 раз/с.
    var cols = cells.map(function (el) {
      var r = el.getBoundingClientRect();
      return { col: el.getAttribute('data-col'), el: el, l: r.left, r: r.right, mid: r.left + r.width / 2 };
    });
    var srcEl = null;
    cols.forEach(function (c) { if (c.col === cid) { srcEl = c.el; } });
    var startX = null, moved = false, tgt = null, side = 'before';
    function clear() { cols.forEach(function (c) { c.el.style.boxShadow = ''; }); }
    function pick(x) {
      for (var i = 0; i < cols.length; i++) { if (x >= cols[i].l && x <= cols[i].r) { return cols[i]; } }
      if (!cols.length) { return null; }
      return x < cols[0].l ? cols[0] : cols[cols.length - 1];
    }
    function mv(e) {
      if (startX === null) { startX = e.clientX; }
      if (Math.abs(e.clientX - startX) > 4) { moved = true; }
      if (!moved) { return; }
      var t = pick(e.clientX);
      if (!t) { return; }
      var s = e.clientX > t.mid ? 'after' : 'before';
      if (t === tgt && s === side) { return; }   // без DOM-записей, пока цель та же
      clear();
      tgt = t; side = s;
      if (srcEl) { srcEl.style.opacity = '0.45'; }
      if (t.col !== cid) {
        t.el.style.boxShadow = (s === 'before' ? 'inset 3px 0 0 0 ' : 'inset -3px 0 0 0 ') + 'var(--accent-9)';
      }
    }
    function done() {
      window.__rtCleanup(mv, done);
      if (srcEl) { srcEl.style.opacity = ''; }
      clear();
      res(moved && tgt && tgt.col !== cid ? tid + '|' + cid + '|' + tgt.col + '|' + side : '');
    }
    window.__rtBind(mv, done);
  });
};

/* Ресайз. Во время тяги двигается только направляющая линия, ширина применяется
   один раз на отпускание: live-resize перекладывал 118×16 ячеек с переносом
   текста на каждый mousemove. Возвращает "table|col|width". */
window.__rtResize = function (tid, cid, minw, labelPad) {
  return new Promise(function (res) {
    var th = document.querySelector('[data-rt="' + tid + '"] th[data-col="' + cid + '"]');
    if (!th) { res(''); return; }
    var r = th.getBoundingClientRect(), L = r.left;
    var lbl = th.querySelector('.rt-label');
    // Уже шапки не сужаем — иначе непонятно, почему колонка не сужается дальше.
    var minW = Math.max(minw, Math.ceil(lbl ? lbl.getBoundingClientRect().width : 0) + labelPad);
    var w0 = Math.round(r.width), w = w0, moved = false;
    var tblEl = th.closest('table'), tr = tblEl.getBoundingClientRect();
    var ln = document.createElement('div');
    ln.style.cssText = 'position:fixed;z-index:9999;width:2px;background:var(--accent-9);'
      + 'pointer-events:none;top:' + tr.top + 'px;height:' + tr.height + 'px;left:' + (L + w) + 'px;';
    document.body.appendChild(ln);
    document.body.style.cursor = 'col-resize';
    function mv(e) {
      var v = Math.round(e.clientX - L);
      if (v < minW) { v = minW; }
      if (v !== w0) { moved = true; }          // база — ширина на СТАРТЕ, не текущая:
      w = v;                                   // иначе дрожь «туда-обратно» писала
      ln.style.left = (L + v) + 'px';          // фантомный оверрайд
    }
    function done() {
      window.__rtCleanup(mv, done);
      if (ln.parentNode) { ln.parentNode.removeChild(ln); }
      // th.style.width НЕ пишем: ширину рисует стейт. Инлайн-стиль перебивал
      // стейт, из-за чего «Сбросить раскладку» не возвращал ширины до перезагрузки.
      res(moved ? tid + '|' + cid + '|' + w : '');
    }
    window.__rtBind(mv, done);
  });
};
