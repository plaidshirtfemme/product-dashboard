"""Деплой дашборда на Reflex Cloud с исключением внутренних файлов.

ЕДИНЫЙ ИСТОЧНИК ПРАВДЫ для исключений = .gitignore. Сам `reflex deploy`
.gitignore НЕ уважает (проверено: CLAUDE.md и handoff-файлы попадали в
бэкенд-архив), поэтому этот скрипт читает .gitignore, раскрывает каждый
шаблон в реальные файлы и передаёт их через --exclude-from-backend.

⚠️ ВАЖНО: если однажды загитайгноришь файл, НУЖНЫЙ приложению в рантайме,
он выпадет из деплоя → сайт сломается. После деплоя всегда проверяй, что
URL открывается. (Сейчас таких файлов нет: assets/external не используется.)

DASH-162 (публичность на уровне проекта): local-проекты (видимость "local" в
PROJECT_VISIBILITY, сейчас Knowledge Pipeline) не уезжают на публичный сервер.
  • assert_no_local_leak() — страж: падает, если файл local-проекта попал бы в
    архив (проверка перед деплоем; есть флаг --check без деплоя);
  • деплою выставляется PUBLIC_BUILD=1, чтобы компиляция не собирала вкладки
    local-проектов во фронтенд (локальный reflex run его не ставит → видно всё).

Запуск (из любой папки):  python scripts/deploy.py
Проверка без деплоя:       python scripts/deploy.py --check
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


def public_ba_sa_paths() -> set[str]:
    """Пути конспектов BA/SA, которые МОЖНО публиковать.

    Папка `dash_app/content/ba-sa/` целиком в .gitignore, то есть по
    умолчанию не уезжает никуда. Исключение — разделы, у которых в шапке
    файла стоит `public: true`: их Гузель отметила готовыми в Obsidian.
    Вместе с разделом пропускаем картинки, на которые он ссылается.

    Нет поля public — раздел непубличный: ошибаемся в безопасную сторону.
    """
    sys.path.insert(0, ROOT)
    from dash_app.data.ba_sa_notes import list_sections, referenced_images

    allowed: set[str] = set()
    for section in list_sections():
        if not section.public:
            continue
        allowed.add(f"dash_app/content/ba-sa/{section.slug}.md")
        for image in referenced_images(section.slug):
            allowed.add(f"assets/ba-sa/{image}")
    return allowed


# ── DASH-162: страж публичности на уровне проекта ──────────────────────────
# Файлы local-проектов (видимость "local" в PROJECT_VISIBILITY) не должны
# уезжать в публичный бэкенд-архив. Маркеры — по расположению/префиксу (данные
# в dash_app/data/kp/, страницы real_*.py), а не по слову "real", чтобы
# переименование real→kp (DASH-187) не ломало страж.
LOCAL_PROJECT_GLOBS = [
    "dash_app/data/kp/**/*",       # данные Knowledge Pipeline
    "dash_app/pages/real_*.py",    # вкладки режима real (KP)
    "scripts/update_vault_snapshot.py",
]


def local_project_files() -> set[str]:
    """Реально существующие файлы local-проектов (по маркерам расположения)."""
    found: set[str] = set()
    for pattern in LOCAL_PROJECT_GLOBS:
        for match in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            # Артефакты компиляции не полицуем: их закрывают общие правила
            # .gitignore (__pycache__/, *.py[cod]) и reflex их не архивирует.
            if "__pycache__" in match or match.endswith((".pyc", ".pyo")):
                continue
            if os.path.isfile(match):
                found.add(os.path.relpath(match, ROOT).replace(os.sep, "/"))
    return found


def assert_no_local_leak(excludes: list[str]) -> None:
    """Прибор DASH-162: падает, если файл local-проекта не исключён из архива.

    Два известных ответа:
      • явления нет — все local-файлы в excludes, проверка молчит;
      • явление есть — какой-то local-файл не исключён (убрали из .gitignore
        или подложили новый), проверка печатает LEAK и отказывает (exit 2).
    """
    leaked = sorted(local_project_files() - set(excludes))
    if leaked:
        print("\n[X] DASH-162: файлы local-проекта попали бы в публичный архив:")
        for path in leaked:
            print("   LEAK:", path)
        print("Проверь .gitignore (dash_app/data/kp/*, dash_app/pages/real_*.py, "
              "scripts/update_vault_snapshot.py). Деплой остановлен.")
        sys.exit(2)


def main() -> None:
    public_paths = public_ba_sa_paths()
    excludes = [e for e in gitignore_excludes() if e not in public_paths]
    assert_no_local_leak(excludes)   # DASH-162: ни один local-файл не уедет
    if "--check" in sys.argv:
        print(f"[OK] DASH-162: все {len(local_project_files())} файлов "
              "local-проекта исключены из публичного архива.")
        return
    if public_paths:
        print("Публикую разделы BA/SA (public: true в шапке файла):")
        for path in sorted(public_paths):
            print("  +", path)
    print("Исключаю из бэкенд-архива (источник — .gitignore):")
    for e in excludes:
        print("  -", e)

    cmd = [sys.executable, "-m", "reflex", "deploy",
           "--app-name", APP_NAME, "--vmtype", VMTYPE, "--region", REGION]
    # 08.09.2026: для запуска из автоматики (там некому ответить «proceed?»)
    # передать скрипту --no-interactive. По умолчанию поведение прежнее,
    # интерактивное: 08.09 с этим флагом reflex вышел с кодом 1 без единой
    # строки вывода, причина не установлена.
    if "--no-interactive" in sys.argv:
        cmd.append("--no-interactive")
    for e in excludes:
        cmd += ["--exclude-from-backend", e]

    deploy_env = {**os.environ, "PUBLIC_BUILD": "1"}  # DASH-162: публичная компиляция
    print(f"\nЗапускаю reflex deploy ({APP_NAME}, {VMTYPE}, {REGION}, "
          f"{len(excludes)} исключений) [PUBLIC_BUILD=1]...\n")
    sys.exit(subprocess.run(cmd, cwd=ROOT, env=deploy_env).returncode)


if __name__ == "__main__":
    main()
