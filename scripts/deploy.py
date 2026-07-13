"""Деплой дашборда на Reflex Cloud с исключением внутренних файлов.

ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ для исключений = .gitignore. Сам `reflex deploy`
.gitignore НЕ уважает (проверено: CLAUDE.md и handoff-файлы попадали в
бэкенд-архив), поэтому этот скрипт читает .gitignore, раскрывает каждый
шаблон в реальные файлы и передаёт их через --exclude-from-backend.

⚠️ ВАЖНО: если однажды загитайгноришь файл, НУЖНЫЙ приложению в рантайме,
он выпадет из деплоя → сайт сломается. После деплоя всегда проверяй, что
URL открывается. (Сейчас таких файлов нет: assets/external не используется.)

Запуск (из любой папки):  python scripts/deploy.py
Ответы на вопросы деплоя:  proceed → y, create app → y, description → Enter.
"""
import glob
import os
import subprocess
import sys

APP_NAME = "product-dashboard"
VMTYPE = "c1m1"   # 1 CPU / 1 ГБ — в квоту free, тёплый старт <1 сек
REGION = "fra"    # Frankfurt — близко к EU-рекрутерам и RU

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gitignore_excludes() -> list[str]:
    """Читает .gitignore и раскрывает шаблоны в реально существующие пути.
    Пропускает комменты, пустые строки и негации (!). Пути — с прямыми слэшами."""
    excludes: set[str] = set()
    with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("!"):
                continue  # негации (!) — это RE-include, не исключаем
            pattern = line.rstrip("/")  # запись-папка вида "name/"
            for match in glob.glob(os.path.join(ROOT, pattern)):
                # прямые слэши — надёжнее кросс-платформенно для --exclude-from-backend
                excludes.add(os.path.relpath(match, ROOT).replace(os.sep, "/"))
    return sorted(excludes)


def main() -> None:
    excludes = gitignore_excludes()
    print("Исключаю из бэкенд-архива (источник — .gitignore):")
    for e in excludes:
        print("  -", e)

    cmd = [sys.executable, "-m", "reflex", "deploy",
           "--app-name", APP_NAME, "--vmtype", VMTYPE, "--region", REGION]
    for e in excludes:
        cmd += ["--exclude-from-backend", e]

    print(f"\nЗапускаю reflex deploy ({APP_NAME}, {VMTYPE}, {REGION}, "
          f"{len(excludes)} исключений)...\n")
    sys.exit(subprocess.run(cmd, cwd=ROOT).returncode)


if __name__ == "__main__":
    main()
