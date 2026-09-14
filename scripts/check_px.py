#!/usr/bin/env python
"""Приёмка DASH-158: число литералов px не растёт.

Запуск из корня проекта:
    python scripts/check_px.py              # проверить
    python scripts/check_px.py --report     # + разбивка по назначению и файлам
    python scripts/check_px.py --self-test  # проверить сам прибор на известных ответах
    python scripts/check_px.py --set-base   # переписать отметку под текущее число

Код возврата: 0 — не выросло, 1 — выросло, 2 — прибор не прошёл самопроверку.

ЧТО СЧИТАЕТСЯ. Любой строковый литерал, содержащий число с `px`, — включая
составные: "1px solid ...", "8px 0", тени, grid-шаблоны. Прежний счёт 575 брал
только литералы вида ровно "16px" и не видел 143 места, в том числе все,
где литерал смешан с токеном (padding=f"10px {SPACING['sm']}").
"""
import argparse, collections, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "dash_app"
EXCLUDE = {"jira_mock_raw.py", "sprint_calendar.py"}   # файлы данных, не UI
BASELINE = 718                                          # замер 14.09.2026

# литерал с числом+px; кавычки не пересекают перевод строки
PX = re.compile(r'["\'][^"\'\n]*?\d+(?:\.\d+)?px[^"\'\n]*?["\']')
PROP = re.compile(r'([a-z_]+)\s*=\s*f?$')
DICT = re.compile(r'["\']([a-zA-Z_]+)["\']\s*:\s*f?$')

OTSTUPY = {"padding", "margin", "gap", "row_gap", "column_gap", "padding_top",
           "padding_bottom", "padding_left", "padding_right", "padding_x",
           "padding_y", "margin_top", "margin_bottom", "margin_left",
           "margin_right", "margin_x", "margin_y"}
RAZMERY = {"width", "height", "min_width", "max_width", "min_height",
           "max_height", "flex_basis", "top", "left", "right", "bottom",
           "grid_template_columns", "grid_template_rows"}


def files():
    return sorted(p for p in ROOT.rglob("*.py")
                  if "__pycache__" not in p.parts and p.name not in EXCLUDE)


def scan():
    """-> (всего, счётчик по файлам, счётчик по категориям, число смешанных)"""
    per_file, per_cat = collections.Counter(), collections.Counter()
    mixed = 0
    for p in files():
        for line in p.read_text(encoding="utf-8").splitlines():
            for m in PX.finditer(line):
                per_file[p.name] += 1
                before = line[:m.start()]
                pm = PROP.search(before) or DICT.search(before)
                prop = pm.group(1) if pm else "?"
                per_cat["отступы" if prop in OTSTUPY else
                        "размеры" if prop in RAZMERY else
                        "вне пропа" if prop == "?" else "прочее"] += 1
                if "SPACING[" in m.group(0) or "ROLE[" in m.group(0):
                    mixed += 1
    return sum(per_file.values()), per_file, per_cat, mixed


def self_test():
    """Прибор обязан уметь сказать «нет». Прогон на строках с известным ответом."""
    cases = [
        ('padding="16px"',                              1, "чистый литерал"),
        ("border=f\"1px solid {ROLE['border-default']}\"", 1, "составная строка"),
        ('padding=f"10px {SPACING[\'sm\']}"',            1, "литерал смешан с токеном"),
        ('gap=SPACING["md"]',                           0, "токен — не нарушение"),
        ('spacing="4"',                                 0, "шкала Radix — не нарушение"),
        ('size="2"',                                    0, "проп размера — не нарушение"),
        ('# 16px в комментарии',                        0, "вне литерала не считается"),
        ('text="стоимость 20px за штуку"',              1, "ложное срабатывание: px в прозе"),
    ]
    bad = 0
    print("САМОПРОВЕРКА ПРИБОРА")
    for src, expect, note in cases:
        got = len(PX.findall(src))
        ok = got == expect
        bad += not ok
        print(f"  {'ok ' if ok else 'СБОЙ'}  ждали {expect}, получили {got}  — {note}")
        if not ok:
            print(f"        строка: {src}")
    print(f"  итог: {'прибор исправен' if not bad else str(bad) + ' сбоев'}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--set-base", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return 2 if self_test() else 0

    total, per_file, per_cat, mixed = scan()

    print("НАСТРОЙКА ПРИБОРА")
    print(f"  область   : dash_app/**/*.py, кроме {sorted(EXCLUDE)}")
    print(f"  файлов    : {len(files())}")
    print(f"  считаем   : литералы, содержащие число с px, включая составные")
    print(f"  отметка   : {BASELINE} (замер 14.09.2026)")
    print()
    print(f"СЕЙЧАС: {total}")

    if a.report:
        print()
        for k, v in per_cat.most_common():
            print(f"  {k:<12} {v}")
        print(f"  {'смешанных с токеном':<12} {mixed}")
        print()
        print("  10 файлов с наибольшим числом:")
        for name, n in per_file.most_common(10):
            print(f"    {n:4d}  {name}")

    if a.set_base:
        src = pathlib.Path(__file__).read_text(encoding="utf-8")
        src = re.sub(r"^BASELINE = \d+", f"BASELINE = {total}", src, count=1, flags=re.M)
        pathlib.Path(__file__).write_text(src, encoding="utf-8")
        print(f"\nОтметка переписана: {BASELINE} -> {total}")
        return 0

    print()
    if total > BASELINE:
        print(f"ВЫРОСЛО на {total - BASELINE}. Приёмка не пройдена.")
        print("Литералы px в отступах — нарушение канона, см. CLAUDE.md,")
        print("«Как ставить задачу на UI», пункт 2.")
        return 1
    if total < BASELINE:
        print(f"Стало меньше на {BASELINE - total}. Отметку можно опустить: --set-base")
    else:
        print("Без изменений.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
