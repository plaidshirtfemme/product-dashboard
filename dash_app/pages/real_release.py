"""Release tab — Real project mode."""

import reflex as rx
from ..components import section_header, real_page_header, real_page_wrapper
from ..data.real_project_extract import GIT_COMMITS
from ..tokens import SPACING, BORDER

_CAT_COLOR = {
    "feat": "teal", "refactor": "blue",
    "fix": "amber", "chore": "gray", "security": "red",
}

_SECURITY_CHECKLIST = [
    ("ANTHROPIC_API_KEY вынесен в .env",       True),
    (".gitignore: cookies.txt, logs/, *.db, urls.txt", True),
    ("Личные пути C:\\Users\\guzel убраны",    True),
    ("История гита проверена на секреты",      True),
    (".env.example с плейсхолдерами добавлен", True),
    ("Репозиторий private",                    True),
    ("Дашборд удалён из repo до интервью",     True),
]


def _commit_milestone(c) -> rx.Component:
    color = _CAT_COLOR.get(c.category, "gray")
    is_security = c.category == "security"
    return rx.flex(
        # Timeline dot
        rx.flex(
            rx.box(
                width="10px", height="10px",
                border_radius="50%",
                background=rx.color(color, 9),
            ),
            rx.box(
                width="1px", height="100%",
                background=rx.color("gray", 4),
                margin="2px auto 0",
            ),
            direction="column",
            align="center",
            min_height="48px",
        ),
        # Content
        rx.flex(
            rx.flex(
                rx.text(c.date, size="1", color=rx.color("gray", 8),
                        font_family="monospace"),
                rx.badge(c.category, color_scheme=color, variant="soft", size="1"),
                gap=SPACING["sm"],
                align="center",
            ),
            rx.text(c.message, size="2", color=rx.color("gray", 11),
                    margin_top="2px", line_height="1.5"),
            direction="column",
            gap="2px",
            padding_bottom=SPACING["md"],
        ),
        gap=SPACING["md"],
        align="start",
    )


def _check_row(label: str, done: bool) -> rx.Component:
    return rx.flex(
        rx.icon(
            "check" if done else "circle",
            size=16,
            color=rx.color("teal" if done else "gray", 8),
        ),
        rx.text(label, size="2",
                color=rx.color("gray", 11 if done else 8)),
        gap=SPACING["sm"],
        align="center",
        padding="6px 0",
    )


def real_release_tab() -> rx.Component:
    first_date = GIT_COMMITS[0].date
    last_date  = GIT_COMMITS[-1].date

    return real_page_wrapper(
        real_page_header(f"git log · {first_date} → {last_date}"),

        # Timeline
        section_header(f"Release history · {len(GIT_COMMITS)} коммитов", "package"),
        rx.box(
            *[_commit_milestone(c) for c in GIT_COMMITS],
            padding=f"{SPACING['md']} {SPACING['lg']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),

        rx.box(height=SPACING["xl"]),

        # Security go/no-go checklist
        section_header("Security go/no-go · перед пушем на GitHub", "shield-check"),
        rx.box(
            *[_check_row(label, done) for label, done in _SECURITY_CHECKLIST],
            padding=f"{SPACING['md']}",
            border=f"{BORDER} {rx.color('gray', 4)}",
            border_radius="var(--radius-3)",
            background=rx.color("gray", 1),
            margin_top=SPACING["sm"],
        ),
        rx.callout(
            "Все пункты выполнены. Репозиторий в private, "
            "дашборд показывается на интервью локально.",
            icon="circle-check",
            color_scheme="teal",
            variant="soft",
            size="1",
            margin_top=SPACING["md"],
        ),

    )
