"""Общие дата-классы OKR — нейтральны к проекту.

Выделены из okr_motif.py (DASH-167, набор C): типы `KeyResult`/`Objective`
общие для всех проектов (Motif, DASH, KP), поэтому живут в безымянном
пространстве, а не в файле одного пира. Данные OKR — в okr_motif.py /
okr_dash.py / (будущем) okr_kp.py.
"""
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
