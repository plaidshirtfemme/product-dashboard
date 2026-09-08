"""Deliver tab (dash-mode only) — Double Diamond этап 4 + Figma MCP runbook.

Working prototype = сам дашборд (self-hosting). Здесь же — операционная инструкция
«как поднять Figma MCP», чтобы гнать HTML→Figma и token round-trip (DASH-133).
Источник правды по ВОЗМОЖНОСТЯМ инструментов — CLAUDE.md (раздел «Figma MCP»);
здесь — шаги запуска (bring-up).
"""

import reflex as rx

from ..tokens import SPACING, BORDER, PAGE_MAX_WIDTH
from ..components import section_header
from .motif_about import _placeholder

_MAX = PAGE_MAX_WIDTH


def _step(n: int, text: str, code: str | None = None) -> rx.Component:
    return rx.flex(
        rx.flex(
            rx.text(str(n), size="1", weight="bold", color=rx.color("teal", 11)),
            width="22px", height="22px", flex_shrink="0",
            align="center", justify="center",
            background=rx.color("teal", 3), border_radius="var(--radius-full)",
        ),
        rx.flex(
            rx.text(text, size="2", color=rx.color("gray", 12),
                    style={"line_height": "1.5"}),
            rx.code(code, size="1") if code is not None else rx.fragment(),
            direction="column", gap="4px",
        ),
        gap=SPACING["sm"], align="start", padding_y="6px", width="100%",
    )


def _runbook_card(title: str, tag: str, tag_color: str, steps: list) -> rx.Component:
    return rx.box(
        rx.flex(
            rx.text(title, size="3", weight="bold", color=rx.color("gray", 12)),
            rx.badge(tag, color_scheme=tag_color, variant="soft", size="1"),
            align="center", gap=SPACING["sm"], margin_bottom=SPACING["sm"],
        ),
        rx.flex(*steps, direction="column", gap="2px"),
        padding=SPACING["lg"],
        border=f"{BORDER} {rx.color('gray', 4)}",
        border_radius="var(--radius-3)",
        background=rx.color("gray", 1),
        flex="1", min_width="320px",
    )


def dash_deliver_tab() -> rx.Component:
    return rx.box(
        section_header(
            "Deliver",
            subtitle="Double Diamond · этап 4 — готовая поставка",
        ),
        _placeholder(
            "Working prototype — уже здесь: весь этот дашборд и есть поставленный продукт "
            "(self-hosting). Wireframes (DASH-62) и hi-fi макеты в Figma (DASH-63) — через "
            "Figma MCP по инструкции ниже.",
        ),

        rx.box(height=SPACING["xl"]),

        # ── Figma MCP bring-up runbook ────────────────────────────────────
        section_header(
            "Figma MCP · bring-up runbook",
            "cable",
            subtitle="Как поднять интеграцию для HTML→Figma и token round-trip (DASH-133)",
        ),
        rx.callout(
            "Два сервера. Официальный (use_figma) — для сборки компонентов/дизайн-систем "
            "(чище, атомарно, per-side border, настоящий hug, bind стилей). ClaudeTalkToFigma "
            "(community) — запасной для точечных правок вживую в открытом файле. Полное сравнение "
            "возможностей — в CLAUDE.md, раздел «Figma MCP».",
            icon="info", color_scheme="teal", variant="soft", size="1",
            margin_top=SPACING["sm"], margin_bottom=SPACING["md"],
        ),
        rx.flex(
            _runbook_card(
                "Официальный figma MCP", "для сборки · round-trip", "teal",
                [
                    _step(1, "Открыть Claude Code в папке product-dashboard — подхватит .mcp.json "
                             "(сервер figma, remote):", "https://mcp.figma.com/mcp"),
                    _step(2, "Проверить OAuth (Claude Pro). Если тулы mcp__figma__* отдают "
                             "auth-ошибку — переавторизоваться."),
                    _step(3, "Перед любым вызовом use_figma — загрузить скилл (иначе "
                             "трудноуловимые баги):", "resource:figma-use"),
                    _step(4, "Дать URL целевого Figma-файла. Без URL официальный создаёт "
                             "новый файл в Drafts (не пишет в открытую вкладку)."),
                ],
            ),
            _runbook_card(
                "ClaudeTalkToFigma", "запасной · live-правки", "violet",
                [
                    _step(1, "Терминал в папке инструмента, поднять socket-сервер (порт 3055, "
                             "окно держать открытым):",
                          "cd C:\\Users\\guzel\\Desktop\\claude-talk-to-figma-mcp ; bun run socket"),
                    _step(2, "Figma Desktop → Plugins → Development → запустить плагин "
                             "(manifest в src/claude_mcp_plugin/). Нет в списке → Import plugin "
                             "from manifest."),
                    _step(3, "В панели плагина скопировать channel ID."),
                    _step(4, "В Claude Code подключиться к каналу:", "join_channel <id>"),
                    _step(5, "Windows: MCP указывает на node dist/talk_to_figma_mcp/server.js "
                             "(сборка bun run build:win; голый npx падает на chmod)."),
                ],
            ),
            direction="row", wrap="wrap", gap=SPACING["lg"],
        ),

        rx.box(height=SPACING["md"]),
        rx.callout(
            "Token round-trip (DASH-133): бейдж собираем с Variables (цвет — через Variable, НЕ "
            "Color Style). Меняешь Variable в Figma вручную → Claude читает get_variable_defs → "
            "правит design_tokens.json → Reflex подхватывает. Полный автосинк JSON⇄Variables — "
            "через плагин Tokens Studio (для ручного демо не обязателен).",
            icon="repeat", color_scheme="amber", variant="soft", size="1",
        ),

        padding=SPACING["xl"],
        max_width=_MAX,
        margin="0 auto",
    )
