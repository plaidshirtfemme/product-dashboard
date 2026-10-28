"""Чтение конспектов BA/SA с диска: вкладка Requirements, режим Product Dashboard.

Один раздел = один .md-файл в `dash_app/content/ba-sa/`. Файлы не в гите и
не в деплое (см. .gitignore и scripts/deploy.py) — это личные материалы,
которые Гузель правит в Obsidian. Читаем при каждом запросе, чтобы правка
файла была видна по F5, без перезапуска сервера.

Шапка файла (Obsidian показывает её как «свойства»):

    ---
    title: REST API
    order: 9
    public: false
    ---

`public` решает, уедет ли файл на публичный сервер. Здесь он не влияет ни
на что: локально видно всё, а на сервере непубличных файлов просто нет.

Что делаем с текстом перед отдачей в браузер:
  * срезаем шапку — её показывает не markdown, а заголовок страницы;
  * вырезаем блоки под заголовком с 🔒 — они для Obsidian, не для дашборда;
  * переписываем ссылки на картинки из обсидиановских `![[имя.png]]`
    в адрес, по которому картинку отдаёт Reflex: `/ba-sa/имя.png`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

CONTENT_DIR = Path(__file__).resolve().parents[1] / "content" / "ba-sa"

# Reflex раздаёт содержимое assets/ от корня сайта: assets/ba-sa/x.png → /ba-sa/x.png
ASSET_PREFIX = "/ba-sa/"

PRIVATE_MARK = "🔒"

_FRONT_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_WIKI_IMG_RE = re.compile(r"!\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
_MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


@dataclass(frozen=True)
class Section:
    slug: str          # имя файла без .md — оно же ключ в интерфейсе
    title: str
    order: int
    public: bool


def _parse_front(raw: str) -> tuple[dict[str, str], str]:
    """Отделяет шапку от текста. Разбираем руками: три поля, ради них
    тянуть в зависимости YAML-парсер незачем."""
    match = _FRONT_RE.match(raw)
    if not match:
        return {}, raw
    front: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            front[key.strip().lower()] = value.strip().strip("'\"")
    return front, raw[match.end():]


def _strip_private(body: str) -> str:
    """Убирает заголовок с 🔒 и всё под ним до следующего заголовка того же
    или более высокого уровня."""
    out: list[str] = []
    skip_level: int | None = None
    for line in body.splitlines():
        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            if skip_level is not None and level <= skip_level:
                skip_level = None           # выныриваем: приватный блок кончился
            if skip_level is None and PRIVATE_MARK in heading.group(2):
                skip_level = level
                continue
        if skip_level is None:
            out.append(line)
    return "\n".join(out)


def _asset_url(target: str) -> str:
    """Имя файла картинки → адрес, по которому её отдаёт Reflex.
    quote() нужен из-за пробелов: Obsidian называет вставленные картинки
    «Pasted image 20260916.png», а пробел ломает markdown-ссылку."""
    return ASSET_PREFIX + quote(target.strip().lstrip("/"))


def _rewrite_images(body: str) -> str:
    body = _WIKI_IMG_RE.sub(lambda m: f"![]({_asset_url(m.group(1))})", body)

    def md_image(match: re.Match[str]) -> str:
        alt, target = match.group(1), match.group(2).strip()
        if target.startswith(("/", "http://", "https://", "data:")):
            return match.group(0)        # абсолютную ссылку не трогаем
        return f"![{alt}]({_asset_url(target)})"

    return _MD_IMG_RE.sub(md_image, body)


def list_sections() -> list[Section]:
    """Все разделы по порядку. Папки нет (публичный сервер) — пустой список."""
    if not CONTENT_DIR.is_dir():
        return []
    sections: list[Section] = []
    for path in CONTENT_DIR.glob("*.md"):
        if path.name.startswith("_"):     # _template.md — не раздел
            continue
        front, _ = _parse_front(path.read_text(encoding="utf-8"))
        try:
            order = int(front.get("order", "0"))
        except ValueError:
            order = 0
        sections.append(Section(
            slug=path.stem,
            title=front.get("title") or path.stem,
            order=order,
            # нет поля — считаем непубличным: ошибаемся в безопасную сторону
            public=front.get("public", "").lower() in {"true", "yes", "1"},
        ))
    return sorted(sections, key=lambda s: (s.order, s.title))


def read_section(slug: str) -> str:
    """Готовый markdown раздела. Неизвестный slug → пустая строка:
    slug приходит из браузера, поэтому сверяем его со списком файлов,
    а не собираем путь из того, что прислали."""
    if slug not in {s.slug for s in list_sections()}:
        return ""
    _, body = _parse_front(CONTENT_DIR.joinpath(f"{slug}.md").read_text(encoding="utf-8"))
    return _rewrite_images(_strip_private(body)).strip()


def referenced_images(slug: str) -> set[str]:
    """Имена файлов картинок, на которые ссылается видимая часть раздела.

    Нужно деплою: вместе с опубликованным разделом должны уехать его
    картинки — и только они. Картинку внутри 🔒-блока не считаем: она
    не рендерится, значит на сервере ей делать нечего.
    """
    path = CONTENT_DIR / f"{slug}.md"
    if not path.is_file():
        return set()
    _, body = _parse_front(path.read_text(encoding="utf-8"))
    body = _strip_private(body)
    names = {m.group(1).strip() for m in _WIKI_IMG_RE.finditer(body)}
    for match in _MD_IMG_RE.finditer(body):
        target = match.group(2).strip()
        if not target.startswith(("/", "http://", "https://", "data:")):
            names.add(target)
    return {n.lstrip("/") for n in names if n}
