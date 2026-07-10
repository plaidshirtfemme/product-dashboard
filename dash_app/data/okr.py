"""Mock OKR data for Q2 2026. Tags match okr_tag field on issues."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class KeyResult:
    key: str
    title: str
    current: float
    target: float
    unit: str
    baseline: float = 0.0
    lower_is_better: bool = False

    @property
    def progress_pct(self) -> int:
        if self.lower_is_better:
            span = self.baseline - self.target
            if span == 0:
                return 100
            return max(0, min(100, round((self.baseline - self.current) / span * 100)))
        else:
            span = self.target - self.baseline
            if span == 0:
                return 100
            return max(0, min(100, round((self.current - self.baseline) / span * 100)))

    @property
    def status(self) -> str:
        # Quarter ~45% elapsed — expect ~45% progress
        p = self.progress_pct
        if p >= 36:    # ≥80% of expected
            return "on_track"
        if p >= 22:    # ≥50% of expected
            return "at_risk"
        return "off_track"

    @property
    def formatted_current(self) -> str:
        v = int(self.current) if self.current == int(self.current) else self.current
        return f"{v} {self.unit}"

    @property
    def formatted_target(self) -> str:
        v = int(self.target) if self.target == int(self.target) else self.target
        return f"{v} {self.unit}"


@dataclass
class Objective:
    tag: str        # matches okr_tag on issues
    title: str
    description: str
    quarter: str = "Q2 2026"
    key_results: list[KeyResult] = field(default_factory=list)

    @property
    def overall_progress_pct(self) -> int:
        if not self.key_results:
            return 0
        return round(sum(kr.progress_pct for kr in self.key_results) / len(self.key_results))

    @property
    def status(self) -> str:
        statuses = [kr.status for kr in self.key_results]
        if any(s == "off_track" for s in statuses):
            return "off_track"
        if any(s == "at_risk" for s in statuses):
            return "at_risk"
        return "on_track"

    @property
    def status_label(self) -> str:
        return {"on_track": "On Track", "at_risk": "At Risk", "off_track": "Off Track"}[self.status]

    @property
    def status_color(self) -> str:
        return {"on_track": "grass", "at_risk": "amber", "off_track": "tomato"}[self.status]


OKR_OBJECTIVES: list[Objective] = [
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


def load_okrs() -> list[Objective]:
    return OKR_OBJECTIVES
