"""
Aggregation functions for the Overview tab. Pure Python — no Reflex
imports — so these are testable and reusable independent of the UI layer.
"""

from __future__ import annotations

import hashlib
import math
import random as _random
import re as _re
from collections import defaultdict
from dataclasses import dataclass

from .adapter import Issue


# ---------------------------------------------------------------------------
# Velocity
# ---------------------------------------------------------------------------

@dataclass
class VelocityStats:
    avg_sp_per_sprint: float | None   # mean story points per closed sprint
    last_sprint_sp: int | None        # story points in the most recent sprint
    sprint_count: int                 # how many sprints have at least one done issue


def velocity_stats(issues: list[Issue]) -> VelocityStats:
    """Story points completed per sprint — grouped by sprint_name."""
    by_sprint: dict[str, int] = defaultdict(int)
    for i in issues:
        if i.sprint_name and i.status == "Done":
            by_sprint[i.sprint_name] += i.story_points

    if not by_sprint:
        return VelocityStats(avg_sp_per_sprint=None, last_sprint_sp=None, sprint_count=0)

    def _sprint_num(name: str) -> int:
        m = _re.search(r'(\d+)\s*$', name)
        return int(m.group(1)) if m else 0

    vals = [sp for _, sp in sorted(by_sprint.items(), key=lambda kv: _sprint_num(kv[0]))]
    return VelocityStats(
        avg_sp_per_sprint=round(sum(vals) / len(vals), 1),
        last_sprint_sp=vals[-1],
        sprint_count=len(vals),
    )


# ---------------------------------------------------------------------------
# Flow Velocity + Flow Load (Mik Kersten / "Project to Product")
# ---------------------------------------------------------------------------

def flow_velocity_total(issues: list[Issue]) -> int:
    """Total story points done across ALL squads — product-level Flow Velocity."""
    return sum(i.story_points for i in issues if i.status == "Done")


def flow_load(issues: list[Issue]) -> int:
    """Current WIP — issues actively In Progress or In Review across all squads."""
    return sum(1 for i in issues if i.status in ("In Progress", "In Review"))


@dataclass
class EpicRiceRow:
    epic: str
    okr_tag: str
    reach: int
    impact: float
    confidence: float
    effort: float
    rice_score: float
    issue_count: int
    done_count: int


def rice_backlog(issues: list[Issue]) -> list[EpicRiceRow]:
    """One row per epic, sorted by RICE score descending."""
    by_epic: dict[str, list[Issue]] = defaultdict(list)
    for i in issues:
        by_epic[i.epic].append(i)

    rows = []
    for epic, epic_issues in by_epic.items():
        sample = epic_issues[0]
        rows.append(EpicRiceRow(
            epic=epic,
            okr_tag=sample.okr_tag,
            reach=sample.rice_reach,
            impact=sample.rice_impact,
            confidence=sample.rice_confidence,
            effort=sample.rice_effort,
            rice_score=sample.rice_score,
            issue_count=len(epic_issues),
            done_count=sum(1 for i in epic_issues if i.status == "Done"),
        ))
    return sorted(rows, key=lambda r: r.rice_score, reverse=True)


@dataclass
class OkrProgress:
    okr_tag: str
    total: int
    done: int

    @property
    def pct_done(self) -> int:
        return round(100 * self.done / self.total) if self.total else 0


def okr_breakdown(issues: list[Issue]) -> list[OkrProgress]:
    by_okr: dict[str, list[Issue]] = defaultdict(list)
    for i in issues:
        by_okr[i.okr_tag].append(i)
    return [
        OkrProgress(
            okr_tag=tag,
            total=len(group),
            done=sum(1 for i in group if i.status == "Done"),
        )
        for tag, group in by_okr.items()
    ]


@dataclass
class FlowStats:
    avg_cycle_time: float | None
    avg_lead_time: float | None
    sprint_predictability_pct: int | None
    total_rework: int
    rework_rate_pct: int  # rework events per issue, as a %


def flow_stats(issues: list[Issue]) -> FlowStats:
    done = [i for i in issues if i.status == "Done"]
    cycle_times = [i.cycle_time_days for i in done if i.cycle_time_days is not None]
    lead_times = [i.lead_time_days for i in done if i.lead_time_days is not None]

    total_rework = sum(i.rework_count for i in issues)

    # Predictability: of issues assigned to a *closed* sprint, what % ended up Done.
    closed_sprint_issues = [i for i in issues if i.sprint_state == "closed"]
    predictability = (
        round(100 * sum(1 for i in closed_sprint_issues if i.status == "Done") / len(closed_sprint_issues))
        if closed_sprint_issues else None
    )

    return FlowStats(
        avg_cycle_time=round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else None,
        avg_lead_time=round(sum(lead_times) / len(lead_times), 1) if lead_times else None,
        sprint_predictability_pct=predictability,
        total_rework=total_rework,
        rework_rate_pct=round(100 * total_rework / len(issues)) if issues else 0,
    )


@dataclass
class SquadHealth:
    squad_key: str
    total: int
    done: int
    blocked: int
    rework: int
    status: str  # "on_track" | "at_risk" | "blocked"

    @property
    def done_pct(self) -> int:
        return round(100 * self.done / self.total) if self.total else 0


# ---------------------------------------------------------------------------
# Analysis BA+SA
# ---------------------------------------------------------------------------

@dataclass
class AnalysisSummary:
    total_requirements: int
    approved: int
    avg_spec_completeness: float | None   # 0-100
    open_ambiguity_questions: int
    total_churn: int                      # sum of requirement_change_count
    avg_time_to_approval: float | None    # days


def analysis_stats(issues: list[Issue]) -> AnalysisSummary:
    reqs = [i for i in issues if i.issue_type == "requirement"]
    approved = [i for i in reqs if i.approved_at is not None]
    specs = [i.spec_completeness for i in issues if i.spec_completeness is not None]
    ttas = [i.time_to_approval_days for i in issues if i.time_to_approval_days is not None]
    return AnalysisSummary(
        total_requirements=len(reqs),
        approved=len(approved),
        avg_spec_completeness=round(sum(specs) / len(specs), 1) if specs else None,
        open_ambiguity_questions=sum(i.ambiguity_questions or 0 for i in issues),
        total_churn=sum(i.requirement_change_count or 0 for i in reqs),
        avg_time_to_approval=round(sum(ttas) / len(ttas), 1) if ttas else None,
    )


@dataclass
class RequirementRow:
    key: str
    status: str
    source: str | None
    spec_completeness: int | None
    ambiguity_questions: int | None
    change_count: int
    approved: bool
    time_to_approval_days: float | None
    epic: str


def analysis_requirements(issues: list[Issue]) -> list[RequirementRow]:
    reqs = [i for i in issues if i.issue_type == "requirement"]
    order = {"In Progress": 0, "To Do": 1, "Done": 2}
    reqs.sort(key=lambda i: (order.get(i.status, 9), i.key))
    return [
        RequirementRow(
            key=i.key,
            status=i.status,
            source=i.requirement_source,
            spec_completeness=i.spec_completeness,
            ambiguity_questions=i.ambiguity_questions,
            change_count=i.requirement_change_count or 0,
            approved=i.approved_at is not None,
            time_to_approval_days=i.time_to_approval_days,
            epic=i.epic,
        )
        for i in reqs
    ]


@dataclass
class DependencyRow:
    key: str
    epic: str
    has_external: bool
    api_contract_changes: int
    documented: bool


def analysis_dependencies(issues: list[Issue]) -> list[DependencyRow]:
    deps = [i for i in issues if i.dependency_documented is not None]
    return [
        DependencyRow(
            key=i.key,
            epic=i.epic,
            has_external=bool(i.has_external_dependency),
            api_contract_changes=i.api_contract_changes or 0,
            documented=bool(i.dependency_documented),
        )
        for i in deps
    ]


def requirement_source_counts(issues: list[Issue]) -> list[tuple[str, int]]:
    from collections import Counter
    sources = [i.requirement_source for i in issues if i.requirement_source]
    return Counter(sources).most_common()


# ---------------------------------------------------------------------------
# Shared squad helpers (Dev, Quality, Release, Monitoring)
# ---------------------------------------------------------------------------

@dataclass
class SquadSummary:
    squad_key: str
    total: int
    done: int
    sp_done: int
    rework: int
    blocked: int
    bugs: int

    @property
    def done_pct(self) -> int:
        return round(100 * self.done / self.total) if self.total else 0


def squad_summary(issues: list[Issue], squad_key: str) -> SquadSummary:
    sq = [i for i in issues if i.squad_key == squad_key]
    done = [i for i in sq if i.status == "Done"]
    return SquadSummary(
        squad_key=squad_key,
        total=len(sq),
        done=len(done),
        sp_done=sum(i.story_points for i in done),
        rework=sum(i.rework_count for i in sq),
        blocked=sum(1 for i in sq if i.blocked_by),
        bugs=sum(1 for i in sq if i.issue_type == "bug"),
    )


@dataclass
class BugRow:
    key: str
    squad_key: str
    status: str
    severity: str | None
    priority: str | None
    story_points: int
    cycle_time_days: float | None
    rework_count: int


def squad_bugs(issues: list[Issue], squad_key: str | None = None) -> list[BugRow]:
    """Bugs for a specific squad, or all bugs if squad_key is None."""
    bugs = [i for i in issues if i.issue_type == "bug"]
    if squad_key:
        bugs = [i for i in bugs if i.squad_key == squad_key]
    sev_order = {"Blocker": 0, "Critical": 1, "Major": 2, "Minor": 3, "Trivial": 4}
    bugs.sort(key=lambda i: (sev_order.get(i.severity or "", 9), i.key))
    return [
        BugRow(
            key=i.key,
            squad_key=i.squad_key,
            status=i.status,
            severity=i.severity,
            priority=i.priority,
            story_points=i.story_points,
            cycle_time_days=i.cycle_time_days,
            rework_count=i.rework_count,
        )
        for i in bugs
    ]


@dataclass
class SimpleIssueRow:
    key: str
    status: str
    issue_type: str
    story_points: int
    priority: str | None
    cycle_time_days: float | None
    rework_count: int
    blocked_by: str | None


def squad_non_bugs(issues: list[Issue], squad_key: str) -> list[SimpleIssueRow]:
    sq = [i for i in issues if i.squad_key == squad_key and i.issue_type not in ("bug", "adr")]
    order = {"In Progress": 0, "In Review": 1, "To Do": 2, "Done": 3}
    sq.sort(key=lambda i: (order.get(i.status, 9), i.key))
    return [
        SimpleIssueRow(
            key=i.key,
            status=i.status,
            issue_type=i.issue_type,
            story_points=i.story_points,
            priority=i.priority,
            cycle_time_days=i.cycle_time_days,
            rework_count=i.rework_count,
            blocked_by=i.blocked_by,
        )
        for i in sq
    ]


@dataclass
class ReleaseVersionRow:
    version: str
    done: int
    total: int
    slipped: int

    @property
    def done_pct(self) -> int:
        return round(100 * self.done / self.total) if self.total else 0


def release_plan(issues: list[Issue]) -> list[ReleaseVersionRow]:
    by_version: dict[str, list[Issue]] = defaultdict(list)
    for i in issues:
        if i.squad_key == "RELEASE" and i.fix_version:
            by_version[i.fix_version].append(i)
    rows = []
    for version, group in sorted(by_version.items()):
        rows.append(ReleaseVersionRow(
            version=version,
            done=sum(1 for i in group if i.status == "Done"),
            total=len(group),
            slipped=sum(1 for i in group if i.release_slipped),
        ))
    return rows


def slipped_issues(issues: list[Issue]) -> list[SimpleIssueRow]:
    slipped = [i for i in issues if i.squad_key == "RELEASE" and i.release_slipped]
    return [
        SimpleIssueRow(
            key=i.key,
            status=i.status,
            issue_type=i.issue_type,
            story_points=i.story_points,
            priority=i.priority,
            cycle_time_days=i.cycle_time_days,
            rework_count=i.rework_count,
            blocked_by=i.blocked_by,
        )
        for i in slipped
    ]


# ---------------------------------------------------------------------------
# Architecture
# ---------------------------------------------------------------------------

@dataclass
class ArchSummary:
    total: int
    done: int
    sp_done: int
    rework: int
    adr_total: int
    adr_done: int
    adr_in_review: int
    adr_in_progress: int


@dataclass
class AdrRow:
    key: str
    issue_status: str   # Jira status: Done / In Review / In Progress
    adr_status: str     # Accepted / Proposed / Deprecated
    context: str | None
    decision: str | None
    consequences: str | None
    story_points: int


@dataclass
class ArchTaskRow:
    key: str
    status: str
    issue_type: str
    story_points: int
    cycle_time_days: float | None
    rework_count: int


def arch_stats(issues: list[Issue]) -> ArchSummary:
    arch = [i for i in issues if i.squad_key == "ARCHITECTURE"]
    adrs = [i for i in arch if i.issue_type == "adr"]
    done = [i for i in arch if i.status == "Done"]
    return ArchSummary(
        total=len(arch),
        done=len(done),
        sp_done=sum(i.story_points for i in done),
        rework=sum(i.rework_count for i in arch),
        adr_total=len(adrs),
        adr_done=sum(1 for i in adrs if i.status == "Done"),
        adr_in_review=sum(1 for i in adrs if i.status == "In Review"),
        adr_in_progress=sum(1 for i in adrs if i.status == "In Progress"),
    )


def arch_adrs(issues: list[Issue]) -> list[AdrRow]:
    adrs = [i for i in issues if i.issue_type == "adr"]
    order = {"In Progress": 0, "In Review": 1, "Done": 2}
    adrs.sort(key=lambda i: (order.get(i.status, 9), i.key))
    return [
        AdrRow(
            key=i.key,
            issue_status=i.status,
            adr_status=i.adr_status or "Proposed",
            context=i.adr_context,
            decision=i.adr_decision,
            consequences=i.adr_consequences,
            story_points=i.story_points,
        )
        for i in adrs
    ]


def arch_tasks(issues: list[Issue]) -> list[ArchTaskRow]:
    arch_non_adr = [i for i in issues if i.squad_key == "ARCHITECTURE" and i.issue_type != "adr"]
    order = {"In Progress": 0, "In Review": 1, "To Do": 2, "Done": 3}
    arch_non_adr.sort(key=lambda i: (order.get(i.status, 9), i.key))
    return [
        ArchTaskRow(
            key=i.key,
            status=i.status,
            issue_type=i.issue_type,
            story_points=i.story_points,
            cycle_time_days=i.cycle_time_days,
            rework_count=i.rework_count,
        )
        for i in arch_non_adr
    ]


# ---------------------------------------------------------------------------
# Growth
# ---------------------------------------------------------------------------

@dataclass
class GrowthSummary:
    total_experiments: int
    b_wins: int           # result == "Вариант B лучше"
    inconclusive: int     # result == "Без значимой разницы"
    pending: int          # result is None
    sp_done: int
    tasks_done: int
    tasks_total: int


def _two_prop_ztest(n_a: int, conv_a: float, n_b: int, conv_b: float) -> float:
    """Two-proportion z-test, two-tailed p-value."""
    p_pool = (conv_a * n_a + conv_b * n_b) / (n_a + n_b)
    if p_pool in (0.0, 1.0):
        return 1.0
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))
    if se == 0:
        return 1.0
    z = (conv_b - conv_a) / se
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return round(p, 4)


def _mock_ab_stats(key: str) -> tuple[int, int, float, float]:
    """Deterministic mock A/B sample sizes and conversion rates from issue key."""
    rng = _random.Random(int(hashlib.md5(key.encode()).hexdigest(), 16))
    n_a = rng.randint(300, 1500)
    n_b = rng.randint(300, 1500)
    conv_a = round(rng.uniform(0.15, 0.50), 3)
    delta = rng.uniform(-0.12, 0.18)
    conv_b = round(max(0.05, min(0.80, conv_a + delta)), 3)
    return n_a, n_b, conv_a, conv_b


_VARIANT_HYPOTHESES: dict[str, str] = {
    "Новый onboarding": "Новый onboarding flow повысит активацию пользователей",
    "Альтернативный folder_examples.yml": "Упрощённый шаблон конфигурации снизит барьер входа",
}


@dataclass
class ExperimentRow:
    key: str
    status: str
    variant_a: str
    variant_b: str
    result: str | None    # "Вариант B лучше" | "Без значимой разницы" | None
    hypothesis: str = ""
    n_a: int = 0
    n_b: int = 0
    conv_a: float = 0.0
    conv_b: float = 0.0
    p_value: float = 1.0


@dataclass
class ReleaseRow:
    version: str
    done: int
    total: int
    slipped: int

    @property
    def done_pct(self) -> int:
        return round(100 * self.done / self.total) if self.total else 0


def growth_stats(issues: list[Issue]) -> GrowthSummary:
    exp = [i for i in issues if i.issue_type == "experiment"]
    growth = [i for i in issues if i.squad_key == "GROWTH"]
    return GrowthSummary(
        total_experiments=len(exp),
        b_wins=sum(1 for i in exp if i.experiment_result == "Вариант B лучше"),
        inconclusive=sum(1 for i in exp if i.experiment_result == "Без значимой разницы"),
        pending=sum(1 for i in exp if i.experiment_result is None),
        sp_done=sum(i.story_points for i in growth if i.status == "Done"),
        tasks_done=sum(1 for i in growth if i.status == "Done"),
        tasks_total=len(growth),
    )


def growth_experiments(issues: list[Issue]) -> list[ExperimentRow]:
    exp = [i for i in issues if i.issue_type == "experiment"]
    rows = []
    for i in exp:
        vb = i.variant_b or "—"
        n_a, n_b, conv_a, conv_b = _mock_ab_stats(i.key)
        rows.append(ExperimentRow(
            key=i.key,
            status=i.status,
            variant_a=i.variant_a or "Контроль",
            variant_b=vb,
            result=i.experiment_result,
            hypothesis=_VARIANT_HYPOTHESES.get(vb, f"Вариант B ({vb}) улучшит ключевую метрику"),
            n_a=n_a,
            n_b=n_b,
            conv_a=conv_a,
            conv_b=conv_b,
            p_value=_two_prop_ztest(n_a, conv_a, n_b, conv_b),
        ))
    return rows


def growth_releases(issues: list[Issue]) -> list[ReleaseRow]:
    by_release: dict[str, list[Issue]] = defaultdict(list)
    for i in issues:
        if i.squad_key == "GROWTH" and i.fix_version:
            by_release[i.fix_version].append(i)
    rows = []
    for version, group in sorted(by_release.items()):
        rows.append(ReleaseRow(
            version=version,
            done=sum(1 for i in group if i.status == "Done"),
            total=len(group),
            slipped=sum(1 for i in group if i.release_slipped),
        ))
    return rows


# ---------------------------------------------------------------------------
# Design
# ---------------------------------------------------------------------------

@dataclass
class DesignSummary:
    total_design_issues: int
    in_progress: int
    done: int
    avg_iterations: float | None
    max_iterations: int | None
    a11y_checked: int
    a11y_total: int       # issues where accessibility_checked is not None
    design_rework: int    # rework events across DESIGN squad


@dataclass
class DesignIssueRow:
    key: str
    status: str
    epic: str
    iteration_count: int | None
    accessibility_checked: bool | None
    okr_tag: str
    story_points: int
    cycle_time_days: float | None
    rework_count: int


def design_stats(issues: list[Issue]) -> DesignSummary:
    design = [i for i in issues if i.issue_type == "design"]
    a11y_issues = [i for i in design if i.accessibility_checked is not None]
    iter_vals = [i.iteration_count for i in design if i.iteration_count is not None]
    design_squad = [i for i in issues if i.squad_key == "DESIGN"]
    return DesignSummary(
        total_design_issues=len(design),
        in_progress=sum(1 for i in design if i.status in ("In Progress", "In Review")),
        done=sum(1 for i in design if i.status == "Done"),
        avg_iterations=round(sum(iter_vals) / len(iter_vals), 1) if iter_vals else None,
        max_iterations=max(iter_vals) if iter_vals else None,
        a11y_checked=sum(1 for i in a11y_issues if i.accessibility_checked),
        a11y_total=len(a11y_issues),
        design_rework=sum(i.rework_count for i in design_squad),
    )


def design_issues(issues: list[Issue]) -> list[DesignIssueRow]:
    design = [i for i in issues if i.issue_type == "design"]
    order = {"In Progress": 0, "In Review": 1, "To Do": 2, "Done": 3}
    design.sort(key=lambda i: (order.get(i.status, 9), i.key))
    return [
        DesignIssueRow(
            key=i.key,
            status=i.status,
            epic=i.epic,
            iteration_count=i.iteration_count,
            accessibility_checked=i.accessibility_checked,
            okr_tag=i.okr_tag,
            story_points=i.story_points,
            cycle_time_days=i.cycle_time_days,
            rework_count=i.rework_count,
        )
        for i in design
    ]


# ---------------------------------------------------------------------------
# Research
# ---------------------------------------------------------------------------

@dataclass
class ResearchSummary:
    total_spikes: int
    in_progress: int
    done: int
    with_insight: int
    applied: int      # decision == "Применено"


def research_stats(issues: list[Issue]) -> ResearchSummary:
    spikes = [i for i in issues if i.issue_type == "research-spike"]
    return ResearchSummary(
        total_spikes=len(spikes),
        in_progress=sum(1 for i in spikes if i.status in ("In Progress", "In Review")),
        done=sum(1 for i in spikes if i.status == "Done"),
        with_insight=sum(1 for i in spikes if i.insight),
        applied=sum(1 for i in spikes if i.decision == "Применено"),
    )


def research_journal(issues: list[Issue]) -> list[Issue]:
    """Research-spike issues sorted: In Progress first, then Done."""
    spikes = [i for i in issues if i.issue_type == "research-spike"]
    order = {"In Review": 0, "In Progress": 1, "Done": 2}
    return sorted(spikes, key=lambda i: (order.get(i.status, 9), i.key))


_SQUAD_HEALTH_EXCLUDE = {"PM"}  # PM tasks have different nature — exclude from cross-squad averages


def squad_health(issues: list[Issue]) -> list[SquadHealth]:
    by_squad: dict[str, list[Issue]] = defaultdict(list)
    for i in issues:
        by_squad[i.squad_key].append(i)

    # Baseline computed only over engineering squads — PM tasks (planning,
    # grooming, OKR) have structurally different blocked/rework patterns
    # and would skew the threshold for everyone else.
    baseline_issues = [i for i in issues if i.squad_key not in _SQUAD_HEALTH_EXCLUDE]
    overall_blocked_rate = sum(1 for i in baseline_issues if i.blocked_by) / len(baseline_issues) if baseline_issues else 0
    overall_rework_rate = sum(i.rework_count for i in baseline_issues) / len(baseline_issues) if baseline_issues else 0

    results = []
    for squad_key, group in by_squad.items():
        blocked = sum(1 for i in group if i.blocked_by)
        rework = sum(i.rework_count for i in group)
        blocked_rate = blocked / len(group)
        rework_rate = rework / len(group)

        # "Meaningfully above average" = at least 1.5x the baseline,
        # AND at least 2 raw occurrences (guards against 1-issue squads
        # showing 100% off a single data point).
        if blocked >= 2 and blocked_rate > overall_blocked_rate * 1.5:
            status = "blocked"
        elif rework >= 2 and rework_rate > overall_rework_rate * 1.5:
            status = "at_risk"
        else:
            status = "on_track"

        results.append(SquadHealth(
            squad_key=squad_key,
            total=len(group),
            done=sum(1 for i in group if i.status == "Done"),
            blocked=blocked,
            rework=rework,
            status=status,
        ))
    return results


# ---------------------------------------------------------------------------
# Per-person WIP (Dev tab)
# ---------------------------------------------------------------------------

@dataclass
class PersonWip:
    assignee: str
    total: int
    in_progress: int
    done: int
    rework: int

    @property
    def context_switches(self) -> int:
        """Proxy: rework events ≈ task interruptions / direction changes."""
        return self.rework

    @property
    def wip_status(self) -> str:
        if self.in_progress >= 3:
            return "overloaded"
        if self.in_progress == 2:
            return "at_risk"
        return "ok"


def dev_person_wip(issues: list[Issue]) -> list[PersonWip]:
    dev = [i for i in issues if i.squad_key == "DEV"]
    by_person: dict[str, list[Issue]] = defaultdict(list)
    for i in dev:
        by_person[i.assignee].append(i)

    result = []
    for assignee, tasks in sorted(by_person.items()):
        result.append(PersonWip(
            assignee=assignee,
            total=len(tasks),
            in_progress=sum(1 for t in tasks if t.status in ("In Progress", "In Review")),
            done=sum(1 for t in tasks if t.status == "Done"),
            rework=sum(t.rework_count for t in tasks),
        ))
    return sorted(result, key=lambda p: -p.in_progress)


# ---------------------------------------------------------------------------
# Sprint Trends (Dev tab)
# ---------------------------------------------------------------------------


@dataclass
class SprintTrend:
    sprint_num: int          # 1-4
    label: str               # "Sprint 1"
    throughput: int          # issues Done
    sp_done: int
    rework_count: int
    avg_cycle_time: float | None
    avg_lead_time: float | None


def sprint_trends(issues: list[Issue]) -> list[SprintTrend]:
    """Aggregate all squads by sprint number (N from 'Squad Name Sprint N')."""
    by_num: dict[int, list[Issue]] = defaultdict(list)
    for i in issues:
        if i.sprint_name:
            m = _re.search(r'(\d+)\s*$', i.sprint_name)
            if m:
                by_num[int(m.group(1))].append(i)

    result = []
    for num in sorted(by_num):
        group = by_num[num]
        done = [i for i in group if i.status == "Done"]
        cycles = [i.cycle_time_days for i in done if i.cycle_time_days is not None]
        leads = [i.lead_time_days for i in done if i.lead_time_days is not None]
        result.append(SprintTrend(
            sprint_num=num,
            label=f"Sprint {num}",
            throughput=len(done),
            sp_done=sum(i.story_points for i in done),
            rework_count=sum(i.rework_count for i in group),
            avg_cycle_time=round(sum(cycles) / len(cycles), 1) if cycles else None,
            avg_lead_time=round(sum(leads) / len(leads), 1) if leads else None,
        ))
    return result


# ---------------------------------------------------------------------------
# Go / No-Go checklist (Quality tab)
# ---------------------------------------------------------------------------

@dataclass
class GoNoGoCriterion:
    label: str
    ok: bool
    detail: str
    critical: bool = True  # critical = blocks release if not ok


def go_no_go_criteria(issues: list[Issue]) -> list[GoNoGoCriterion]:
    bugs = [i for i in issues if i.issue_type == "bug"]
    blocker_open = [b for b in bugs if b.severity == "Blocker" and b.status != "Done"]
    critical_open = [b for b in bugs if b.severity == "Critical" and b.status != "Done"]
    major_open = [b for b in bugs if b.severity == "Major" and b.status != "Done"]
    release_slipped = [i for i in issues if i.release_slipped]
    critical_blocked = [i for i in issues if i.blocked_by and i.priority in ("Highest", "High")]

    return [
        GoNoGoCriterion(
            label="Нет открытых Blocker-багов",
            ok=len(blocker_open) == 0,
            detail=f"{len(blocker_open)} Blocker открыто" if blocker_open else "✓ все закрыты",
            critical=True,
        ),
        GoNoGoCriterion(
            label="Нет открытых Critical-багов",
            ok=len(critical_open) == 0,
            detail=f"{len(critical_open)} Critical открыто" if critical_open else "✓ все закрыты",
            critical=True,
        ),
        GoNoGoCriterion(
            label="Major-баги: не более 3",
            ok=len(major_open) <= 3,
            detail=f"{len(major_open)} Major открыто",
            critical=True,
        ),
        GoNoGoCriterion(
            label="Нет задач с release_slipped",
            ok=len(release_slipped) == 0,
            detail=f"{len(release_slipped)} задач сдвинуты" if release_slipped else "✓ нет сдвигов",
            critical=True,
        ),
        GoNoGoCriterion(
            label="Нет критических заблокированных задач",
            ok=len(critical_blocked) == 0,
            detail=f"{len(critical_blocked)} High/Highest заблокировано" if critical_blocked else "✓ нет блокировок",
            critical=True,
        ),
        GoNoGoCriterion(
            label="CI/CD green (последний build)",
            ok=True,
            detail="✓ mock: все gates прошли",
            critical=True,
        ),
        GoNoGoCriterion(
            label="Покрытие тестами ≥ 70%",
            ok=True,
            detail="✓ mock: 74%",
            critical=False,
        ),
    ]
