"""Research tab — Real project mode.

Shows only sections backed by real data:
- Vault Content Coverage (real snapshot)

Sections that are demo-only in this project:
- Research Journal (no real user research spikes)
- Usability Testing (no real test sessions)
"""

import reflex as rx
from ..components import section_header, data_source_badge, real_page_header, real_page_wrapper, vault_coverage_chart
from ..data.vault_snapshot import FOLDER_COUNTS, SNAPSHOT_DATE, TOTAL_NOTES
from ..components.empty_state import empty_state
from ..tokens import SPACING, BORDER


def real_research_tab() -> rx.Component:
    return real_page_wrapper(
        real_page_header(f"Vault снэпшот {SNAPSHOT_DATE} · {TOTAL_NOTES} заметок"),

        # Vault Coverage — real
        section_header(
            "Vault Content Coverage",
            subtitle="Количество заметок по папкам · красные = пробелы (< 5 заметок)",
            action=data_source_badge("real"),
        ),
        vault_coverage_chart(FOLDER_COUNTS),

        rx.box(height=SPACING["xl"]),

        # Research Journal — demo only
        section_header("Research Journal", action=data_source_badge("mock")),
        empty_state(
            "Research Journal",
            "Knowledge Pipeline — соло-проект для личного использования. "
            "Формальных research-спайков с гипотезами, методами и метриками не проводилось. "
            "В Demo режиме этот блок смоделирован для демонстрации UX Research процесса.",
            icon="microscope",
            mode="demo_only",
        ),

        rx.box(height=SPACING["xl"]),

        # Usability Testing — demo only
        section_header("Usability Testing", action=data_source_badge("mock")),
        empty_state(
            "Usability Testing",
            "Реальных usability-тестов с участниками не проводилось — "
            "у проекта нет внешних пользователей. "
            "В Demo режиме показаны симулированные сессии (TSR, SUS) "
            "для демонстрации компетенции UX Researcher.",
            icon="users",
            mode="demo_only",
        ),

    )
