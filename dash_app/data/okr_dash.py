"""OKR data for DASH project (KP Dashboard itself). Sprint: 2026-06-22..2026-08-01."""
from __future__ import annotations
from .okr import KeyResult, Objective


DASH_OKR_OBJECTIVES: list[Objective] = [
    # Установочная встреча PM+Stakeholder 11.07.2026 (DASH-95):
    # North Star одна — «Кейс → оффер Muse». Прежние O1-O3 остаются как
    # операционные цели, инструментальные по отношению к O0.
    Objective(
        tag="O0 · North Star",
        title="Оффер продуктового дизайнера от Muse",
        description="Кейс — главная цель; удобство дашборда для выдуманной команды — инструментальная. "
                    "При конфликте приоритетов побеждает зритель кейса. Запасная цель — Tola (тёплый контакт).",
        quarter="Спринт 11–17 июля 2026 · жёсткий дедлайн пт 17.07",
        key_results=[
            KeyResult("KR-0.1", "Кейс опубликован на Framer ≤ 17.07",
                      current=0, target=1, unit="кейс", baseline=0),
            KeyResult("KR-0.2", "Отклики отправлены (Muse + Tola) ≤ 20.07",
                      current=0, target=2, unit="отклика", baseline=0),
            KeyResult("KR-0.3", "Приглашение на интервью",
                      current=0, target=1, unit="интервью", baseline=0),
        ],
    ),
    Objective(
        tag="O1 · Portfolio",
        title="Рекрутер понимает продуктовый контекст без объяснений",
        description="Portfolio North Star: дашборд самодостаточен как портфолио без дополнительных пояснений",
        quarter="Sprint 3–5 · июль 2026",
        key_results=[
            KeyResult("KR-1.1", "Вкладок с реальным контентом (не заглушка)",
                      current=17, target=17, unit="вкладок", baseline=0),
            KeyResult("KR-1.2", "Figma-артефактов дизайн-процесса (JM, HMW, UF, WF, Hi-fi)",
                      current=0, target=5, unit="артефактов", baseline=0),
            KeyResult("KR-1.3", "GitHub публичный релиз с README и demo GIF",
                      current=0, target=1, unit="релиз", baseline=0),
        ],
    ),
    Objective(
        tag="O2 · Design Process",
        title="Дизайн-процесс задокументирован и виден в дашборде",
        description="Product North Star: PM и команда понимают статус. Все роли и артефакты Double Diamond представлены.",
        quarter="Sprint 3–5 · июль 2026",
        key_results=[
            KeyResult("KR-2.1", "Артефактов Design Process (Journey Map, HMW, User Flow)",
                      current=0, target=3, unit="артефакта", baseline=0),
            KeyResult("KR-2.2", "Дневников ролей написано (PM + 7 ролей)",
                      current=1, target=8, unit="дневников", baseline=0),
            KeyResult("KR-2.3", "Единый sprint scenario задокументирован",
                      current=0, target=1, unit="сценарий", baseline=0),
        ],
    ),
    Objective(
        tag="O3 · Quality",
        title="Дашборд технически стабилен и готов к демо",
        description="Нет критических багов, DASH данные корректно отображаются во всех вкладках",
        quarter="Sprint 3–5 · июль 2026",
        key_results=[
            KeyResult("KR-3.1", "Handoff-2 багов закрыто",
                      current=6, target=6, unit="багов", baseline=0),
            KeyResult("KR-3.2", "DASH данные видны в Kanban и Backlog (DASH-73)",
                      current=0, target=1, unit="фича", baseline=0),
            KeyResult("KR-3.3", "Usability-тестов проведено с IT-друзьями",
                      current=0, target=3, unit="теста", baseline=0),
        ],
    ),
]


def load_dash_okrs() -> list[Objective]:
    return DASH_OKR_OBJECTIVES
