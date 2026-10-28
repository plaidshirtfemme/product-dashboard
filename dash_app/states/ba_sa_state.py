"""Состояние вкладки Requirements · BA/SA в режиме Product Dashboard.

Двенадцать разделов-конспектов лежат на диске .md-файлами. Читаем их не
на импорте, а в обработчиках: правка файла в Obsidian видна после F5,
перезапускать сервер не нужно.

`load()` висит на загрузке страницы (dash_app.py), `open_section()` — на
клике по разделу. Оба перечитывают диск.
"""

from __future__ import annotations

import reflex as rx

from ..data.ba_sa_notes import list_sections, read_section


class BaSaState(rx.State):
    """Список разделов и текст выбранного."""

    # [{"slug": ..., "title": ...}] — rx.foreach по списку словарей
    sections: list[dict[str, str]] = []
    active_slug: str = ""
    active_title: str = ""
    content: str = ""

    def load(self):
        """Пересобрать список разделов и перечитать открытый."""
        found = list_sections()
        self.sections = [{"slug": s.slug, "title": s.title} for s in found]
        if not found:
            # Папки нет — так выглядит публичный сервер, куда файлы не уезжают.
            self.active_slug = ""
            self.active_title = ""
            self.content = ""
            return
        if self.active_slug not in {s.slug for s in found}:
            self.active_slug = found[0].slug
        self.content = read_section(self.active_slug)
        self._sync_title()

    def open_section(self, slug: str):
        self.active_slug = slug
        self.content = read_section(slug)
        self._sync_title()

    def _sync_title(self):
        """Название открытого раздела — заголовок страницы; список названий
        живёт в левом меню, поэтому на странице его больше нет."""
        self.active_title = next(
            (s["title"] for s in self.sections if s["slug"] == self.active_slug),
            "",
        )
