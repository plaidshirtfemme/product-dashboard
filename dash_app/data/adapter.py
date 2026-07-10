"""
Adapter — the "Transform" stage of our mini-ETL.

Parses raw Jira-shaped issue JSON (see jira_mock_raw.py) into clean,
UI-friendly dataclasses. This is the ONLY place that knows both the raw
Jira shape AND the internal schema — the dashboard components never see
customfield_XXXXX or changelog directly.

Everything computed here (cycle_time, rework_count, assignee_churn,
blocked_by) is a derived value that real Jira does not hand you directly —
this function is doing the work a real integration's ETL job would do.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .jira_mock_raw import (
    generate_raw_issues,
    get_dash_issues,
    get_releases,
    ProjectConfig,
    MOTIF_DEMO_CONFIG,
    DASH_CONFIG,
    WORKFLOW_INDEX,
    CF_STORY_POINTS,
    CF_SPRINT,
    CF_EPIC_LINK,
    CF_RICE_REACH,
    CF_RICE_IMPACT,
    CF_RICE_CONFIDENCE,
    CF_RICE_EFFORT,
    CF_OKR_TAG,
    CF_HYPOTHESIS,
    CF_RESEARCH_METHOD,
    CF_RESEARCH_METRIC,
    CF_INSIGHT,
    CF_DECISION,
    CF_VARIANT_A,
    CF_VARIANT_B,
    CF_EXPERIMENT_RESULT,
    CF_REQUIREMENT_SOURCE,
    CF_SEVERITY,
    CF_SPEC_COMPLETENESS,
    CF_AMBIGUITY_QUESTIONS,
    CF_DEPENDENCY_DOCUMENTED,
    CF_HAS_EXTERNAL_DEPENDENCY,
    CF_ADR_CONTEXT,
    CF_ADR_OPTIONS,
    CF_ADR_DECISION,
    CF_ADR_CONSEQUENCES,
    CF_ADR_STATUS,
    CF_ITERATION_COUNT,
    CF_ACCESSIBILITY_CHECKED,
)


def _parse_iso(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.000+0000")


@dataclass
class Issue:
    key: str
    squad_key: str
    epic: str
    issue_type: str
    status: str
    assignee: str
    story_points: int

    created_at: datetime
    started_at: datetime | None    # first transition INTO "In Progress"
    done_at: datetime | None       # resolutiondate

    cycle_time_days: float | None       # done_at - started_at
    lead_time_days: float | None        # done_at - created_at
    rework_count: int                   # count of backward status transitions
    assignee_churn: int                 # count of assignee changes

    blocked_by: list[str] = field(default_factory=list)

    rice_reach: int = 0
    rice_impact: float = 0
    rice_confidence: float = 0
    rice_effort: float = 1
    okr_tag: str = ""

    sprint_name: str = ""
    sprint_state: str = ""

    fix_version: str = ""
    release_slipped: bool = False
    original_fix_version: str = ""

    priority: str = ""
    severity: str | None = None       # bug-only; None for non-bug issue types
    resolution: str | None = None     # None while unresolved
    affects_version: str | None = None  # bug or support-ticket; where it was actually found

    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    related_to: list[str] = field(default_factory=list)  # "Relates" links — dependency graph, not blocking

    # Approval flow (BA requirements + Design) — derived from changelog,
    # not a native field (see _derive_flow_metrics)
    approved_at: datetime | None = None
    time_to_approval_days: float | None = None

    # BA-specific
    requirement_change_count: int = 0  # description-change events — feeds "requirements stability"

    # SA-specific (Analysis squad's "task" issues only — see jira_mock_raw.py)
    spec_completeness: int | None = None
    ambiguity_questions: int | None = None
    dependency_documented: bool | None = None
    has_external_dependency: bool | None = None
    api_contract_changes: int = 0

    # ADR-specific (issue_type == "adr")
    adr_context: str | None = None
    adr_options: str | None = None
    adr_decision: str | None = None
    adr_consequences: str | None = None
    adr_status: str | None = None

    # Design-specific (issue_type == "design")
    iteration_count: int | None = None
    accessibility_checked: bool | None = None

    @property
    def escaped_to_prod(self) -> bool:
        """
        A bug counts as "escaped" if it surfaced in the Monitoring squad
        (i.e. found post-release) rather than the Quality squad (caught
        pre-release). This is the mechanism, not a separate flag — squad
        assignment already encodes when/where the bug was found.
        """
        return self.issue_type == "bug" and self.squad_key == "MONITORING"

    @property
    def is_beta(self) -> bool:
        """Bug reported via the Beta program — tracked via components,
        not squad (a beta bug can still be caught pre- or post-release)."""
        return "Beta Program" in self.components

    # type-specific, populated only when relevant, None otherwise
    hypothesis: str | None = None
    research_method: str | None = None
    research_metric: str | None = None
    insight: str | None = None
    decision: str | None = None
    variant_a: str | None = None
    variant_b: str | None = None
    experiment_result: str | None = None
    requirement_source: str | None = None

    @property
    def rice_score(self) -> float:
        if not self.rice_effort:
            return 0.0
        return round(
            (self.rice_reach * self.rice_impact * self.rice_confidence) / self.rice_effort, 2
        )


def _derive_flow_metrics(raw_issue: dict) -> dict:
    """
    Walks the changelog once and extracts everything that isn't a native
    Jira field: when work actually started, how many times it bounced
    backward (rework), and how many times the assignee changed.
    """
    histories = raw_issue["changelog"]["histories"]
    started_at: datetime | None = None
    rework_count = 0
    assignee_churn = 0
    release_slips: list[tuple[str, str]] = []  # (from, to) pairs, in order
    approved_at: datetime | None = None
    requirement_change_count = 0
    api_contract_changes = 0

    for event in histories:
        for item in event["items"]:
            if item["field"] == "status":
                from_idx = WORKFLOW_INDEX.get(item["fromString"])
                to_idx = WORKFLOW_INDEX.get(item["toString"])
                ts = _parse_iso(event["created"])

                if to_idx == WORKFLOW_INDEX["In Progress"] and started_at is None:
                    started_at = ts

                if from_idx is not None and to_idx is not None and to_idx < from_idx:
                    rework_count += 1

            elif item["field"] == "assignee":
                assignee_churn += 1

            elif item["field"] == "Fix Version":
                release_slips.append((item["fromString"], item["toString"]))

            elif item["field"] == "Approval":
                approved_at = _parse_iso(event["created"])

            elif item["field"] == "description":
                requirement_change_count += 1

            elif item["field"] == "API Contract":
                api_contract_changes += 1

    return {
        "started_at": started_at,
        "rework_count": rework_count,
        "assignee_churn": assignee_churn,
        "release_slips": release_slips,
        "approved_at": approved_at,
        "requirement_change_count": requirement_change_count,
        "api_contract_changes": api_contract_changes,
    }


def adapt_issue(raw: dict) -> Issue:
    fields = raw["fields"]
    flow = _derive_flow_metrics(raw)

    created_at = _parse_iso(fields["created"])
    done_at = _parse_iso(fields["resolutiondate"])
    started_at = flow["started_at"]

    cycle_time = (
        (done_at - started_at).total_seconds() / 86400
        if done_at and started_at else None
    )
    lead_time = (
        (done_at - created_at).total_seconds() / 86400
        if done_at and created_at else None
    )

    blocked_by = [
        link["inwardIssue"]["key"]
        for link in raw.get("issuelinks", [])
        if link["type"]["name"] == "Blocks" and "inwardIssue" in link
    ]
    related_to = [
        link["outwardIssue"]["key"]
        for link in raw.get("issuelinks", [])
        if link["type"]["name"] == "Relates" and "outwardIssue" in link
    ]

    sprint_entries = fields.get(CF_SPRINT) or []
    latest_sprint = sprint_entries[-1] if sprint_entries else {}

    fix_versions = fields.get("fixVersions") or []
    current_fix_version = fix_versions[-1]["name"] if fix_versions else ""
    release_slips = flow["release_slips"]
    original_fix_version = release_slips[0][0] if release_slips else current_fix_version

    priority = fields.get("priority", {}).get("name", "")
    resolution = fields.get("resolution")
    resolution_name = resolution["name"] if resolution else None
    severity = fields.get(CF_SEVERITY)  # None for non-bug issue types

    affects_versions = fields.get("versions") or []
    affects_version = affects_versions[-1]["name"] if affects_versions else None

    labels = fields.get("labels") or []
    components = [c["name"] for c in (fields.get("components") or [])]

    approved_at = flow["approved_at"]
    time_to_approval = (
        (approved_at - created_at).total_seconds() / 86400
        if approved_at and created_at else None
    )

    return Issue(
        key=raw["key"],
        squad_key=raw["_squad_key"],
        epic=fields.get(CF_EPIC_LINK, ""),
        issue_type=fields["issuetype"]["name"],
        status=fields["status"]["name"],
        assignee=fields["assignee"]["displayName"],
        story_points=fields.get(CF_STORY_POINTS, 0),
        created_at=created_at,
        started_at=started_at,
        done_at=done_at,
        cycle_time_days=round(cycle_time, 1) if cycle_time is not None else None,
        lead_time_days=round(lead_time, 1) if lead_time is not None else None,
        rework_count=flow["rework_count"],
        assignee_churn=flow["assignee_churn"],
        blocked_by=blocked_by,
        rice_reach=fields.get(CF_RICE_REACH, 0),
        rice_impact=fields.get(CF_RICE_IMPACT, 0),
        rice_confidence=fields.get(CF_RICE_CONFIDENCE, 0),
        rice_effort=fields.get(CF_RICE_EFFORT, 1),
        okr_tag=fields.get(CF_OKR_TAG, ""),
        sprint_name=latest_sprint.get("name", ""),
        sprint_state=latest_sprint.get("state", ""),
        fix_version=current_fix_version,
        release_slipped=len(release_slips) > 0,
        original_fix_version=original_fix_version,
        priority=priority,
        severity=severity,
        resolution=resolution_name,
        affects_version=affects_version,
        labels=labels,
        components=components,
        related_to=related_to,
        approved_at=approved_at,
        time_to_approval_days=round(time_to_approval, 1) if time_to_approval is not None else None,
        requirement_change_count=flow["requirement_change_count"],
        spec_completeness=fields.get(CF_SPEC_COMPLETENESS),
        ambiguity_questions=fields.get(CF_AMBIGUITY_QUESTIONS),
        dependency_documented=fields.get(CF_DEPENDENCY_DOCUMENTED),
        has_external_dependency=fields.get(CF_HAS_EXTERNAL_DEPENDENCY),
        api_contract_changes=flow["api_contract_changes"],
        adr_context=fields.get(CF_ADR_CONTEXT),
        adr_options=fields.get(CF_ADR_OPTIONS),
        adr_decision=fields.get(CF_ADR_DECISION),
        adr_consequences=fields.get(CF_ADR_CONSEQUENCES),
        adr_status=fields.get(CF_ADR_STATUS),
        iteration_count=fields.get(CF_ITERATION_COUNT),
        accessibility_checked=fields.get(CF_ACCESSIBILITY_CHECKED),
        hypothesis=fields.get(CF_HYPOTHESIS),
        research_method=fields.get(CF_RESEARCH_METHOD),
        research_metric=fields.get(CF_RESEARCH_METRIC),
        insight=fields.get(CF_INSIGHT),
        decision=fields.get(CF_DECISION),
        variant_a=fields.get(CF_VARIANT_A),
        variant_b=fields.get(CF_VARIANT_B),
        experiment_result=fields.get(CF_EXPERIMENT_RESULT),
        requirement_source=fields.get(CF_REQUIREMENT_SOURCE),
    )


def load_issues(config: ProjectConfig = MOTIF_DEMO_CONFIG) -> list[Issue]:
    """
    The single function every dashboard tab should call. Swap `config`
    for a different ProjectConfig to simulate an entirely different
    project through the exact same pipeline.
    DASH_CONFIG is special: uses hand-authored get_dash_issues() instead of the random generator.
    """
    if config.project_key == "DASH":
        raw_issues = get_dash_issues()
    else:
        raw_issues = generate_raw_issues(config)
    return [adapt_issue(raw) for raw in raw_issues]


def list_releases(config: ProjectConfig = MOTIF_DEMO_CONFIG):
    """
    Release history for the Release tab — includes rolled_back. Already
    clean (no changelog/customfield parsing needed), so this is a direct
    pass-through rather than a full adapt step.
    """
    return get_releases(config)
