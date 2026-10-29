"""Motif (demo) OKR-данные. Общие дата-классы — в okr_types (DASH-167, набор C)."""
from __future__ import annotations

from .okr_types import KeyResult, Objective


MOTIF_OKR_OBJECTIVES: list[Objective] = [
    Objective(
        tag="Рост охвата контента",
        title="Расширить охват и качество контента в пайплайне",
        description="Пайплайн должен покрывать достаточный объём контента с высоким качеством обработки",
        key_results=[
            KeyResult("KR-1.1", "Увеличить число обработанных URL",
                      current=823, target=2000, unit="URL", baseline=200),
            KeyResult("KR-1.2", "Поднять долю заметок с оценкой качества ≥4",
                      current=51, target=70, unit="%", baseline=40),
            KeyResult("KR-1.3", "Снизить % дублей в vault",
                      current=8, target=3, unit="%", baseline=12, lower_is_better=True),
        ],
    ),
    Objective(
        tag="Снижение needs_review",
        title="Устранить накопленный технический долг",
        description="Закрыть нестабильные результаты и ускорить цикл QA",
        key_results=[
            KeyResult("KR-2.1", "Закрыть заметки в статусе needs_review",
                      current=31, target=100, unit="%", baseline=0),
            KeyResult("KR-2.2", "Снизить Cycle Time по задачам QA",
                      current=4.8, target=3.0, unit="дн.", baseline=6.0, lower_is_better=True),
        ],
    ),
    Objective(
        tag="Скорость обработки",
        title="Повысить скорость и надёжность пайплайна",
        description="Пайплайн должен работать быстрее и стабильнее при росте нагрузки",
        key_results=[
            KeyResult("KR-3.1", "Сократить время полного прогона пайплайна",
                      current=140, target=45, unit="мин", baseline=240, lower_is_better=True),
            KeyResult("KR-3.2", "Поднять uptime пайплайна",
                      current=94, target=99, unit="%", baseline=87),
            KeyResult("KR-3.3", "Достичь 0 критических инцидентов в квартал",
                      current=2, target=0, unit="инц.", baseline=5, lower_is_better=True),
        ],
    ),
]


def load_motif_okrs() -> list[Objective]:
    return MOTIF_OKR_OBJECTIVES
