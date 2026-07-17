"""
Raw Jira mock layer — "Extract" stage of our mini-ETL.

Generates data shaped the way the real Jira Cloud REST API actually
returns it: verbose, nested, custom fields keyed by instance-specific
customfield_XXXXX IDs, changelog as a list of per-field transition
events, and issuelinks as a separate structure from changelog.

This layer knows NOTHING about "cycle time" or "rework rate" — those are
derived concepts, not things Jira gives you. That derivation lives in
adapter.py (the "Transform" stage). This file only produces data that
looks like what /rest/api/3/search or /rest/api/3/issue/{key} would
actually return, so the adapter has something realistic to parse.

Reusability: nothing here references Knowledge Pipeline. Everything is
driven by a ProjectConfig — swap it for a different project (different
key prefix, different squads, different MVP scope) and you get a
different, unrelated mock dataset from the same code.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Jira's real customfield ID convention: instance-specific, opaque numbers.
# We fix a set here so the mock is internally consistent (a real project
# would look these up once via /rest/api/3/field/search).
# ---------------------------------------------------------------------------

CF_STORY_POINTS = "customfield_10001"
CF_SPRINT = "customfield_10002"
CF_EPIC_LINK = "customfield_10003"
CF_RICE_REACH = "customfield_10101"
CF_RICE_IMPACT = "customfield_10102"
CF_RICE_CONFIDENCE = "customfield_10103"
CF_RICE_EFFORT = "customfield_10104"
CF_OKR_TAG = "customfield_10105"
# research-spike-specific fields
CF_HYPOTHESIS = "customfield_10201"
CF_RESEARCH_METHOD = "customfield_10202"
CF_RESEARCH_METRIC = "customfield_10203"
CF_INSIGHT = "customfield_10204"
CF_DECISION = "customfield_10205"
# experiment-specific fields
CF_VARIANT_A = "customfield_10301"
CF_VARIANT_B = "customfield_10302"
CF_EXPERIMENT_RESULT = "customfield_10303"
# BA/SA-specific fields
CF_REQUIREMENT_SOURCE = "customfield_10401"
CF_SPEC_COMPLETENESS = "customfield_10402"
CF_AMBIGUITY_QUESTIONS = "customfield_10403"
CF_DEPENDENCY_DOCUMENTED = "customfield_10404"
CF_HAS_EXTERNAL_DEPENDENCY = "customfield_10405"
# ADR-specific (Architecture)
CF_ADR_CONTEXT = "customfield_10601"
CF_ADR_OPTIONS = "customfield_10602"
CF_ADR_DECISION = "customfield_10603"
CF_ADR_CONSEQUENCES = "customfield_10604"
CF_ADR_STATUS = "customfield_10605"  # Proposed/Accepted/Superseded — ADR lifecycle, separate from issue workflow status
# Design-specific
CF_ITERATION_COUNT = "customfield_10701"
CF_ACCESSIBILITY_CHECKED = "customfield_10702"
# Bug-specific: Jira has no native Severity field (dropped by design —
# see Priority below); teams that want it add it as a custom field.
CF_SEVERITY = "customfield_10501"

# Priority IS native (unlike Severity) — applies to every issue type,
# not just bugs. Business urgency, can change over time.
PRIORITIES = ["Highest", "High", "Medium", "Low", "Lowest"]

# Severity — custom field, bug-specific only. Objective technical impact,
# doesn't change once assessed (unlike priority).
SEVERITIES = ["Blocker", "Critical", "Major", "Minor", "Trivial"]

# Resolution — native field, separate from status. How the issue was
# actually closed. Matters for bug stats: counting "Won't Fix" or
# "Duplicate" as if they were real fixed defects would inflate escape
# rate with noise.
RESOLUTIONS_POSITIVE = ["Fixed", "Done"]
RESOLUTIONS_OTHER = ["Won't Fix", "Duplicate", "Cannot Reproduce"]

ADR_STATUSES = ["Proposed", "Accepted", "Superseded"]

# Real ADRs from Knowledge Pipeline's own README — used instead of inventing
# generic mock decisions, so the Architecture tab shows genuine content.
REAL_ADR_TOPICS = [
    ("Fallback chain для видео без субтитров", "yt-dlp транскрипция как запасной путь"),
    ("Идемпотентность обработки батчей", "хэш URL как ключ дедупликации"),
    ("Chunking длинных транскриптов", "разбиение по токен-лимиту перед LLM-обогащением"),
]

LABELS_POOL = ["tech-debt", "needs-refactor", "quick-win", "blocked-by-external"]


# ---------------------------------------------------------------------------
# Project configuration — this is what makes the generator reusable for
# any project, not just Knowledge Pipeline.
# ---------------------------------------------------------------------------

@dataclass
class SquadConfig:
    key: str                 # e.g. "RESEARCH" — internal id, not shown in UI
    name: str                # e.g. "Research"
    stage_order: int         # position in the SDLC pipeline (0-indexed)
    sprint_length_days: int  # must be a multiple of 7
    issue_types: list[str]   # which issue types this squad produces


@dataclass
class ProjectConfig:
    project_key: str          # Jira key prefix, e.g. "KP"
    project_name: str
    mvp_start: datetime
    mvp_deadline: datetime
    total_scope: int          # e.g. 2000 URLs for Knowledge Pipeline
    north_star_metric: str
    squads: list[SquadConfig]
    seed: int = 42             # reproducible randomness


# Default config for Motif demo team — NOT hardcoded into the generator,
# just the default argument. Any other ProjectConfig works identically.
MOTIF_DEMO_CONFIG = ProjectConfig(
    project_key="MTF",
    project_name="Motif",
    mvp_start=datetime(2026, 4, 1),
    mvp_deadline=datetime(2026, 8, 15),
    total_scope=5000,
    north_star_metric="Активных пользователей завершивших первый скетч",
    squads=[
        SquadConfig("RESEARCH", "Research", 0, 7, ["research-spike"]),
        SquadConfig("ARCHITECTURE", "Architecture", 1, 14, ["task", "story", "adr"]),
        SquadConfig("ANALYSIS", "Analysis", 2, 14, ["requirement", "task"]),
        SquadConfig("DESIGN", "Design", 3, 7, ["story", "task", "design"]),
        SquadConfig("DEV", "Development & Pipeline", 4, 7, ["story", "bug", "task"]),
        SquadConfig("QUALITY", "Quality", 5, 7, ["bug", "task"]),
        SquadConfig("RELEASE", "Instructions & Release", 6, 7, ["task"]),
        SquadConfig("MONITORING", "Monitoring & Support", 7, 7, ["bug", "task", "support-ticket"]),
        SquadConfig("GROWTH", "Growth", 8, 14, ["experiment", "task"]),
        SquadConfig("PM", "Product Management", 9, 14, ["task", "story"]),
    ],
)


# ---------------------------------------------------------------------------
# Status workflow — order matters: a transition to an EARLIER status than
# the issue has already reached is what we count as "rework" (a bounce
# backward), not just any status change.
# ---------------------------------------------------------------------------

WORKFLOW = ["To Do", "In Progress", "In Review", "Done"]
WORKFLOW_INDEX = {status: i for i, status in enumerate(WORKFLOW)}

# Real Jira has exactly 3 status categories (To Do / In Progress / Done —
# hardcoded, cannot be customized). "In Review" maps to the same category
# as "In Progress" in most real workflows. We deliberately do NOT use
# statusCategory for rework detection below — it's too coarse (an
# In Review -> In Progress bounce, the most common real rework case,
# wouldn't register as a category change at all). Full status order is
# what practitioners actually use for this. statusCategory is still
# included on the mock issue for realism / in case a tab wants to filter
# by it the way JQL's statusCategory=Done would.
STATUS_CATEGORY = {
    "To Do": {"id": 2, "key": "new", "name": "To Do"},
    "In Progress": {"id": 4, "key": "indeterminate", "name": "In Progress"},
    "In Review": {"id": 4, "key": "indeterminate", "name": "In Progress"},
    "Done": {"id": 3, "key": "done", "name": "Done"},
}

ISSUE_LINK_TYPES = [
    ("Blocks", "blocks", "is blocked by"),
    ("Relates", "relates to", "relates to"),
]

PEOPLE = ["Гузель", "SA-контур", "QA-бот", "Dev-контур", "Research-контур"]


# ---------------------------------------------------------------------------
# Releases (Jira "Version" objects). fixVersions is a NATIVE Jira field
# (not a customfield) — an array, though in practice usually holds one
# entry. "Release slip" (a task bumped to a later release) shows up as a
# changelog event with field "Fix Version", exactly like a status change.
# ---------------------------------------------------------------------------

@dataclass
class Release:
    id: int
    name: str
    release_date: datetime
    released: bool
    rolled_back: bool = False


def _generate_releases(config: ProjectConfig) -> list[Release]:
    rng = random.Random(config.seed + 2)
    releases = []
    cursor = config.mvp_start + timedelta(days=14)
    i = 1
    while cursor <= config.mvp_deadline:
        released = cursor < config.mvp_deadline
        releases.append(Release(
            id=i,
            name=f"Release {cursor.date()}",
            release_date=cursor,
            released=released,  # simplistic: past releases are "released"
            rolled_back=released and rng.random() < 0.1,
        ))
        cursor += timedelta(days=14)
        i += 1
    return releases


def _release_dict(r: Release) -> dict:
    return {
        "id": r.id, "name": r.name, "releaseDate": _iso(r.release_date),
        "released": r.released, "rolledBack": r.rolled_back,
    }


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def _gen_changelog(
    rng: random.Random,
    created: datetime,
    final_status: str,
) -> tuple[list[dict], datetime | None]:
    """
    Simulates the realistic messiness of a Jira changelog: an issue doesn't
    move cleanly To Do -> In Progress -> Done. It bounces backward
    sometimes (rework), and the assignee sometimes changes mid-flight.

    Returns (histories, last_transition_timestamp). The caller uses the
    timestamp as resolutiondate when final_status == "Done" — this keeps
    resolutiondate consistent with what the changelog actually shows,
    instead of picking it independently and risking a mismatch.
    """
    histories: list[dict] = []
    current = created
    current_status = "To Do"
    current_assignee = rng.choice(PEOPLE)
    target_index = WORKFLOW_INDEX[final_status]

    if target_index == 0:
        # Issue never left the backlog — no transitions to log.
        return histories, None

    step = 0
    last_forward_ts: datetime | None = None
    while WORKFLOW_INDEX[current_status] < target_index:
        current += timedelta(hours=rng.randint(4, 72))

        # 15% chance of bouncing one step backward before moving forward
        if rng.random() < 0.15 and WORKFLOW_INDEX[current_status] > 0:
            new_index = WORKFLOW_INDEX[current_status] - 1
        else:
            new_index = min(WORKFLOW_INDEX[current_status] + 1, target_index)

        new_status = WORKFLOW[new_index]
        histories.append({
            "created": _iso(current),
            "items": [{"field": "status", "fieldtype": "jira", "fieldId": "status", "fromString": current_status, "toString": new_status}],
        })
        current_status = new_status
        if new_index == target_index:
            last_forward_ts = current
        step += 1
        if step > 12:  # safety valve — force-finish rather than leave dangling
            if current_status != final_status:
                current += timedelta(hours=rng.randint(4, 72))
                histories.append({
                    "created": _iso(current),
                    "items": [{"field": "status", "fieldtype": "jira", "fieldId": "status", "fromString": current_status, "toString": final_status}],
                })
                last_forward_ts = current
            break

        # 20% chance the assignee changes at this point too
        if rng.random() < 0.2:
            new_assignee = rng.choice([p for p in PEOPLE if p != current_assignee])
            current += timedelta(hours=rng.randint(1, 24))
            histories.append({
                "created": _iso(current),
                "items": [{"field": "assignee", "fieldtype": "jira", "fieldId": "assignee", "fromString": current_assignee, "toString": new_assignee}],
            })
            current_assignee = new_assignee

    return histories, last_forward_ts


def _issue_type_extra_fields(rng: random.Random, issue_type: str, squad_key: str) -> dict:
    if issue_type == "research-spike":
        return {
            CF_HYPOTHESIS: rng.choice([
                "Если добавить фильтр по source_type, пользователь быстрее найдёт заметку",
                "Явный CTA на пустом состоянии повысит частоту первого действия",
                "Группировка по темам снизит время поиска нужной заметки",
            ]),
            CF_RESEARCH_METHOD: rng.choice(["Task-based usability test", "A/B тест", "Опрос"]),
            CF_RESEARCH_METRIC: rng.choice(["Task Success Rate", "Time on task", "SUS score"]),
            CF_INSIGHT: rng.choice([
                "80% не заметили фильтр с первого раза",
                "Пользователи ожидали группировку по дате, а не по теме",
                None,
            ]),
            CF_DECISION: rng.choice(["Применено", "В работе", None]),
        }
    if issue_type == "experiment":
        return {
            CF_VARIANT_A: "Контроль",
            CF_VARIANT_B: rng.choice(["Новый onboarding", "Альтернативный folder_examples.yml"]),
            CF_EXPERIMENT_RESULT: rng.choice(["Вариант B лучше", "Без значимой разницы", None]),
        }
    if issue_type == "requirement":
        return {
            CF_REQUIREMENT_SOURCE: rng.choice(["Research insight", "Стейкхолдер", "PM decision"]),
        }
    if issue_type == "adr":
        topic, decision = rng.choice(REAL_ADR_TOPICS)
        return {
            "summary": f"ADR: {topic}",
            CF_ADR_CONTEXT: f"Нужно было решить: {topic.lower()}",
            CF_ADR_OPTIONS: "Рассмотрено 2-3 альтернативы (см. README)",
            CF_ADR_DECISION: decision,
            CF_ADR_CONSEQUENCES: rng.choice([
                "Упростило дальнейшую поддержку", "Добавило зависимость от внешнего инструмента", None,
            ]),
            CF_ADR_STATUS: rng.choices(ADR_STATUSES, weights=[1, 5, 1])[0],
        }
    if issue_type == "design" and squad_key == "DESIGN":
        return {
            CF_ITERATION_COUNT: rng.randint(1, 5),
            CF_ACCESSIBILITY_CHECKED: rng.random() < 0.6,
        }
    if issue_type == "task" and squad_key == "ANALYSIS":
        # This models SA (Systems Analyst) spec-writing work specifically —
        # not every "task" in every squad, only Analysis squad's tasks.
        return {
            CF_SPEC_COMPLETENESS: rng.choice([60, 70, 80, 90, 100]),
            CF_AMBIGUITY_QUESTIONS: rng.choice([0, 0, 1, 2, 3, 5]),
            CF_DEPENDENCY_DOCUMENTED: rng.random() < 0.75,
            CF_HAS_EXTERNAL_DEPENDENCY: rng.random() < 0.4,
        }
    if issue_type == "support-ticket":
        return {
            "summary": "Support: обращение пользователя",
        }
    return {}


def get_releases(config: ProjectConfig = MOTIF_DEMO_CONFIG) -> list[Release]:
    """Public accessor for the Release tab — exposes rolled_back etc."""
    return _generate_releases(config)


def generate_raw_issues(config: ProjectConfig = MOTIF_DEMO_CONFIG) -> list[dict]:
    """
    Returns a list of issues in (approximately) Jira Cloud REST API shape:
    { "key": ..., "fields": {...}, "changelog": {"histories": [...]}, ... }
    """
    rng = random.Random(config.seed)
    releases = _generate_releases(config)
    issues: list[dict] = []
    issue_counter = 100
    all_keys: list[str] = []

    def _target_release(after: datetime) -> Release | None:
        for r in releases:
            if r.release_date >= after:
                return r
        return releases[-1] if releases else None

    for squad in config.squads:
        n_issues = rng.randint(8, 14)

        # RICE and OKR are epic-level facts, not per-task. Generate once
        # per squad's epic so every issue under it shares the same score —
        # a real RICE score belongs to the feature, not each ticket in it.
        epic_key = f"{config.project_key}-EPIC-{squad.stage_order + 1}"
        epic_rice = {
            CF_RICE_REACH: rng.randint(1, 10),
            CF_RICE_IMPACT: rng.choice([0.25, 0.5, 1, 2, 3]),
            CF_RICE_CONFIDENCE: rng.choice([0.5, 0.8, 1.0]),
            CF_RICE_EFFORT: rng.choice([1, 2, 3, 5, 8]),
        }
        epic_okr_tag = rng.choice([
            "Рост охвата контента", "Снижение needs_review", "Скорость обработки",
        ])

        for _ in range(n_issues):
            issue_counter += 1
            key = f"{config.project_key}-{issue_counter}"
            all_keys.append(key)

            issue_type = rng.choice(squad.issue_types)
            created = config.mvp_start + timedelta(
                days=squad.stage_order * 7 + rng.randint(0, 10)
            )
            is_done = rng.random() < 0.7
            final_status = "Done" if is_done else rng.choice(["To Do", "In Progress", "In Review"])

            changelog, resolved_ts = _gen_changelog(rng, created, final_status)
            resolved = resolved_ts if final_status == "Done" else None

            # Release assignment + possible slip to a later release.
            original_release = _target_release(created + timedelta(days=10))
            final_release = original_release
            if original_release and rng.random() < 0.18:
                idx = releases.index(original_release)
                if idx + 1 < len(releases):
                    final_release = releases[idx + 1]
                    slip_ts = original_release.release_date - timedelta(days=rng.randint(1, 4))
                    changelog.append({
                        "created": _iso(slip_ts),
                        "items": [{
                            "field": "Fix Version", "fieldtype": "jira", "fieldId": "fixVersions",
                            "fromString": original_release.name, "toString": final_release.name,
                        }],
                    })
                    changelog.sort(key=lambda h: h["created"])

            # Approval changelog — real Jira teams often track this as a
            # custom transition/field rather than a native field. Applies
            # to requirement (BA) and design issues: gives us
            # "time to approved requirement/design".
            approved_at: datetime | None = None
            if issue_type in ("requirement", "design") and rng.random() < 0.7:
                approved_at = created + timedelta(days=rng.randint(2, 10))
                changelog.append({
                    "created": _iso(approved_at),
                    "items": [{
                        "field": "Approval", "fieldtype": "custom", "fieldId": "approval_status",
                        "fromString": "Pending", "toString": "Approved",
                    }],
                })

            # Requirement text changes ("description" changelog field is a
            # real native Jira field name) — feeds requirements stability
            # and change request rate for BA.
            if issue_type == "requirement":
                n_changes = rng.choices([0, 1, 2, 3], weights=[5, 3, 1, 1])[0]
                for _ in range(n_changes):
                    change_ts = created + timedelta(days=rng.randint(1, 20))
                    changelog.append({
                        "created": _iso(change_ts),
                        "items": [{
                            "field": "description", "fieldtype": "jira", "fieldId": "description",
                            "fromString": "(предыдущая версия текста)", "toString": "(обновлённый текст)",
                        }],
                    })

            # API Contract stability — SA (Analysis squad tasks) and DEV
            # story work. Modeled the same way as a Fix Version slip: a
            # changelog event on a custom-tracked field, not a native one
            # (Jira has no built-in "API contract" field — teams that
            # track this add it themselves, often as a changelog-style log).
            if issue_type in ("task", "story") and squad.key in ("ANALYSIS", "DEV") and rng.random() < 0.2:
                contract_change_ts = created + timedelta(days=rng.randint(3, 15))
                changelog.append({
                    "created": _iso(contract_change_ts),
                    "items": [{
                        "field": "API Contract", "fieldtype": "custom", "fieldId": "api_contract_version",
                        "fromString": "v1", "toString": "v2",
                    }],
                })
                changelog.sort(key=lambda h: h["created"])

            changelog.sort(key=lambda h: h["created"])

            # "versions" (Affects Version/s — real API field name, NOT
            # "affectsVersion") — bugs AND support tickets: a support
            # ticket also "affects" whichever release was live when the
            # user hit the problem, which lets us later correlate ticket
            # volume with releases.
            affects_versions: list[dict] = []
            if issue_type in ("bug", "support-ticket") and final_release:
                if squad.key == "MONITORING":
                    idx = releases.index(final_release)
                    shipped_release = releases[idx - 1] if idx > 0 else final_release
                    affects_versions = [_release_dict(shipped_release)]
                else:
                    affects_versions = [_release_dict(final_release)]

            # labels — native array field. tech-debt tagging lives here;
            # Jira has no dedicated built-in field for tech debt, teams
            # tag it via labels in practice.
            labels: list[str] = []
            if squad.key in ("ARCHITECTURE", "DEV") and rng.random() < 0.15:
                labels.append(rng.choice(LABELS_POOL))

            # components — native array field, distinct from labels. Used
            # here to mark bugs found via the Beta program, separate from
            # the squad-based escaped/caught distinction already in place.
            components: list[str] = []
            if issue_type == "bug" and rng.random() < 0.15:
                components.append("Beta Program")

            days_since_start = (created - config.mvp_start).days
            sprint_index = max(1, days_since_start // squad.sprint_length_days + 1)
            sprint_start = config.mvp_start + timedelta(
                days=(sprint_index - 1) * squad.sprint_length_days
            )
            sprint_end = sprint_start + timedelta(days=squad.sprint_length_days)

            issue = {
                "key": key,
                "fields": {
                    "summary": f"{squad.name}: задача {issue_counter}",
                    "issuetype": {"name": issue_type},
                    "status": {"name": final_status, "statusCategory": STATUS_CATEGORY[final_status]},
                    "assignee": {"displayName": rng.choice(PEOPLE)},
                    "created": _iso(created),
                    "updated": _iso(resolved or created),
                    "resolutiondate": _iso(resolved) if resolved else None,
                    "fixVersions": [_release_dict(final_release)] if final_release else [],
                    "versions": affects_versions,
                    "labels": labels,
                    "components": [{"name": c} for c in components],
                    CF_STORY_POINTS: rng.choice([1, 2, 3, 5, 8]),
                    "priority": {"name": rng.choice(PRIORITIES)},
                    "resolution": (
                        {"name": rng.choice(RESOLUTIONS_POSITIVE if rng.random() < 0.85 else RESOLUTIONS_OTHER)}
                        if is_done else None
                    ),
                    **({CF_SEVERITY: rng.choice(SEVERITIES)} if issue_type == "bug" else {}),
                    CF_SPRINT: [{
                        "id": sprint_index,
                        "name": f"{squad.name} Sprint {sprint_index}",
                        # Some not-done issues belong to already-closed sprints
                        # (missed the sprint, carried over). Without this, predictability
                        # is trivially 100% because only Done issues get "closed" state.
                        "state": "closed" if (is_done or rng.random() < 0.5) else "active",
                        "startDate": _iso(sprint_start),
                        "endDate": _iso(sprint_end),
                    }],
                    CF_EPIC_LINK: epic_key,
                    CF_RICE_REACH: epic_rice[CF_RICE_REACH],
                    CF_RICE_IMPACT: epic_rice[CF_RICE_IMPACT],
                    CF_RICE_CONFIDENCE: epic_rice[CF_RICE_CONFIDENCE],
                    CF_RICE_EFFORT: epic_rice[CF_RICE_EFFORT],
                    CF_OKR_TAG: epic_okr_tag,
                    **_issue_type_extra_fields(rng, issue_type, squad.key),
                },
                "changelog": {"histories": changelog},
                "issuelinks": [],  # populated in a second pass below
                "_squad_key": squad.key,  # not a real Jira field; carried for the adapter's convenience
            }
            issues.append(issue)

    # Second pass: wire up cross-squad links. "Blocks" simulates real
    # dependencies that delay work; "Relates" simulates a general
    # component dependency graph (Architecture's "dependency graph"
    # metric) without implying a blocking relationship.
    rng2 = random.Random(config.seed + 1)
    for issue in issues:
        if rng2.random() < 0.12 and len(all_keys) > 1:
            blocker = rng2.choice([k for k in all_keys if k != issue["key"]])
            issue["issuelinks"].append({
                "type": {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
                "inwardIssue": {"key": blocker},
            })
        if rng2.random() < 0.1 and len(all_keys) > 1:
            related = rng2.choice([k for k in all_keys if k != issue["key"]])
            issue["issuelinks"].append({
                "type": {"name": "Relates", "inward": "relates to", "outward": "relates to"},
                "outwardIssue": {"key": related},
            })

    return issues


# ---------------------------------------------------------------------------
# DASH project — KP Dashboard as its own product (hand-authored, not generated)
#
# Each issue reflects actual work done (or planned) on this dashboard.
# Assignee "Guzel K." = PM / Product Designer / PA (human decisions).
# Assignee "Claude Code" = Tech Lead / Developer (implementation).
# This is realistic for an AI-assisted solo product project.
# ---------------------------------------------------------------------------

DASH_CONFIG = ProjectConfig(
    project_key="DASH",
    project_name="Product Dashboard",
    mvp_start=datetime(2026, 6, 22),
    mvp_deadline=datetime(2026, 8, 1),
    total_scope=100,
    north_star_metric="Рекрутер понимает продуктовый контекст без объяснений",
    squads=[
        SquadConfig("DISCOVERY",    "Discovery",           0, 7,  ["spike", "task"]),
        SquadConfig("ARCHITECTURE", "Architecture",        1, 14, ["task", "adr"]),
        SquadConfig("DESIGN",       "Design",              2, 7,  ["story", "task"]),
        SquadConfig("DEV",          "Development",         3, 7,  ["story", "bug", "task"]),
        SquadConfig("ANALYSIS",     "Product Analysis",    4, 14, ["spike", "task"]),
    ],
    seed=99,
)

_DASH_SPRINTS = [
    {"id": 1, "name": "Sprint 1 · Discovery",     "state": "closed",
     "startDate": "2026-06-22T10:00:00.000+0000", "endDate": "2026-06-29T10:00:00.000+0000"},
    {"id": 2, "name": "Sprint 2 · Shell & Data",  "state": "closed",
     "startDate": "2026-06-29T10:00:00.000+0000", "endDate": "2026-07-06T10:00:00.000+0000"},
    {"id": 3, "name": "Sprint 3 · Tabs & Multi",  "state": "active",
     "startDate": "2026-07-06T10:00:00.000+0000", "endDate": "2026-07-13T10:00:00.000+0000"},
    {"id": 4, "name": "Sprint 4 · Product & Docs","state": "future",
     "startDate": "2026-07-13T10:00:00.000+0000", "endDate": "2026-07-20T10:00:00.000+0000"},
    {"id": 5, "name": "Sprint 5 · Release",       "state": "future",
     "startDate": "2026-07-20T10:00:00.000+0000", "endDate": "2026-07-27T10:00:00.000+0000"},
]

# Эпики E1-E8 — компонентная нарезка первого месяца (закрыты историей, не переписываем).
# 11.07.2026 на установочной встрече эпики перенарезаны по ценности (DASH-95):
# business-эпик отвечает «что получит зритель кейса», enabler обязан ссылаться
# «разблокирует → …» (SAFe business/enabler epics + ПМ-краш письмо 4-5).
_DASH_EPICS = {
    "E1": "DASH-EPIC-1",   # Discovery & Setup
    "E2": "DASH-EPIC-2",   # Navigation & Shell
    "E3": "DASH-EPIC-3",   # Motif Demo Tabs
    "E4": "DASH-EPIC-4",   # Mock Data Layer
    "E5": "DASH-EPIC-5",   # Multi-Project Architecture
    "E6": "DASH-EPIC-6",   # Real KP Data Integration
    "E7": "DASH-EPIC-7",   # Product Discovery & Documentation
    "E8": "DASH-EPIC-8",   # Release Preparation
    "E9": "DASH-EPIC-9",   # Дизайн-процесс, которым восхищаются (business)
    "E10": "DASH-EPIC-10", # Живая команда и живой бизнес (business)
    "E11": "DASH-EPIC-11", # Зритель понимает кейс (business)
    "E12": "DASH-EPIC-12", # Кейс опубликован (business)
    "E13": "DASH-EPIC-13", # Деплой и инженерная готовность (enabler → E12)
    "E14": "DASH-EPIC-14", # Figma MCP (enabler → E9)
}

EPIC_NAMES: dict[str, str] = {
    "DASH-EPIC-1": "Discovery & Setup",
    "DASH-EPIC-2": "Navigation & Shell",
    "DASH-EPIC-3": "Motif Demo Tabs",
    "DASH-EPIC-4": "Mock Data Layer",
    "DASH-EPIC-5": "Multi-Project Architecture",
    "DASH-EPIC-6": "Real KP Data Integration",
    "DASH-EPIC-7": "Product Discovery & Docs",
    "DASH-EPIC-8": "Release Preparation",
    "DASH-EPIC-9": "Дизайн-процесс, которым восхищаются",
    "DASH-EPIC-10": "Живая команда и живой бизнес",
    "DASH-EPIC-11": "Зритель понимает кейс",
    "DASH-EPIC-12": "Кейс опубликован",
    "DASH-EPIC-13": "Деплой и инженерная готовность",
    "DASH-EPIC-14": "Figma MCP",
}

# Тип эпика: business — ценность зрителю кейса, enabler — разблокирует business-эпик,
# component — историческая компонентная нарезка (до перенарезки 11.07.2026).
EPIC_TYPES: dict[str, str] = {
    "DASH-EPIC-1": "component",
    "DASH-EPIC-2": "component",
    "DASH-EPIC-3": "component",
    "DASH-EPIC-4": "component",
    "DASH-EPIC-5": "component",
    "DASH-EPIC-6": "component",
    "DASH-EPIC-7": "component",
    "DASH-EPIC-8": "component",
    "DASH-EPIC-9": "business",
    "DASH-EPIC-10": "business",
    "DASH-EPIC-11": "business",
    "DASH-EPIC-12": "business",
    "DASH-EPIC-13": "enabler",
    "DASH-EPIC-14": "enabler",
}

# Enabler-эпик обязан явно ссылаться на то, что разблокирует.
EPIC_UNLOCKS: dict[str, str] = {
    "DASH-EPIC-13": "DASH-EPIC-12",  # без деплоя нечего встраивать в Framer
    "DASH-EPIC-14": "DASH-EPIC-9",   # MCP ускоряет hi-fi артефакты + сам по себе плюс в кейс
}

# Эпик → цель (tag из okr_dash.py O0-O3). Раньше у всех задач был один okr_tag —
# теперь разнесено по смыслу эпика (DASH-111). tag = короткая метка в UI,
# okr_title (полное название цели) резолвится в _OKR_TITLES_DASH по этому tag.
EPIC_OKR: dict[str, str] = {
    # компонентная история — сборка самого дашборда
    "DASH-EPIC-1": "O1 · Portfolio",
    "DASH-EPIC-2": "O1 · Portfolio",
    "DASH-EPIC-3": "O1 · Portfolio",
    "DASH-EPIC-4": "O3 · Quality",
    "DASH-EPIC-5": "O1 · Portfolio",
    "DASH-EPIC-6": "O1 · Portfolio",
    "DASH-EPIC-7": "O2 · Design Process",
    "DASH-EPIC-8": "O3 · Quality",
    # ценностные
    "DASH-EPIC-9":  "O2 · Design Process",  # дизайн-процесс
    "DASH-EPIC-10": "O1 · Portfolio",       # живая команда = достоверный контекст
    "DASH-EPIC-11": "O1 · Portfolio",       # комикс = зритель понимает
    "DASH-EPIC-12": "O0 · North Star",      # публикация кейса = путь к офферу
    "DASH-EPIC-13": "O0 · North Star",      # деплой разблокирует публикацию
    "DASH-EPIC-14": "O2 · Design Process",  # Figma MCP питает дизайн-артефакты
}

# Инвариант параллельных словарей: каждый эпик из NAMES обязан иметь тип, и
# наоборот — иначе тип молча пропадёт в UI, а sort бросит эпик в конец.
# Каждый unlocks-таргет и его источник должны существовать в NAMES.
assert set(EPIC_NAMES) == set(EPIC_TYPES), (
    f"EPIC_NAMES vs EPIC_TYPES рассинхронены: "
    f"только в NAMES {set(EPIC_NAMES) - set(EPIC_TYPES)}, "
    f"только в TYPES {set(EPIC_TYPES) - set(EPIC_NAMES)}"
)
for _src, _dst in EPIC_UNLOCKS.items():
    assert _src in EPIC_NAMES and _dst in EPIC_NAMES, (
        f"EPIC_UNLOCKS ссылается на несуществующий эпик: {_src} → {_dst}"
    )
    assert EPIC_TYPES.get(_src) == "enabler", (
        f"EPIC_UNLOCKS[{_src}] задан, но тип эпика не enabler"
    )

# Порядок групп эпиков в списках: business → enabler → component → прочее.
EPIC_TYPE_ORDER: dict[str, int] = {"business": 0, "enabler": 1, "component": 2}


def epic_sort_key(epic_key: str) -> tuple[int, int]:
    """Единый ключ сортировки эпиков: сначала по типу (business→enabler→
    component), внутри группы — по числовому суффиксу (E9, E10…, а не E1, E10)."""
    tail = epic_key.rsplit("-", 1)[-1]
    num = int(tail) if tail.isdigit() else 0
    return (EPIC_TYPE_ORDER.get(EPIC_TYPES.get(epic_key, ""), 3), num)


def _di(
    key: str,
    summary: str,
    status: str,
    issue_type: str,
    squad_key: str,
    epic: str,
    sprint_id: int,
    sp: int,
    assignee: str,
    created: str,
    started: str | None = None,
    resolved: str | None = None,
    labels: list[str] | None = None,
    priority: str = "Medium",
    links: list[dict] | None = None,
    description: str = "",
    decision_note: str = "",
) -> dict:
    """Build a minimal but valid Jira-format issue dict for the DASH project."""
    sprint = next((s for s in _DASH_SPRINTS if s["id"] == sprint_id), _DASH_SPRINTS[0])
    changelog_histories = []
    if started:
        changelog_histories.append({
            "created": started,
            "items": [{"field": "status", "fieldtype": "jira", "fieldId": "status",
                       "fromString": "To Do", "toString": "In Progress"}],
        })
    if resolved and status == "Done":
        changelog_histories.append({
            "created": resolved,
            "items": [{"field": "status", "fieldtype": "jira", "fieldId": "status",
                       "fromString": "In Progress", "toString": "Done"}],
        })
    extra: dict = {}
    if decision_note:
        extra[CF_DECISION] = decision_note
    return {
        "key": key,
        "fields": {
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type},
            "status": {"name": status},
            "priority": {"name": priority},
            "assignee": {"displayName": assignee},
            "reporter": {"displayName": "Guzel K."},
            "created": created,
            "resolutiondate": resolved,
            "labels": labels or [],
            CF_STORY_POINTS: sp,
            CF_SPRINT: [sprint],
            CF_EPIC_LINK: epic,
            CF_RICE_REACH: 5, CF_RICE_IMPACT: 1.0, CF_RICE_CONFIDENCE: 0.8, CF_RICE_EFFORT: sp,
            CF_OKR_TAG: EPIC_OKR.get(epic, "O1 · Portfolio"),
            **extra,
        },
        "changelog": {"histories": changelog_histories},
        "issuelinks": links or [],
        "_squad_key": squad_key,
    }


def get_dash_issues() -> list[dict]:
    """
    Hand-authored Jira issues reflecting actual work on KP Dashboard.
    Timeline extracted from session JSONL (005f3cb3-...).
    """
    issues: list[dict] = []

    # ── Epic 1: Discovery & Setup ─────────────────────────────────────────────
    issues += [
        _di("DASH-1", "Изучить вакансию Coasthill IV и определить концепцию демо",
            "Done", "spike", "DISCOVERY", _DASH_EPICS["E1"], 1, 2, "Guzel K.",
            created="2026-06-22T14:56:00.000+0000",
            started="2026-06-22T15:00:00.000+0000",
            resolved="2026-06-22T17:00:00.000+0000",
            labels=["spike", "discovery"],
            decision_note="Решили не симулировать реальный лейбл, а выбрать похожий домен — Motif (рисование/анимация), чтобы показать PM-навыки без претензии на реальный проект",
            priority="High"),
        _di("DASH-2", "Установить Reflex и создать скелет проекта kp_dashboard",
            "Done", "task", "DISCOVERY", _DASH_EPICS["E1"], 1, 3, "Claude Code",
            created="2026-06-24T00:00:00.000+0000",
            started="2026-06-24T00:05:00.000+0000",
            resolved="2026-06-24T02:00:00.000+0000",
            labels=["setup"]),
        _di("DASH-3", "Определить структуру дашборда: 16 SDLC-вкладок по Product Guild ролям",
            "Done", "spike", "DISCOVERY", _DASH_EPICS["E1"], 1, 3, "Guzel K.",
            created="2026-06-24T01:00:00.000+0000",
            started="2026-06-24T01:30:00.000+0000",
            resolved="2026-06-24T02:00:00.000+0000",
            labels=["spike", "architecture"],
            decision_note="Вкладки = роли в продуктовой команде по SDLC, каждая показывает метрики своей роли. WIP-вкладки показываются серым — рекрутер видит полный SDLC, не только реализованное",
            priority="High"),
    ]

    # ── Epic 2: Navigation & Shell ────────────────────────────────────────────
    issues += [
        _di("DASH-4", "Реализовать боковую панель навигации (sidebar) с табами",
            "Done", "story", "DEV", _DASH_EPICS["E2"], 2, 3, "Claude Code",
            created="2026-07-02T19:00:00.000+0000",
            started="2026-07-02T19:30:00.000+0000",
            resolved="2026-07-02T21:00:00.000+0000",
            labels=[]),
        _di("DASH-5", "Реализовать горизонтальные табы как альтернативу сайдбару",
            "Done", "story", "DEV", _DASH_EPICS["E2"], 2, 2, "Claude Code",
            created="2026-07-02T20:05:00.000+0000",
            started="2026-07-02T20:10:00.000+0000",
            resolved="2026-07-02T22:00:00.000+0000",
            labels=[]),
        _di("DASH-6", "Добавить бургер-кнопку для переключения между вариантами навигации",
            "Done", "task", "DEV", _DASH_EPICS["E2"], 2, 1, "Claude Code",
            created="2026-07-02T20:05:00.000+0000",
            started="2026-07-02T20:20:00.000+0000",
            resolved="2026-07-02T22:30:00.000+0000",
            labels=[]),
        _di("DASH-7", "Добавить дашбоард-заголовок с названием проекта и субтитром",
            "Done", "task", "DEV", _DASH_EPICS["E2"], 2, 1, "Claude Code",
            created="2026-07-02T20:05:00.000+0000",
            started="2026-07-02T20:30:00.000+0000",
            resolved="2026-07-02T23:00:00.000+0000",
            labels=[]),
        _di("DASH-8", "Добавить data_source_badge (мок/реал) к каждой секции данных",
            "Done", "task", "DEV", _DASH_EPICS["E2"], 2, 1, "Claude Code",
            created="2026-07-02T21:00:00.000+0000",
            started="2026-07-02T21:10:00.000+0000",
            resolved="2026-07-02T23:30:00.000+0000",
            labels=[]),
        _di("DASH-9", "Добавить tooltip 'В разработке' для WIP-вкладок в навигации",
            "Done", "task", "DEV", _DASH_EPICS["E2"], 2, 1, "Claude Code",
            created="2026-07-02T22:00:00.000+0000",
            started="2026-07-02T22:10:00.000+0000",
            resolved="2026-07-02T23:00:00.000+0000",
            labels=[],
            decision_note="WIP-вкладки кликабельно отключены (cursor: default) но видны рекрутеру — показывает полный SDLC-охват"),
    ]

    # ── Epic 3: Motif Demo Tabs ───────────────────────────────────────────────
    issues += [
        _di("DASH-10", "Overview tab: Flow Metrics, North Star, Squad Health, OKR, RICE, Gantt",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 2, 8, "Claude Code",
            created="2026-07-02T18:00:00.000+0000",
            started="2026-07-02T18:30:00.000+0000",
            resolved="2026-07-02T23:24:00.000+0000",
            labels=[], priority="High"),
        _di("DASH-11", "Research tab: исследовательский план, статус, usability test results",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 2, 5, "Claude Code",
            created="2026-07-02T23:24:00.000+0000",
            started="2026-07-02T23:30:00.000+0000",
            resolved="2026-07-03T02:00:00.000+0000",
            labels=[]),
        _di("DASH-12", "Analysis tab (BA/SA): реестр требований, RTM, интеграции",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 2, 5, "Claude Code",
            created="2026-07-03T00:00:00.000+0000",
            started="2026-07-03T00:10:00.000+0000",
            resolved="2026-07-03T02:00:00.000+0000",
            labels=[]),
        _di("DASH-13", "Design tab: итерации, rework rate, a11y, handoff статус",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 2, 5, "Claude Code",
            created="2026-07-03T00:00:00.000+0000",
            started="2026-07-03T00:30:00.000+0000",
            resolved="2026-07-03T02:30:00.000+0000",
            labels=[]),
        _di("DASH-14", "Growth tab: AARRR воронка, North Star chart, ICE backlog, эксперименты",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 2, 5, "Claude Code",
            created="2026-07-03T00:00:00.000+0000",
            started="2026-07-03T00:30:00.000+0000",
            resolved="2026-07-03T03:00:00.000+0000",
            labels=[]),
        _di("DASH-15", "Architecture tab: ADR реестр, tech stack, code quality, риски",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T00:00:00.000+0000",
            started="2026-07-03T00:23:00.000+0000",
            resolved="2026-07-03T01:00:00.000+0000",
            labels=[]),
        _di("DASH-16", "Dev & Pipeline tab: velocity, cycle time, pipeline, PR статус",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T01:00:00.000+0000",
            started="2026-07-03T01:10:00.000+0000",
            resolved="2026-07-03T03:00:00.000+0000",
            labels=[]),
        _di("DASH-17", "Quality tab: severity distribution, test coverage, alpha testing, sign-off",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T01:00:00.000+0000",
            started="2026-07-03T01:30:00.000+0000",
            resolved="2026-07-03T03:30:00.000+0000",
            labels=[]),
        _di("DASH-18", "Instructions & Release tab: release checklist, changelog, history",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T01:00:00.000+0000",
            started="2026-07-03T02:00:00.000+0000",
            resolved="2026-07-03T04:00:00.000+0000",
            labels=[]),
        _di("DASH-19", "Monitoring & Support tab: инциденты, SLA, MTTR, uptime",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T01:00:00.000+0000",
            started="2026-07-03T02:00:00.000+0000",
            resolved="2026-07-03T04:30:00.000+0000",
            labels=[]),
        _di("DASH-20", "About project tab: описание проекта, команда, цели",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 3, "Claude Code",
            created="2026-07-03T01:00:00.000+0000",
            started="2026-07-03T02:00:00.000+0000",
            resolved="2026-07-03T03:00:00.000+0000",
            labels=[]),
        _di("DASH-21", "Backlog tab: таблица задач с RICE, фильтрами, группировкой",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T02:00:00.000+0000",
            started="2026-07-03T02:10:00.000+0000",
            resolved="2026-07-03T04:00:00.000+0000",
            labels=[]),
        _di("DASH-22", "Kanban tab: колонки по статусам, WIP-лимиты, карточки",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T02:00:00.000+0000",
            started="2026-07-03T02:30:00.000+0000",
            resolved="2026-07-03T04:30:00.000+0000",
            labels=[]),
        _di("DASH-23", "Design System tab: токены, компоненты, coverage",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 3, "Claude Code",
            created="2026-07-03T02:00:00.000+0000",
            started="2026-07-03T03:00:00.000+0000",
            resolved="2026-07-03T04:00:00.000+0000",
            labels=[]),
        _di("DASH-24", "Info/Practices tab: engineering practices, DoD/DoR, глоссарий",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 3, "Claude Code",
            created="2026-07-03T02:00:00.000+0000",
            started="2026-07-03T03:00:00.000+0000",
            resolved="2026-07-03T04:30:00.000+0000",
            labels=[]),
        _di("DASH-25", "Analytics PA tab: воронка активации, retention, A/B эксперименты",
            "Done", "story", "DEV", _DASH_EPICS["E3"], 3, 5, "Claude Code",
            created="2026-07-03T02:00:00.000+0000",
            started="2026-07-03T03:00:00.000+0000",
            resolved="2026-07-03T05:00:00.000+0000",
            labels=[]),
    ]

    # ── Epic 4: Mock Data Layer ───────────────────────────────────────────────
    issues += [
        _di("DASH-26", "Создать jira_mock_raw.py с ProjectConfig паттерном",
            "Done", "task", "DEV", _DASH_EPICS["E4"], 2, 5, "Claude Code",
            created="2026-07-02T18:00:00.000+0000",
            started="2026-07-02T18:30:00.000+0000",
            resolved="2026-07-02T21:00:00.000+0000",
            labels=["architecture"],
            decision_note="ProjectConfig как dataclass делает генератор переиспользуемым для любого проекта — не хардкодим KP-специфику",
            priority="High"),
        _di("DASH-27", "Создать adapter.py — Transform-слой ETL между raw Jira и UI",
            "Done", "task", "DEV", _DASH_EPICS["E4"], 2, 5, "Claude Code",
            created="2026-07-02T18:00:00.000+0000",
            started="2026-07-02T19:00:00.000+0000",
            resolved="2026-07-02T22:00:00.000+0000",
            labels=["architecture"]),
        _di("DASH-28", "Переименовать KNOWLEDGE_PIPELINE_CONFIG → MOTIF_DEMO_CONFIG",
            "Done", "task", "DEV", _DASH_EPICS["E4"], 3, 1, "Claude Code",
            created="2026-07-07T10:00:00.000+0000",
            started="2026-07-07T10:10:00.000+0000",
            resolved="2026-07-07T10:30:00.000+0000",
            labels=["tech-debt"],
            decision_note="Имя KNOWLEDGE_PIPELINE_CONFIG путало: конфиг описывает демо-команду Motif, а не реальный KP. project_key='MTF', project_name='Motif', total_scope=5000"),
    ]

    # ── Epic 5: Multi-Project Architecture ───────────────────────────────────
    issues += [
        _di("DASH-29", "Создать ProjectState: global state для переключения проектов",
            "Done", "task", "DEV", _DASH_EPICS["E5"], 3, 2, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:10:00.000+0000",
            resolved="2026-07-07T10:00:00.000+0000",
            labels=["architecture"]),
        _di("DASH-30", "Добавить project dropdown в навигацию (sidebar + compact)",
            "Done", "task", "DEV", _DASH_EPICS["E5"], 3, 3, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:30:00.000+0000",
            resolved="2026-07-07T11:00:00.000+0000",
            labels=[]),
        _di("DASH-31", "Реализовать _by_project() роутер (мотиф/kp/dash)",
            "Done", "task", "DEV", _DASH_EPICS["E5"], 3, 3, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:30:00.000+0000",
            resolved="2026-07-07T11:30:00.000+0000",
            labels=["architecture"],
            decision_note="Первые попытки: _real(demo,real) → _for_mode(demo,real,dash) → _by_project(motif,kp,dash). Финальное имя явное: параметры = конкретные проекты, не абстрактные режимы"),
        _di("DASH-32", "Добавить третий режим DASH в project switcher",
            "Done", "task", "DEV", _DASH_EPICS["E5"], 3, 2, "Claude Code",
            created="2026-07-07T10:00:00.000+0000",
            started="2026-07-07T10:10:00.000+0000",
            resolved="2026-07-07T11:00:00.000+0000",
            labels=[]),
        _di("DASH-33", "Рефакторинг router.py: 16-уровневый rx.cond → плоский список",
            "Done", "task", "DEV", _DASH_EPICS["E5"], 3, 3, "Claude Code",
            created="2026-07-03T03:00:00.000+0000",
            started="2026-07-03T03:10:00.000+0000",
            resolved="2026-07-03T04:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="Вложенный rx.cond не читается при 16 вкладках. Плоский список _TAB_ENTRIES + reversed() обход = та же логика, но O(n) читаемость"),
    ]

    # ── Epic 6: Real KP Data Integration ─────────────────────────────────────
    issues += [
        _di("DASH-34", "real_overview_tab: реальные данные KP (vault count, pipeline metrics)",
            "Done", "story", "DEV", _DASH_EPICS["E6"], 2, 5, "Claude Code",
            created="2026-07-02T23:30:00.000+0000",
            started="2026-07-02T23:40:00.000+0000",
            resolved="2026-07-03T01:00:00.000+0000",
            labels=[]),
        _di("DASH-35", "real_architecture_tab: реальные ADR из KP README",
            "Done", "story", "DEV", _DASH_EPICS["E6"], 3, 3, "Claude Code",
            created="2026-07-03T00:30:00.000+0000",
            started="2026-07-03T00:40:00.000+0000",
            resolved="2026-07-03T01:30:00.000+0000",
            labels=[]),
        _di("DASH-36", "real_dev_tab, real_quality_tab, real_release_tab",
            "Done", "story", "DEV", _DASH_EPICS["E6"], 3, 5, "Claude Code",
            created="2026-07-03T01:00:00.000+0000",
            started="2026-07-03T01:30:00.000+0000",
            resolved="2026-07-03T03:00:00.000+0000",
            labels=[]),
        _di("DASH-37", "real_monitoring_tab, real_research_tab, real_design_tab",
            "Done", "story", "DEV", _DASH_EPICS["E6"], 3, 5, "Claude Code",
            created="2026-07-03T01:30:00.000+0000",
            started="2026-07-03T02:00:00.000+0000",
            resolved="2026-07-03T04:00:00.000+0000",
            labels=[]),
        _di("DASH-38", "Добавить empty_state компонент для demo_only / coming_soon режимов",
            "Done", "task", "DEV", _DASH_EPICS["E6"], 3, 2, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:30:00.000+0000",
            resolved="2026-07-07T10:00:00.000+0000",
            labels=[],
            decision_note="Вкладки без данных для реального KP (Kanban, Backlog) объясняют почему: 'В соло-проекте нет командного Jira-процесса'. Это честнее чем просто 'В разработке'"),
    ]

    # ── Epic 7: Product Discovery & Documentation ─────────────────────────────
    issues += [
        _di("DASH-39", "Spike: изучить официальный Scrum-набор issue types в Jira",
            "Done", "spike", "ANALYSIS", _DASH_EPICS["E7"], 3, 3, "Guzel K.",
            created="2026-07-04T10:00:00.000+0000",
            started="2026-07-04T10:30:00.000+0000",
            resolved="2026-07-05T12:00:00.000+0000",
            labels=["spike", "research"],
            decision_note="Atlassian docs: Epic/Story/Task/Bug/Subtask. Sub-task ≠ story в классическом Scrum. Выбрали стандартный набор"),
        _di("DASH-40", "Spike: исследовать жизненный цикл эпиков (Product/Maintenance/Growth)",
            "Done", "spike", "ANALYSIS", _DASH_EPICS["E7"], 3, 3, "Guzel K.",
            created="2026-07-04T12:00:00.000+0000",
            started="2026-07-04T12:30:00.000+0000",
            resolved="2026-07-05T14:00:00.000+0000",
            labels=["spike", "research"],
            decision_note="Product epic — конечный, закрывается после релиза. Maintenance — квартальный цикл. Growth — по метрике AARRR. Баги после закрытого эпика — через Jira links (is caused by)"),
        _di("DASH-41", "Spike: Growth-команда — структура, AARRR, параллельный трек",
            "Done", "spike", "ANALYSIS", _DASH_EPICS["E7"], 3, 2, "Guzel K.",
            created="2026-07-04T14:00:00.000+0000",
            started="2026-07-04T14:30:00.000+0000",
            resolved="2026-07-05T16:00:00.000+0000",
            labels=["spike", "research"],
            decision_note="Amplitude, Reforge, Lenny's Newsletter: Growth — параллельный трек, не стадия SDLC. Работает по воронке AARRR, эпики по метрике"),
        _di("DASH-42", "Spike: Alpha testing — кто владелец (QA vs UX Researcher)",
            "Done", "spike", "ANALYSIS", _DASH_EPICS["E7"], 3, 1, "Guzel K.",
            created="2026-07-05T10:00:00.000+0000",
            started="2026-07-05T10:30:00.000+0000",
            resolved="2026-07-05T11:00:00.000+0000",
            labels=["spike", "research"],
            decision_note="Guru99: Alpha = QA+Dev (не UX Researcher). Prototype testing (с пользователями) → Research tab. Alpha results → Quality tab"),
        _di("DASH-43", "Spike: Roadmap hierarchy — Vision→Goals→Themes→Epics",
            "Done", "spike", "ANALYSIS", _DASH_EPICS["E7"], 3, 2, "Guzel K.",
            created="2026-07-05T11:00:00.000+0000",
            started="2026-07-05T11:30:00.000+0000",
            resolved="2026-07-05T13:00:00.000+0000",
            labels=["spike", "research"],
            decision_note="Aha!, Reforge: один Product Goal на момент времени (Scrum Guide 2020). Roadmap = Goals + Timeline (Initiatives→Epics→Releases) + Sprint Review summary"),
        _di("DASH-44", "Создать USER_STORIES.md: 17 ролей, 100+ User Stories с ✅/🔧/❌",
            "Done", "task", "ANALYSIS", _DASH_EPICS["E7"], 3, 8, "Guzel K.",
            created="2026-07-05T14:00:00.000+0000",
            started="2026-07-06T10:00:00.000+0000",
            resolved="2026-07-07T18:00:00.000+0000",
            labels=["content", "product"],
            priority="High"),
        _di("DASH-45", "Разделить слипшиеся роли в USER_STORIES.md (TL/DevOps, BA/SA, TW/RM)",
            "Done", "task", "ANALYSIS", _DASH_EPICS["E7"], 3, 5, "Guzel K.",
            created="2026-07-07T15:00:00.000+0000",
            started="2026-07-07T15:30:00.000+0000",
            resolved="2026-07-09T12:00:00.000+0000",
            labels=["content"],
            decision_note="Tech Lead ≠ DevOps: TL→архитектурные решения, ADR; DevOps→CI/CD, IaC, мониторинг. BA ≠ SA: BA→бизнес-процессы, BRD; SA→системные спеки, ERD, API-контракты"),
        _di("DASH-46", "Обсудить и согласовать таксономию компонентов/лейблов для DASH-задач",
            "Done", "task", "ANALYSIS", _DASH_EPICS["E7"], 3, 1, "Guzel K.",
            created="2026-07-09T12:00:00.000+0000",
            started="2026-07-09T12:30:00.000+0000",
            resolved="2026-07-09T13:00:00.000+0000",
            labels=["process"],
            decision_note="Компоненты = что затрагивает в коде/продукте. Лейблы = характер задачи. Таксономию можно менять позже — все данные в jira_mock_raw.py, это Python-словари"),
        _di("DASH-47", "Прочитать JSONL истории сессии и создать Jira-задачи для DASH",
            "Done", "task", "ANALYSIS", _DASH_EPICS["E10"], 3, 8, "Claude Code",
            created="2026-07-09T13:00:00.000+0000",
            started="2026-07-09T13:30:00.000+0000",
            resolved="2026-07-12T13:00:00.000+0000",
            labels=["content", "process"],
            priority="High",
            decision_note="Закрыто 12.07 при наведении порядка: DASH-задачи (121 шт.) заведены и ведутся."),
    ]

    # ── Epic 8: Release Preparation (все задачи открыты) ─────────────────────
    issues += [
        _di("DASH-48", "Создать вкладку Roadmap / Stakeholder (Goals, Timeline, Sprint Review summary)",
            "Done", "story", "DEV", _DASH_EPICS["E8"], 3, 8, "Claude Code",
            created="2026-07-05T10:00:00.000+0000",
            started="2026-07-09T10:00:00.000+0000",
            resolved="2026-07-09T12:00:00.000+0000",
            labels=[], priority="High",
            decision_note=(
                "pages/roadmap.py: три секции — Goals·OKR (okr_dash.py), Timeline·Epics, Sprint Review. "
                "data/okr_dash.py: три Objective специально для DASH (O1 Portfolio, O2 Design Process, O3 Quality). "
                "Данные DASH_CONFIG, не MOTIF — соблюдено правило соответствия проекта."
            )),
        _di("DASH-49", "Создать Dev Tech Debt tab (вложена в Backlog)",
            "To Do", "story", "DEV", _DASH_EPICS["E10"], 4, 5, "Claude Code",
            created="2026-07-05T10:00:00.000+0000",
            labels=["❌-missing"]),
        _di("DASH-50", "Создать Design Tech Debt tab (вложена в Backlog)",
            "To Do", "story", "DEV", _DASH_EPICS["E10"], 4, 5, "Claude Code",
            created="2026-07-05T10:00:00.000+0000",
            labels=["❌-missing"]),
        _di("DASH-51", "Переименовать Info → Practices & Rules и переместить сразу после About project",
            "Done", "task", "DEV", _DASH_EPICS["E8"], 4, 1, "Claude Code",
            created="2026-07-05T10:00:00.000+0000",
            started="2026-07-07T10:00:00.000+0000",
            resolved="2026-07-07T12:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="states/__init__.py: tab key 'info', label изменён на 'Practices & Rules', иконка book-open."),
        _di("DASH-52", "Перенести Design System → вложенная под Design",
            "Done", "task", "DEV", _DASH_EPICS["E8"], 4, 4, "Claude Code",
            created="2026-07-05T10:00:00.000+0000",
            started="2026-07-10T10:00:00.000+0000",
            resolved="2026-07-10T10:30:00.000+0000",
            labels=["tech-debt"],
            decision_note="navigation.py: _design_accordion() с chevron + rx.cond для ds sub-item. "
                          "NavState.design_open: bool + toggle_design(). В tabs_nav ds скрыта."),
        _di("DASH-53", "Реализовать онбординг для рекрутера (tooltips, coach marks, progressive disclosure)",
            "To Do", "story", "DEV", _DASH_EPICS["E11"], 4, 8, "Claude Code",
            created="2026-07-05T10:00:00.000+0000",
            labels=["❌-missing", "ux"], priority="High"),
        _di("DASH-54", "Провести Retro → зафиксировать coding rules в CLAUDE.md",
            "Done", "task", "ANALYSIS", _DASH_EPICS["E10"], 4, 3, "Guzel K.",
            created="2026-07-07T12:00:00.000+0000",
            started="2026-07-10T10:00:00.000+0000",
            resolved="2026-07-12T13:00:00.000+0000",
            labels=["process"],
            decision_note="Закрыто 12.07: правило зафиксировано — Claude ведёт актуальность CLAUDE.md "
                          "(retro-выводы DASH-90, релиз-конвенции, DS-канон, критический путь). "
                          "Стало постоянной практикой (feedback-память rules-in-claudemd)."),
        _di("DASH-55", "Подготовить GitHub release: README, demo GIF, публичный репо",
            "Done", "task", "DEV", _DASH_EPICS["E8"], 5, 5, "Guzel K.",
            created="2026-07-07T12:00:00.000+0000",
            started="2026-07-10T14:00:00.000+0000",
            resolved="2026-07-10T16:00:00.000+0000",
            labels=["release"], priority="High",
            decision_note=(
                "git init + явный git add (без git add .) → первый коммит. "
                "gh repo create product-dashboard --public → https://github.com/plaidshirtfemme/product-dashboard. "
                "67 файлов, 13124 строки. Ветка master. "
                "demo GIF — отложен на следующую итерацию после деплоя."
            )),

        # ── North Star ────────────────────────────────────────────────────────
        _di("DASH-56", "Зафиксировать два North Star: продуктовый и портфолийный",
            "Done", "Task", "PM", _DASH_EPICS["E7"], 3, 1, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-09T10:00:00.000+0000",
            resolved="2026-07-09T11:00:00.000+0000",
            labels=["discovery", "process"],
            decision_note=(
                "Продуктовый North Star: «PM и команда всегда понимают статус проекта "
                "и могут эффективно работать». "
                "Портфолийный North Star: «Рекрутер понимает продуктовый контекст без объяснений». "
                "Продуктовый — первичен, определяет что строить. "
                "Портфолийный — определяет как подавать. Оба зафиксированы в CLAUDE.md."
            )),

        # ── Double Diamond: Design Process artifacts ──────────────────────────
        _di("DASH-57", "Journey map: путь рекрутера по дашборду",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E9"], 4, 3, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux", "discovery"],
            description=(
                "Создать Journey map рекрутера: от получения ссылки на дашборд до "
                "понимания продуктового контекста. Шаги: действие, мысли, эмоции, болевые точки. "
                "Хранение: вкладка Design Process в дашборде + Figma."
            )),

        _di("DASH-118", "Research: опыт дизайнеров с Figma MCP — подводные камни, за/против",
            "Done", "Spike", "ANALYSIS", _DASH_EPICS["E14"], 3, 3, "Guzel K.",
            created="2026-07-12T11:00:00.000+0000",
            started="2026-07-12T11:30:00.000+0000",
            resolved="2026-07-12T12:00:00.000+0000",
            labels=["research", "spike"], priority="High",
            description=(
                "Актуальный опыт (YouTube, статьи, threads) работы с Figma MCP. Фокус: подводные "
                "камни В СВЯЗИ С ДИЗАЙН-СИСТЕМОЙ, есть ли доводы вообще не браться, плюсы. "
                "Особенно интересует round-trip код↔Figma и генерация Figma из живого UI: "
                "надёжность, потеря структуры/слоёв, качество вывода. De-risk перед вложением в DS-в-Figma."
            ),
            decision_note=(
                "РЕЗУЛЬТАТ (12.07): ЗА (когда работает) — для команд со ЗРЕЛОЙ структурированной DS "
                "ускорение 50-70%; дашборд из 8 компонентов 2-3 дня → полдня, ревизии 4-5 → ~1. "
                "ПРОТИВ / камни: без Code Connect точность стилей 85-90% МИМО (руками правишь spacing/"
                "radius/responsive; модель «угадывает»); Code Connect — #1 рычаг, но требует платного + "
                "setup; начальная настройка 40-80 часов; на файле с непоследовательным неймингом — тяжёлое "
                "редактирование; мультипликатор есть ТОЛЬКО при зрелой DS. Безопасность: аудит 68 MCP-"
                "пакетов → 118 находок (транзитивные зависимости). НАШ КЕЙС (соло, free, DS с нуля): большие "
                "выигрыши достаются командам с DS+Code Connect+платными seat — у нас пока нет ничего из "
                "этого; Figma→код гейтится Dev Mode (платно) И даёт 85-90% мимо без Code Connect. "
                "ВЫВОД: на дедлайне сейчас ROI низкий → пауза оправдана, hi-fi в коде. Позже (чистая DS "
                "+ возможно платный seat) — реальный мультипликатор и сильный скилл для портфолио."
            )),
        _di("DASH-119", "Research: альтернативы Figma MCP для round-trip код↔дизайн",
            "Done", "Spike", "ANALYSIS", _DASH_EPICS["E14"], 3, 2, "Guzel K.",
            created="2026-07-12T11:00:00.000+0000",
            started="2026-07-12T12:00:00.000+0000",
            resolved="2026-07-12T12:20:00.000+0000",
            labels=["research", "spike"],
            description=(
                "Инструменты-альтернативы под задачу Guzel (основа в коде → правки в дизайн-тула → "
                "обратно в код, + дизайн-система-источник-правды). Кандидаты: Claude Design "
                "(claude.ai/design), Tokens Studio standalone, Anima, Builder.io, локоны code-to-design. "
                "Критерий: качество round-trip, token-first, цена, зрелость."
            ),
            decision_note=(
                "РЕЗУЛЬТАТ (12.07): КЛЮЧЕВОЙ вывод — почти все Figma→code инструменты (Anima 1.5M "
                "инсталлов, Builder.io Visual Copilot, Locofy, v0) выводят React/Vue/HTML, а НЕ Reflex "
                "Python. Наш стек — Reflex (Python→React под капотом), в него их вывод напрямую не ложится: "
                "пришлось бы переводить React→Reflex. То есть нога «Figma→код» плохо обслуживается ЛЮБЫМ "
                "тулом для Reflex-проекта, не только Figma MCP. Качество: AI даёт ~75%, доводка руками "
                "встроена в процесс, ни один не выдаёт production-ready без правок. ЧТО РЕАЛЬНО ПОДХОДИТ "
                "под наш кейс: (1) Tokens Studio ↔ design_tokens.json — token pipeline framework-agnostic, "
                "ложится в наш token-first БЕЗ Figma→code генерации; (2) Claude Design (DesignSync, доступен "
                "мне) + мой перевод в Reflex; (3) ручной путь — hi-fi в Reflex-коде мной, Guzel правит "
                "визуально, я перевожу намерение. ВЫВОД: не гнаться за Figma→code тулами (все про JS); "
                "инвестировать в токен-пайплайн + Claude Design. Комплементы: Builder.io Visual Copilot — "
                "лучший по маппингу на существующие компоненты; Locofy — чистейшая структура; Anima — "
                "самый распространённый, но flat HTML без семантики."
            )),
        _di("DASH-120", "Research: свод правил дизайн-системы по канону (Figma + документация)",
            "Done", "Spike", "DESIGN", _DASH_EPICS["E9"], 3, 5, "Guzel K.",
            created="2026-07-12T11:00:00.000+0000",
            started="2026-07-12T12:20:00.000+0000",
            resolved="2026-07-12T12:50:00.000+0000",
            labels=["research", "design-system"], priority="High",
            description=(
                "Лучшие практики DS от дизайнеров в командах: как оформлять в Figma (variables, "
                "components, tokens, naming, структура файла/страниц) и как вести документацию. "
                "Мы собираем DS сами → нужен канон + подводные камни. Выход: свод правил в CLAUDE.md/wiki, "
                "по которому строим DS-артефакт для рекрутера (эпик E9)."
            ),
            decision_note=(
                "РЕЗУЛЬТАТ (12.07): свод правил оформлен → wiki/design_system_canon.md (+ краткие правила "
                "в CLAUDE.md). Канон: токены — единый источник (W3C DTCG v2025.10); 3 уровня primitive→"
                "semantic→component; Figma-файлы Foundations/Components/Docs, страницы=категории; 3 коллекции "
                "Variables; нейминг категория-роль-вариант; документация анатомия/состояния/do-don't. "
                "Наши гэпы: design_tokens.json плоский (привести к 3 уровням); publish library требует paid "
                "(на free — визуальная подача); Storybook/Code Connect неприменимы (Reflex). Чек-лист «наша "
                "DS по канону» — в конце wiki-документа."
            )),

        _di("DASH-121", "Research: как дизайнеры и фронтендеры синхронят работу и дизайн-системы",
            "Done", "Spike", "ANALYSIS", _DASH_EPICS["E9"], 3, 5, "Guzel K.",
            created="2026-07-12T12:00:00.000+0000",
            started="2026-07-12T12:20:00.000+0000",
            resolved="2026-07-12T12:50:00.000+0000",
            labels=["research", "design-system"], priority="High",
            description=(
                "Лучшие практики синхронизации дизайн↔фронтенд, особенно Figma-DS ↔ код-DS. "
                "Вопросы: кто источник правды для токенов/компонентов; token pipeline "
                "(Figma variables → Tokens Studio → JSON → код, W3C DTCG); handoff-процесс; "
                "как избегают дрейфа между макетом и кодом; Code Connect; версионирование DS; "
                "роли и ритуалы (DS-review, contribution model). Отличие от DASH-120: там — как "
                "оформить DS по канону; здесь — как ДВЕ стороны держат её в согласии. Наш кейс: "
                "design_tokens.json уже единый источник — проверить против канона."
            ),
            decision_note=(
                "РЕЗУЛЬТАТ (12.07): Канон 2026 — граф ТОКЕНОВ единый источник правды, чтобы дизайн и код "
                "НЕ МОГЛИ разойтись (не «Figma главный» и не «код главный», а токены). Стандарт: W3C DTCG "
                "v2025.10 (стабилен с окт.2025) — один JSON-формат $value/$type, который Figma, Tokens "
                "Studio, Style Dictionary, Penpot, Supernova читают без конвертеров. Пайплайн: Figma "
                "Variables ↔ Tokens Studio ↔ design_tokens.json (DTCG) → Style Dictionary 4 → CSS/Tailwind/"
                "TS → Storybook preview → версионированный npm-пакет. Валидация: JSON-schema против DTCG в CI. "
                "Против дрейфа: Code Connect (маппинг Figma-компонент → код-компонент). Ритуалы: DS-review, "
                "contribution model. НАШ КЕЙС: design_tokens.json уже DTCG-стиля ($schema/$value/$type) — "
                "это правильный современный подход (сильная история для рекрутера!), НО структура плоская "
                "(color/spacing/…), без 3-уровневой канонной (primitive→semantic→component). Гэп на доработку "
                "в DASH-120. Reflex-нюанс: у нас нет Storybook/npm — Style Dictionary опционален, tokens.py "
                "читает JSON напрямую."
            )),

        _di("DASH-58", "HMW-вопросы: переформулировать проблемы рекрутера в возможности",
            "To Do", "Task", "DESIGN", _DASH_EPICS["E9"], 2, 1, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux", "discovery"],
            description=(
                "How Might We — техника переформулировки. "
                "Пример: «Рекрутер не понимает дашборд» → «Как мы могли бы показать контекст за первые 10 секунд?». "
                "Зафиксировать в wiki/ и вкладке Design Process."
            )),

        _di("DASH-59", "User flow: ключевые сценарии взаимодействия с дашбордом",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E9"], 3, 2, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux"],
            description=(
                "Схемы переходов между экранами для ключевых сценариев: "
                "рекрутер-первый-визит, PM-ежедневная-работа, рекрутер-углублённый-просмотр. "
                "Хранение: вкладка Design Process + Figma."
            )),

        _di("DASH-60", "Создать вкладку Design Process в дашборде",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E9"], 5, 5, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux", "content"],
            description=(
                "Новая вкладка в router.py: показывает Double Diamond процесс, "
                "Journey map, HMW-вопросы, User flow. "
                "Делает дизайн-процесс видимым рекрутеру прямо внутри продукта."
            )),

        # ── Figma integration ─────────────────────────────────────────────────
        _di("DASH-61", "Настроить Figma MCP: подключить к Claude Code",
            "To Do", "Spike", "ARCH", _DASH_EPICS["E14"], 3, 2, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            labels=["spike", "architecture"],
            description=(
                "ЦЕЛЬ GUZEL (из прошлых сессий): token-first архитектура — design_tokens.json "
                "единый источник правды для КОДА и FIGMA одновременно; дизайн-система редактируется "
                "в Figma и переносима между проектами. Три связанных инструмента: (1) официальный "
                "Figma Dev Mode MCP — двусторонний Figma↔код; (2) Tokens Studio — синк "
                "design_tokens.json ↔ Figma variables; (3) Claude Design 'Create using Claude Code'.\n\n"
                "КЛЮЧЕВОЕ для кейса: MCP теперь умеет 'Generate Designs from Live UI' / write-to-canvas — "
                "то есть из ЖИВОГО Reflex-дашборда генерировать редактируемые Figma-слои. Это прямо "
                "закрывает пробел Double Diamond «hi-fi есть в коде, нечего показать в Figma» "
                "(обратное направление код→Figma, которое раньше было невозможно).\n\n"
                "ШАГИ (офиц. Figma Learn, проверено 12.07.2026):\n"
                "0. Тариф: remote MCP доступен на ВСЕХ планах включая free; write-to-canvas бесплатен "
                "в бете. Блокера по оплате нет.\n"
                "1. `claude plugin install figma@claude-plugins-official` → рестарт Claude Code.\n"
                "2. `/plugin` → вкладка Installed → figma → Enter → страница авторизации.\n"
                "3. Авторизация: Allow access (Guzel делает сама — OAuth к её Figma-аккаунту).\n"
                "4. `/plugin` снова → figma должен быть connected.\n"
                "(Desktop-вариант — только для enterprise, требует Dev/Full seat; нам не нужен.)\n\n"
                "После подключения: DASH-62/63 (wireframes/hi-fi в Figma) и Tokens Studio синк.\n\n"
                "ПОДКЛЮЧЕНИЕ (desktop-app, Windows, 12.07): `claude` НЕ в PATH; `/plugin` в билде нет; "
                "проектный .mcp.json приложение НЕ читает даже после полного перезапуска. "
                "Рабочий путь (по claude-code-guide): user-scoped ~/.claude.json → добавить "
                "mcpServers.figma = {type:http, url:https://mcp.figma.com/mcp}. Правку делать ПОКА "
                "приложение полностью закрыто (иначе затрёт при выходе). Скрипт: "
                "scratchpad/add_figma_mcp.py (бэкап .bak-figma, additive-only). Авторизация: "
                "запустить app → /mcp → figma → Authenticate → браузер Allow access. "
                "Не проверено, читает ли билд top-level mcpServers — тестируем.\n\n"
                "⏸ ПАУЗА (12.07): эмпирически подтверждён потолок free-плана. Установлен официальный "
                "dev-mode-mcp-server-dxt (Enabled, 7 инструментов), НО он «работает только когда Dev Mode "
                "активен в Figma-файле», а Dev Mode недоступен на free Starter. В /mcp у remote-сервера НЕ "
                "появился статус Needs authentication (нет Dev Mode). Figma-инструменты ко мне не подтянулись. "
                "Вывод: генерация Figma↔код — функция Dev Mode = платно. Решение об апгрейде — после DASH-118/119. "
                "Пока: hi-fi делаем в коде (первая нога round-trip Figma не требует).\n\n"
                "💪 АРГУМЕНТ ЗА платный план (контр-вес к «ROI низкий сейчас», DASH-118): апгрейд — это "
                "инвестиция в НАВЫК, а не только в round-trip нашего кейса. Dev Mode надо изучить и в нём "
                "разбираться, потому что это пригодится в реальной командной работе (inspect, handoff, "
                "code panel, Code Connect). И шире: БОЛЬШИНСТВО платных фич Figma — именно про работу в "
                "команде (published libraries, права/seats, ветки, dev handoff). Для позиционирования "
                "«продуктовый дизайнер в команде» владение этим — прямая ценность и сильный сигнал "
                "рекрутеру. Т.е. решение об апгрейде взвешивать не только по дедлайну кейса, но и как "
                "профессиональное вложение. Тайминг — по итогам DASH-118/119 (сделаны) + личного приоритета."
            )),

        _di("DASH-62", "Wireframes ключевых экранов дашборда в Figma",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E9"], 4, 3, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux"],
            description=(
                "Серые б/ч схемы экранов: layout, иерархия, навигация. "
                "Без цветов и точных размеров — только «что где стоит». "
                "Покрыть: главный экран, 3-4 ключевые вкладки, recruiter onboarding flow."
            )),

        _di("DASH-63", "Hi-fi макеты в Figma на основе wireframes",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E9"], 5, 5, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux"],
            description=(
                "Детальные макеты с реальными цветами, типографикой, контентом. "
                "Использовать design_tokens.json через Tokens Studio. "
                "Демонстрирует Figma proficiency для вакансии Muse.\n\n"
                "WORKFLOW (решение Guzel 12.07): round-trip код → Figma → код. "
                "1) Claude пишет основу hi-fi фреймов кодом по референсам; "
                "2) Guzel редактирует в Figma desktop; "
                "3) через Figma MCP забираем правки обратно в Reflex-код. "
                "Итог — красивый дашборд для рекрутера. То же для wireframes (DASH-62)."
            )),

        # ── Командный сценарий и комикс ───────────────────────────────────────
        _di("DASH-64", "Блок 1 · World-bible команды и продукта (канвас фактов 2-нед спринта)",
            "Done", "Story", "PM", _DASH_EPICS["E10"], 4, 8, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-12T15:00:00.000+0000",
            resolved="2026-07-16T20:00:00.000+0000",
            labels=["content", "discovery"],
            priority="Highest",
            decision_note="ПРОДУКТ выбран (12.07): Motif — совместный comic/storyboard инструмент, "
                          "CRAFT-FIRST, БЕЗ генеративного AI (консистентность через модель-листы/ассеты, "
                          "не AI). World-bible → wiki/team_world_bible.md. "
                          "ГОТОВ (16.07): продукт (+MVP/скоуп), каст (грейды/бэкстори/черты), инвестор Даниэль, "
                          "банки факторов, спайн A1, финальный сценарий по дням, роли-карта (сверка с USER_STORIES), "
                          "раскадровка §5. §4-7 покрыты. Имена Ая/Нур — временные (поменять позже).",
            description=(
                "НЕ проза, а WORLD-BIBLE — лаконичный структурированный КАНВАС ФАКТОВ, единый источник "
                "правды для ОБОИХ потребителей: дашборд Motif (Блок 6 — полнота: все роли/задачи/тайм-канва) "
                "и комикс (Блоки 3-4 — фокусный срез). Держит их согласованными. Объединяет DASH-64+96.\n\n"
                "1) ПРОДУКТ — В ПЕРВУЮ ОЧЕРЕДЬ (от него весь флёр истории): что за продукт, для кого, "
                "цели/ценность, как команда финансируется, почему это важно. Ограничение — спринт 2 недели.\n"
                "2) КАСТ: ростер + роли (PM, PD, BA/SA, PA, Dev, QA, Growth, Research, Scrum Master?), "
                "ИМЕНА, устойчивые визуальные образы, человеческие характеры/типажи.\n"
                "3) НАРРАТИВНЫЙ СПАЙН: цель спринта как сквозная линия → центральное напряжение → развязка.\n"
                "4) ЧТО ДЕМОНСТРИРУЕМ (явная цель, не фон): зрелый продуктовый процесс — церемонии и "
                "артефакты, которыми обмениваются роли, каждый этап разработки освещён «как правильно».\n"
                "5) СОБЫТИЯ (кризисные И радостные): рабочие; нерабочие общие (погода, город/страна); "
                "нерабочие личные (семья, друзья, романтика).\n"
                "6) ТАЙМ-КАНВА день-за-днём (день 1…10) — чтобы события легли в дневники, данные, календарь.\n"
                "Хранение: wiki/team_story.md. Бизнес-Goals легенды (финансирование, метрики) — здесь же."
            )),

        _di("DASH-65", "Блок 2 · Дневники ролей (те же события глазами каждого)",
            "To Do", "Story", "PM", _DASH_EPICS["E10"], 4, 5, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["content", "ux"],
            priority="High",
            description=(
                "Разложение истории (Блок 1) по дневникам ролей. Правило: ОДНИ И ТЕ ЖЕ события спринта "
                "глазами разных ролей (Rashomon, как в ПМ-краше). Список ролей = ростер из Блока 1. "
                "PM-дневник уже есть (wiki/pm_role_sprint_diary.md — обновим под финальную историю). "
                "Каждый: голос персонажа, его задачи Jira, блокеры, эмоции, рабочий контекст. "
                "Хранение: wiki/[role]_role_sprint_diary.md. Блокируется Блоком 1."
            )),

        _di("DASH-66", "Разработать концепцию комикса: персонажи, раскадровка, стиль",
            "Done", "Story", "DESIGN", _DASH_EPICS["E11"], 8, 5, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-12T14:00:00.000+0000",
            resolved="2026-07-12T14:10:00.000+0000",
            labels=["ux", "content"],
            description="Концепция комикса — персонажи/раскадровка/стиль.",
            decision_note="Объединено при перекомпоновке (12.07): раскадровка → Блок 3 (DASH-100), "
                          "персонажи/стиль/референс-листы → Блок 4 (DASH-101)."),

        _di("DASH-67", "Создать UI комикса в дашборде (новая вкладка или страница)",
            "Done", "Story", "DESIGN", _DASH_EPICS["E11"], 8, 8, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-12T14:00:00.000+0000",
            resolved="2026-07-12T14:10:00.000+0000",
            labels=["ux", "content"],
            description="Интерактивный комикс в Reflex.",
            decision_note="Объединено при перекомпоновке (12.07): встраивание комикса в дашборд → DASH-102 (Блок 4)."),

        _di("DASH-80", "UX/UI аудит дашборда: пройти по всем вкладкам глазами рекрутера",
            "To Do", "Task", "DESIGN", _DASH_EPICS["E9"], 3, 2, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux", "research"],
            description=(
                "Самостоятельный аудит: открыть дашборд, пройти все вкладки как рекрутер. "
                "Фиксировать: что непонятно с первого взгляда, где теряешься, что перегружено, "
                "что пустовато, где нет понятного следующего действия. "
                "Результаты → задачи на улучшение. Делать до Usability testing с IT-друзьями (DASH-68)."
            )),

        _di("DASH-68", "Usability testing: показать дашборд IT-друзьям, собрать фидбек",
            "To Do", "Task", "RESEARCH", _DASH_EPICS["E12"], 3, 2, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["research"],
            description=(
                "После GitHub release — показать дашборд 3-5 знакомым из IT. "
                "Сценарий: «найди раздел с аналитикой», «что делает этот проект?». "
                "Фиксировать: где теряются, что удивляет, что непонятно. "
                "Результаты → задачи на улучшение."
            )),

        # ── Переписать MOTIF данные под реальный сценарий ────────────────────
        _di("DASH-69", "Spike: переписать MOTIF_DEMO_CONFIG данные под реальный сценарий спринта",
            "Done", "Spike", "DEV", _DASH_EPICS["E10"], 8, 5, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-12T14:00:00.000+0000",
            resolved="2026-07-12T14:10:00.000+0000",
            labels=["spike", "content"],
            description="Переписать случайные MOTIF-данные под сценарий.",
            decision_note="Объединено в DASH-97 (Блок 6) при перекомпоновке 12.07."),

        _di("DASH-122", "Блок 5 (бонус) · Музыка виджетом к фреймам комикса",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E11"], 5, 3, "Guzel K.",
            created="2026-07-12T14:00:00.000+0000",
            labels=["ux", "content"], priority="Low",
            description="Если хватит сил/времени: добавить музыку виджетом к конкретным фреймам комикса "
                        "(плейлисты персонажей / атмосфера рабочего дня). Бонус, флексится первым. "
                        "Блокируется Блоком 4 (отрисовка)."),

        # ── Технический долг (рефакторинг из плана) ──────────────────────────
        _di("DASH-70", "Рефакторинг компонентов: универсальный data_table, вынос молекул",
            "In Progress", "Task", "DEV", _DASH_EPICS["E13"], 5, 5, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-12T13:00:00.000+0000",
            labels=["tech-debt", "architecture"],
            description=(
                "32 инлайн-молекулы в page-файлах → вынести в components/. "
                "Дублирование: _tasks_table (4×), _bug_table (3×), _legend (4×). "
                "Универсальный data_table_wrapper (шапка + строки + overflow)."
            ),
            decision_note="Частично (сверка 12.07): components/data_table.py СОЗДАН, но 6 файлов "
                          "(architecture, dev, info, monitoring, quality, release) ещё держат свои "
                          "_bug_table/_legend — миграция не завершена. Остаток: перевести их на data_table."),

        _di("DASH-71", "Рефакторинг кода: router, god-файл kp_dashboard.py",
            "Done", "Task", "DEV", _DASH_EPICS["E13"], 3, 3, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-09T10:00:00.000+0000",
            resolved="2026-07-10T12:00:00.000+0000",
            labels=["tech-debt"],
            description=(
                "real_page_wrapper() — общий wrapper для всех real_*.py. "
                "stat_card — keyword-only аргументы после value. "
                "Разбить god-файл kp_dashboard.py если разросся."
            ),
            decision_note="Закрыто (сверка 12.07): real_page_wrapper в components/shared.py; god-файл "
                          "разбит (dash_app.py ~144 строки, DASH-84); stat_card keyword-only — DASH-83."),

        _di("DASH-72", "Spike: Claude Design интеграция — код → макеты → код",
            "Done", "Spike", "DESIGN", _DASH_EPICS["E14"], 3, 3, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-12T12:00:00.000+0000",
            resolved="2026-07-12T13:10:00.000+0000",
            labels=["spike", "architecture"],
            description=(
                "Исследовать workflow: Claude Design читает компоненты → генерирует макеты. "
                "Зависит от: DASH-61 (Figma MCP настроен)."
            ),
            decision_note="Закрыто как superseded DASH-119: исследование Claude Design как пути "
                          "проведено (DesignSync доступен, + мой перевод в Reflex). Реальную пробу — "
                          "внутри работы над DS, не отдельным спайком."),

        # ── Баг: DASH данные не видны в Kanban/Backlog ───────────────────────
        _di("DASH-73", "Баг: DASH задачи не отображаются в Kanban и Backlog вкладках",
            "Done", "Bug", "DEV", _DASH_EPICS["E5"], 3, 3, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            started="2026-07-09T12:00:00.000+0000",
            resolved="2026-07-09T14:00:00.000+0000",
            labels=["tech-debt"],
            priority="High",
            decision_note=(
                "kanban.py: добавлена dash_kanban_tab() с load_issues(DASH_CONFIG). "
                "backlog_state.py: BacklogState наследует ProjectState, предзагружены _ALL и _ALL_DASH, "
                "filtered() выбирает датасет по self.project_mode. "
                "router.py: kanban и backlog получили dash= варианты."
            )),

        # ── Handoff-2 баги — все починены, статус Done ───────────────────────
        _di("DASH-74", "Fix 1.1: приватный путь пользователя — вынести в JSON снэпшот",
            "Done", "Bug", "DEV", _DASH_EPICS["E6"], 2, 2, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:00:00.000+0000",
            resolved="2026-07-07T18:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="Создан real_project_extract.py со статическими константами. Живое чтение диска убрано."),

        _di("DASH-75", "Fix 1.2: sprint_index случаен — вычислять из дат задачи",
            "Done", "Bug", "DEV", _DASH_EPICS["E4"], 2, 2, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:00:00.000+0000",
            resolved="2026-07-07T18:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="metrics.py:503 — sprint_index = max(1, days_since_start // squad.sprint_length_days + 1). Хронологичен."),

        _di("DASH-76", "Fix 1.3: p_value захардкожен — вычислять через честный z-test",
            "Done", "Bug", "DEV", _DASH_EPICS["E4"], 2, 2, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:00:00.000+0000",
            resolved="2026-07-07T18:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="metrics.py:509 — функция _two_prop_ztest(n_a, conv_a, n_b, conv_b). p_value вычисляется из данных."),

        _di("DASH-77", "Fix 1.4: CI назван Wilson в docstring, по факту — Wald",
            "Done", "Bug", "DEV", _DASH_EPICS["E4"], 1, 1, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:00:00.000+0000",
            resolved="2026-07-07T18:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="analytics.py:183 — docstring исправлен: '95% confidence interval for a proportion (Wald approximation)'."),

        _di("DASH-78", "Fix 1.5: Growth и Analytics показывали два разных набора экспериментов",
            "Done", "Bug", "DEV", _DASH_EPICS["E4"], 2, 2, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:00:00.000+0000",
            resolved="2026-07-07T18:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="analytics.py:530 — exp_rows = growth_experiments(issues). Оба таба теперь используют один источник."),

        _di("DASH-82", "Code review: второе мнение Claude по состоянию кодовой базы перед релизом",
            "Done", "Task", "DEV", _DASH_EPICS["E8"], 3, 3, "Claude Code",
            created="2026-07-09T14:00:00.000+0000",
            started="2026-07-09T15:00:00.000+0000",
            resolved="2026-07-09T18:00:00.000+0000",
            labels=["architecture", "tech-debt"],
            priority="High",
            decision_note=(
                "Два агента (Angle A–E + Reuse/Simplification) нашли 8 находок: "
                "3 HIGH (roadmap не в _by_project, DASH squad keys в Kanban, @rx.var cross-state), "
                "2 MEDIUM (дропдауны статичные, _TODAY захардкожен), 3 LOW. "
                "Все кроме cross-state dependency зафиксированы в рамках этой же сессии (DASH-83)."
            )),

        _di("DASH-83", "Fix: code review findings — router, kanban squads, дропдауны, _TODAY",
            "Done", "Bug", "DEV", _DASH_EPICS["E8"], 5, 5, "Claude Code",
            created="2026-07-09T18:00:00.000+0000",
            started="2026-07-09T18:00:00.000+0000",
            resolved="2026-07-09T20:00:00.000+0000",
            labels=["tech-debt"],
            priority="High",
            decision_note=(
                "router.py: roadmap_tab() обёрнут в _by_project(motif=coming_soon, kp=coming_soon, dash=roadmap_tab()). "
                "kanban.py: SQUAD_LABELS дополнен DISCOVERY, ARCH, PM. "
                "roadmap.py: _TODAY = date.today(), zero-guard _TOTAL_DAYS or 1. "
                "backlog_state.py: 5 computed vars *_options() + _select_dyn() через rx.foreach. "
                "reset_filters() теперь сбрасывает mode. Убран pass перед vars в классе."
            )),

        _di("DASH-84", "Rename: kp_dashboard → dash_app, 20260702_2219_kp_dashboard_v2 → dashboard_product",
            "Done", "Task", "DEV", _DASH_EPICS["E8"], 2, 2, "Claude Code",
            created="2026-07-10T09:00:00.000+0000",
            started="2026-07-10T09:00:00.000+0000",
            resolved="2026-07-10T11:00:00.000+0000",
            labels=["architecture"],
            priority="Medium",
            decision_note=(
                "Дашборд стал архитектурно универсальным — убран префикс kp. "
                "Python-пакет переименован: kp_dashboard/ → dash_app/, kp_dashboard.py → dash_app.py. "
                "rxconfig.py: app_name='dash_app'. scripts/, __init__.py, launch.json обновлены. "
                "Корневая папка переименована вручную в проводнике: dashboard_product/."
            )),

        _di("DASH-85", "Удалить tabs_nav и горизонтальный режим навигации",
            "Done", "Task", "DEV", _DASH_EPICS["E13"], 3, 3, "Claude Code",
            created="2026-07-10T10:00:00.000+0000",
            started="2026-07-12T21:00:00.000+0000",
            resolved="2026-07-12T21:20:00.000+0000",
            labels=["tech-debt"],
            priority="Low",
            description=(
                "Горизонтальный режим навигации (tabs_nav) не используется и не вызывается. "
                "При 17 вкладках не умещается без скролла и плохо читается. Мёртвый код. "
                "Удалить: tabs_nav() и _tab_item() из navigation.py, "
                "nav_variant и toggle_variant() из NavState, "
                "_burger_btn() из navigation.py, "
                "условный рендер sidebar vs tabs из layout.py. "
                "Оставить только sidebar_nav()."
            ),
            decision_note="Закрыто 12.07: подтверждён недостижимый tabs_layout (переключатель _burger_btn "
                          "жил внутри tabs_nav, в который из sidebar не попасть). Удалено −160 строк: "
                          "tabs_nav/_tab_item/_burger_btn/_project_dropdown_compact (navigation.py), "
                          "nav_variant/toggle_variant (NavState), tabs_layout+rx.cond (layout.py), "
                          "экспорты (components/__init__). Компиляция OK, мёртвых ссылок нет."),

        _di("DASH-88", "Spike: Framer как платформа для портфолио + возможность встроить дашборд",
            "Done", "Spike", "ARCH", _DASH_EPICS["E8"], 3, 3, "Guzel K.",
            created="2026-07-11T09:00:00.000+0000",
            started="2026-07-11T09:00:00.000+0000",
            resolved="2026-07-11T09:30:00.000+0000",
            labels=["spike", "architecture", "release"],
            priority="Medium",
            decision_note=(
                "Решение: Вариант 2 → гибрид по мере готовности. "
                "Шаг 1: дашборд деплоится отдельно (Railway/Fly.io/VPS), Framer-портфолио даёт кнопку-ссылку. "
                "Шаг 2: по мере появления Figma, journey map, комикса — они красиво ложатся в Framer как кейс-страница. "
                "Дашборд остаётся живым приложением рядом как 'бонус для технически любопытных'. "
                "Iframe не используем: проблемы на мобильном + сложность с заголовками безопасности."
            )),

        _di("DASH-87", "Spike: сохранение логов сессий Claude — исследовать подходы",
            "Done", "Spike", "ARCH", _DASH_EPICS["E13"], 3, 3, "Guzel K.",
            created="2026-07-10T12:00:00.000+0000",
            started="2026-07-12T22:00:00.000+0000",
            resolved="2026-07-12T22:20:00.000+0000",
            labels=["spike", "architecture", "process"],
            priority="Low",
            decision_note="Закрыто 12.07 → wiki/session_logs_spike.md. Логи: ~/.claude/projects/"
                          "<encoded-cwd>/<sessionId>.jsonl, один файл на сессию, JSONL (события user/"
                          "assistant/system + служебные), поля timestamp/uuid/parentUuid/gitBranch/"
                          "toolUseResult/attribution*. Для DASH-113 достаточно полу-ручного скрипта "
                          "(сопоставление по времени с git). Сырые логи НЕ коммитить (приватность), "
                          "формат недокументирован (может меняться). Ценное — выжимками в wiki/CLAUDE.md.",
            description=(
                "Исследовать варианты сохранения логов работы в сессиях Claude Code. "
                "Вопросы: где хранятся .jsonl файлы истории, можно ли их читать/экспортировать, "
                "стоит ли делать периодические снэпшоты важных решений из логов в артефакты проекта, "
                "как связать лог-сессии с Jira-задачами. "
                "Возможные подходы: автоматический экспорт в Obsidian, "
                "скрипт извлечения decision_notes из JSONL в CLAUDE.md."
            )),

        _di("DASH-86", "Fix: invalid icon names + App(theme=...) deprecation warning",
            "Done", "Bug", "DEV", _DASH_EPICS["E8"], 2, 2, "Claude Code",
            created="2026-07-10T11:00:00.000+0000",
            started="2026-07-10T11:00:00.000+0000",
            resolved="2026-07-10T11:30:00.000+0000",
            labels=["tech-debt"],
            priority="Low",
            decision_note=(
                "Иконки check-circle/x-circle/help-circle → circle-check/circle-x/circle-help "
                "в real_release.py, real_quality.py, real_overview.py, real_architecture.py, real_design.py. "
                "Кеш .states/*.pkl с устаревшими именами иконок (check_circle) удалён. "
                "SitemapPlugin добавлен в disable_plugins в rxconfig.py. "
                "App(theme=...) deprecation: TODO — перенести тему в RadixThemesPlugin в rxconfig.py."
            )),

        _di("DASH-81", "UX/UI аудит: карточки раздела Goals на вкладке Roadmap",
            "To Do", "Task", "DESIGN", _DASH_EPICS["E9"], 3, 3, "Guzel K.",
            created="2026-07-09T12:00:00.000+0000",
            labels=["ux", "design"],
            priority="Medium",
            description=(
                "Провести UX/UI аудит компонента _okr_card() в pages/roadmap.py. "
                "Оценить: читаемость KR-строк, визуальную иерархию, выравнивание, "
                "отступы, цветовые акценты статусов. При необходимости доработать компонент "
                "или вынести в design system как переиспользуемый OKR-виджет."
            )),

        _di("DASH-79", "Fix 1.6: import re посреди файла — перенести в шапку",
            "Done", "Bug", "DEV", _DASH_EPICS["E4"], 1, 1, "Claude Code",
            created="2026-07-07T09:00:00.000+0000",
            started="2026-07-07T09:00:00.000+0000",
            resolved="2026-07-07T18:00:00.000+0000",
            labels=["tech-debt"],
            decision_note="metrics.py:11 — import re as _re теперь в шапке файла вместе с остальными импортами."),

        # ── Предрелизная подготовка ───────────────────────────────────────────
        _di("DASH-90", "Backlog UX: попапы задачи/эпика в стиле Jira, кликабельные ключи, фильтр по эпику",
            "Done", "Story", "DEV", _DASH_EPICS["E7"], 4, 5, "Claude Code",
            created="2026-07-10T16:00:00.000+0000",
            started="2026-07-10T16:30:00.000+0000",
            resolved="2026-07-11T20:00:00.000+0000",
            labels=["ux", "backlog"],
            priority="High",
            description=(
                "Улучшение вкладки Backlog (5 пунктов + расширения 11 июля):\n"
                "1) попап задачи в стиле Jira (статус-кнопка сверху, поля в правой панели);\n"
                "2) попап эпика по клику на строку эпика (агрегированная статистика + список задач);\n"
                "3) Epic KEY (DASH-EPIC-1) виден в таблице и в заголовке попапа;\n"
                "4) фильтр эпиков показывает 'KEY · Название' в дропдауне;\n"
                "5) Epic редактируемый в попапе задачи;\n"
                "6) KEY и название задачи/эпика кликабельны для открытия попапа из любого режима (Issues и Epics)."
            ),
            decision_note=(
                "Единственный rx.dialog.root на страницу (Radix-конфликт при двух sibling-диалогах). "
                "Контент переключается через rx.cond(selected_epic_key != '', _epic_content(), _issue_content()). "
                "selected_epic_key объявлен ДО методов open_issue/open_epic (порядок vars в Reflex-State критичен). "
                "rx.badge(color_scheme=DynamicVar) не работает → заменён на rx.box + rx.cond цепочки. "
                "Структурные изменения требуют Remove-Item .web/ + reflex run (hot reload не подхватывает). "
                "epic фильтр хранит KEY, не name; filtered() сравнивает r['epic'] == self.epic. "
                "Clickable cells: epic key + epic name в _issue_row → open_epic(); issue key в _issue_row → open_issue()."
            )),

        _di("DASH-91", "UI/UX аудит: синхронизация состояния интерфейса и сущностей для разных пользователей",
            "To Do", "research-spike", "DISCOVERY", _DASH_EPICS["E9"], 5, 3, "Guzel K.",
            created="2026-07-10T16:00:00.000+0000",
            labels=["ux", "research", "architecture"],
            priority="Medium",
            description=(
                "Аудит того, как состояние UI синхронизируется с данными (сущностями-объектами) "
                "при работе разных пользователей с одним продуктом одновременно.\n\n"
                "Вопросы для исследования:\n"
                "1. Кто «владеет» состоянием: UI-слой или слой данных? "
                "Где живёт source of truth для каждого поля?\n"
                "2. Что происходит когда два пользователя одновременно редактируют одну задачу? "
                "Какая модель разрешения конфликтов?\n"
                "3. Оптимистичные обновления (optimistic UI) vs. pessimistic locking — "
                "что лучше подходит для нашего контекста и почему?\n"
                "4. Как отражать «чужие» изменения: polling, WebSockets, SSE? "
                "Какие артефакты UI появляются при этом (индикатор 'updated', toast, badge)?\n"
                "5. Разница в UX между синхронными (Figma: live cursors) и асинхронными (Jira: last-write-wins) инструментами — "
                "когда какая модель уместна?\n\n"
                "Цель: сформулировать дизайн-принципы для продуктов с мультипользовательским стейтом. "
                "Оформить как UX-артефакт (principles doc или journey map конфликта состояния).\n\n"
                "Живой кейс из нашего же дашборда (11.07): после полной перезагрузки страницы "
                "выбранный проект сбрасывается на Motif — project_mode не переживает reload "
                "(нет персистентности в localStorage/URL). Разобрать в рамках аудита."
            )),

        _di("DASH-89", "Переименовать проект: KP Dashboard → Product Dashboard + папка product-dashboard",
            "Done", "Task", "DEV", _DASH_EPICS["E8"], 2, 1, "Guzel K.",
            created="2026-07-10T14:00:00.000+0000",
            started="2026-07-10T14:00:00.000+0000",
            resolved="2026-07-10T15:00:00.000+0000",
            labels=["release", "tech-debt"],
            priority="Medium",
            decision_note=(
                "Старое название 'KP Dashboard' несло двойную нагрузку: аббревиатуру 'KP' (Knowledge Pipeline) "
                "и название самого дашборда — путаница при переключении режимов. "
                "Новое название 'Product Dashboard' однозначно: это портфолио-дашборд о продуктовой работе. "
                "Имя репозитория 'product-dashboard' выбрано перед 'dashboard-product' по GitHub-конвенции: "
                "[домен]-[тип] читается как 'дашборд продуктовый', а не 'продукт-дашборд'. "
                "Изменено: title браузера, дропдаун режимов, project_name в DASH_CONFIG, design_tokens.json, "
                "README.md, README_RU.md, USER_STORIES.md, clone URL. "
                "Папка переименована вручную в проводнике."
            )),

        # ── Спринт 11–17.07: перенарезка по ценностям (установочная встреча) ──
        _di("DASH-95", "Перенарезка эпиков по ценностям: business/enabler, распределение задач",
            "Done", "Task", "PM", _DASH_EPICS["E10"], 3, 3, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            started="2026-07-11T12:00:00.000+0000",
            resolved="2026-07-11T20:30:00.000+0000",
            labels=["process", "architecture"], priority="High",
            description=(
                "DOD: North Star видна в Overview; OKR и артефакты установочной встречи — в Roadmap; "
                "у эпиков виден тип (business/enabler); все открытые задачи распределены по новым эпикам; "
                "в календаре спринта key + название задач актуальны."
            ),
            decision_note=(
                "Установочная встреча PM+Stakeholder 11.07: пересмотр DASH-56 — North Star одна, не две. "
                "«Кейс → оффер Muse» — главная цель; «удобный дашборд для выдуманной команды» — инструментальная "
                "(выдуманный PM — персона, не стейкхолдер). При конфликте побеждает зритель кейса. "
                "Эпики нарезаны по ценности (SAFe business/enabler): E9-E12 business, E13-E14 enabler c явным "
                "«разблокирует →» (EPIC_UNLOCKS). Компонентные E1-E8 не переписываем — честная история проекта. "
                "Открытые задачи (25 шт.) переназначены на новые эпики."
            )),
        _di("DASH-92", "Дизайн-система дашборда: ревизия токенов и компонентов перед hi-fi",
            "To Do", "Task", "DESIGN", _DASH_EPICS["E9"], 3, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["ux", "design-system"], priority="High",
            description="Ревизия design_tokens.json и компонентов: консистентность цветов, типографики, "
                        "отступов. База для hi-fi макетов (DASH-63) и Tokens Studio."),
        _di("DASH-96", "История команды: кризисы + Goals легенды (финансирование, бизнес-метрики)",
            "Done", "Story", "PM", _DASH_EPICS["E10"], 3, 5, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            started="2026-07-12T14:00:00.000+0000",
            resolved="2026-07-12T14:10:00.000+0000",
            labels=["content", "discovery"], priority="High",
            description="Бизнес-контекст легенды: финансирование, Goals, 2-3 кризиса.",
            decision_note="Объединено в DASH-64 (Блок 1) при перекомпоновке 12.07 — история и бизнес-контекст в одной задаче."),
        _di("DASH-100", "Блок 3 · Сценарий комикса (законы жанра + фокусный поток)",
            "Done", "Story", "DESIGN", _DASH_EPICS["E11"], 4, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            started="2026-07-15T12:00:00.000+0000",
            resolved="2026-07-17T14:00:00.000+0000",
            labels=["content", "ux"], priority="High",
            description="Переход от истории (Блок 1) к сценарию комикса. Объединяет раскадровочную часть DASH-66.\n"
                        "1) Исследовать законы сценария короткого комикса: что можно/нельзя, ограничения "
                        "(панельная грамматика, ритм/паузы, page-turn, «показывай не рассказывай», баблы).\n"
                        "2) Жанр — «рабочая повседневность» (slice-of-life манга/аниме/сериал): живое, "
                        "понятное каждому, БЕЗ чрезмерной драмы.\n"
                        "3) Комикс не показывает всё — выбрать ОДИН фокусный поток/арку из истории.\n"
                        "Блокируется Блоком 1. Хранение: wiki/comic_script.md.",
            decision_note=(
                "ГОТОВ (16.07). Фокусный поток = A1 «Потеря арта» (ансамблевая плетёнка со спайном). Финальный "
                "сценарий по дням + раскадровка (12 сцен, формат СТРАНИЦЫ) — wiki/comic_script.md + world-bible "
                "§3b/§3c/§5 + раздел «Сценарий» на About. Кризис переписан на компетентную механику (живая "
                "миграция + латентный техдолг + RPO, не «забыли бэкапы»). Дальше — кадр-уровень + DASH-101 (отрисовка)."
            )),
        _di("DASH-97", "Блок 6 · Пересоздание Motif: Jira-данные + наполнение вкладок",
            "To Do", "Task", "DEV", _DASH_EPICS["E10"], 4, 8, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            labels=["content", "data"], priority="High",
            description="Вшить историю (Блок 1) + дневники (Блок 2) в MOTIF-данные и наполнение вкладок "
                        "дашборда: Jira-задачи по тайм-канве, роли, кризисы, Goals легенды. Объединяет DASH-69. "
                        "ЗАВИСИТ от Блоков 1-2, идёт ПАРАЛЛЕЛЬНО комиксу (Блоки 3-5) — комикс не предпосылка данных."),
        _di("DASH-98", "Карточки персон команды: цитаты, JTBD, RACI",
            "Done", "Story", "DESIGN", _DASH_EPICS["E10"], 4, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            started="2026-07-13T12:00:00.000+0000",
            resolved="2026-07-16T20:00:00.000+0000",
            labels=["ux", "content"],
            description="Артефакт из Блока 1 (каст): визуальные карточки персон команды поверх истории + "
                        "USER_STORIES.md + RACI по Deliverables. Закрывает пробел Double Diamond «User personas». "
                        "Блокируется Блоком 1 (каст/имена/образы).",
            decision_note=(
                "ГОТОВ (16.07). На About (Motif): карточки 11 (роль+грейд+характер+образ+черты/события), JTBD, "
                "RACI (9 активностей, A выделена), цитаты (по характерам), бэкстори (кратко), + карточка "
                "инвестора Даниэля. Перевыполнено сверх ТЗ."
            )),
        _di("DASH-99", "Карта обмена артефактами PD ↔ команда (визуализация на дашборде)",
            "Done", "Story", "ANALYSIS", _DASH_EPICS["E10"], 4, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            started="2026-07-13T12:00:00.000+0000",
            resolved="2026-07-14T20:00:00.000+0000",
            labels=["ux", "content"],
            description="Артефакт из Блока 1 (продуктовая сторона): PD в центре, стрелки по ролям "
                        "(таблица в CLAUDE.md). Место: вкладка ролей/RACI или Design Process tab. Блокируется Блоком 1.",
            decision_note=(
                "ГОТОВ (перевыполнено): на About (Motif) схема обмена артефактами для ВСЕХ 11 ролей "
                "(хаб-спицы: даёт →/получает ←/двусторонне ↔ и с кем), не только PD."
            )),
        _di("DASH-93", "Визуальная иерархия Goals → Epics → Issues в коде дашборда",
            "In Progress", "Story", "DEV", _DASH_EPICS["E9"], 4, 5, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            started="2026-07-11T17:00:00.000+0000",
            labels=["ux"], priority="High",
            description="Три уровня оптики (ПМ-краш п.5): Goals — квадрокоптер, Epics — пейзаж "
                        "(тип business/enabler виден, у enabler — «разблокирует →»), Issues — лупа. "
                        "Побочный продукт — схема сущностей Goal→Epic→Issue (SA-артефакт)."),
        _di("DASH-94", "Competitive-слайд: почему такая структура навигации (Jira/Linear/Notion)",
            "To Do", "Task", "ANALYSIS", _DASH_EPICS["E9"], 4, 1, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["research"], priority="Low",
            description="Закрывает пробел Double Diamond «Competitive analysis». Could — флексится первым."),
        _di("DASH-101", "Блок 4 · Отрисовка комикса (выбор AI, референс-листы, фреймы)",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E11"], 4, 8, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["ux", "content"], priority="High",
            description="1-й этап отрисовки. Объединяет стиль/персонажей из DASH-66.\n"
                        "1) ВЫБОР AI для генерации (критерий №1 — консистентность персонажа между "
                        "кадрами; это главная боль AI-комиксов) — отдельное мини-исследование.\n"
                        "2) РЕФЕРЕНС-ЛИСТЫ персонажей (character sheets: лица, одежда, палитра) — без них "
                        "AI не удержит героев одинаковыми.\n"
                        "3) Раскадровка истории по фреймам (по законам из Блока 3).\n"
                        "4) Фреймы-картинки в ЕДИНОМ стиле.\n"
                        "5) Текст: рядом с фреймами (более читабельно) vs внутри — решить, склоняемся к рядом.\n"
                        "Блокируется Блоком 3 (сценарий)."),
        _di("DASH-102", "Блок 4 · Встроить комикс в дашборд/кейс",
            "To Do", "Task", "DEV", _DASH_EPICS["E11"], 4, 5, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            labels=["ux", "content"], priority="High",
            description="Интерактивный комикс в Reflex (объединяет DASH-67): слайды-фреймы, текст рядом, "
                        "навигация. Финал Блока 4. Блокируется DASH-101 (отрисовка)."),
        _di("DASH-103", "Деплой дашборда (Reflex Cloud) — публичный URL",
            "Done", "Task", "ARCH", _DASH_EPICS["E13"], 4, 3, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            started="2026-07-13T14:30:00.000+0000",
            resolved="2026-07-13T15:00:00.000+0000",
            labels=["release", "architecture"], priority="High",
            description="По решению DASH-88: дашборд отдельно, Framer даёт кнопку-ссылку. Блокирует Framer-сборку.",
            decision_note=(
                "════════ ДЕПЛОЙ 13.07.2026 — ПОЛНЫЙ ЛОГ ════════\n"
                "РЕЗУЛЬТАТ: https://product-dashboard-teal-ring.reflex.run (Reflex Cloud, free). "
                "App id 4461802e-cf0a-4ae3-afe2-590f53994ad2. Машина c1m1 (1 CPU/1ГБ), регион fra (Франкфурт), "
                "БЕЗ пингера. Проверено: главная 200, внутренние доки 404 (не публичны).\n\n"
                "ВЫБОР ПЛАТФОРМЫ (почему Reflex Cloud free):\n"
                "• Reflex — 2 процесса (фронт+бэкенд websocket). Railway/Fly/Render/VPS требуют Docker+reverse-"
                "proxy; Reflex Cloud деплоит одной командой без Docker.\n"
                "• Reflex Cloud always-on (Pro) = $200/мес — дорого, отпали. Vercel/Netlify не подходят (нужен "
                "постоянный Python-бэкенд).\n"
                "• Решение: free + маленькая машина c1m1. Ключевой факт: машины <c2m2 стартуют «тёпло» <1 сек "
                "(не 15!), биллинг посекундный, простой = $0. Значит ПИНГЕР НЕ НУЖЕН и даже ВРЕДЕН (держал бы "
                "app 24/7 → сжёг бы 50 кредитов/мес за дни; + мусорил бы в аналитике). Без пингера кредиты "
                "тратятся только при реальных визитах → 50/мес хватит витрине.\n\n"
                "ШАГИ:\n"
                "1. requirements.txt был неполный (только reflex) → дополнили reflex-components-radix==0.9.5, "
                "reflex-base==0.9.6.post1 (иначе деплой упал бы на импортах).\n"
                "2. `python -m reflex login` → браузер → Google (GitHub на странице НЕ предлагают, только "
                "Google/Email; аккаунт создаётся автоматически при входе).\n"
                "3. `reflex cloud vmtypes` / `regions` → выбрали c1m1 + fra.\n"
                "4. `reflex deploy` (интерактивно, в терминале Guzel).\n\n"
                "ТРУДНОСТИ И РЕШЕНИЯ:\n"
                "• `--no-interactive` требует явный `--token` → не извлекаем токен (приватность), запускаем "
                "ИНТЕРАКТИВНО (сохранённый вход подхватывается).\n"
                "• ГЛАВНЫЙ ЗАТЫК: `ValueError: user does not have access to deploy for this project`. Причина — "
                "НЕ токен (read-команды работали), а НЕВЫБРАННЫЙ проект (`project selected` → 'no selected "
                "project'). ФИКС: `reflex cloud project select f02cd2c3-6668-4d13-8196-af33dd0edf0f` → деплой прошёл.\n"
                "• ПРИВАТНОСТЬ: `reflex deploy` НЕ уважает .gitignore (проверено `reflex export --backend-only` → "
                "в backend.zip попадали CLAUDE.md + 4 handoff/state .md). Публично недоступны (404), но лежали в "
                "архиве на серверах Reflex. ФИКС: scripts/deploy.py читает .gitignore (единый источник правды), "
                "раскрывает шаблоны через glob и передаёт файлы в --exclude-from-backend. Чистый передеплой → "
                "backend 75→71 файл, доки исключены, сайт по-прежнему 200.\n\n"
                "ВЫВОДЫ (правила, продублированы в CLAUDE.md):\n"
                "• Деплоить ТОЛЬКО через `python scripts/deploy.py` (не голым reflex deploy — утечёт приватка).\n"
                "• Обновление сайта = повторный запуск скрипта (пушит ЛОКАЛЬНЫЙ код, не GitHub).\n"
                "• Без пингера: тёплый старт <1с, кредиты только при визитах.\n"
                "• После деплоя проверять: главная 200 + внутренние доки 404.\n"
                "• Не гитайгнорить файлы, нужные приложению в рантайме (выпадут из деплоя).\n"
                "• Затык 'no access' → project select."
            )),
        _di("DASH-104", "Переписать CV под позиционирование «продуктовый дизайнер»",
            "To Do", "Task", "PM", _DASH_EPICS["E12"], 4, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["content", "release"], priority="High"),
        _di("DASH-105", "Hero-блоки остальных кейсов портфолио (реальные показатели-достижения)",
            "To Do", "Task", "DESIGN", _DASH_EPICS["E12"], 4, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["content", "release"]),
        _di("DASH-106", "Framer: структура и сборка кейс-страницы + встройка дашборда",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E12"], 4, 5, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["release", "ux"], priority="High"),
        _di("DASH-107", "Публикация кейса + отклик Muse (буфер 18-20.07: Tola)",
            "To Do", "Task", "PM", _DASH_EPICS["E12"], 4, 2, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["release"], priority="Highest",
            description="⏰ Жёсткий дедлайн вс 19.07 (сдвинут с 17.07). Отклики Muse + Tola ≤ 22.07."),

        # ── Backlog UX-улучшения (стейкхолдер-ревью 11.07 вечером) ───────────
        _di("DASH-108", "Backlog: мультивыбор в фильтрах (Squad, Type, Status и др.)",
            "To Do", "Story", "DEV", _DASH_EPICS["E9"], 5, 3, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            labels=["ux", "backlog"],
            description="Заменить одиночные select на мультивыбор (checkbox-список в дропдауне). "
                        "filtered() переходит от равенства к 'значение in выбранные'."),
        _di("DASH-109", "Backlog: числовая сортировка эпиков в фильтре (E1…E14)",
            "Done", "Bug", "DEV", _DASH_EPICS["E9"], 3, 1, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            started="2026-07-11T18:00:00.000+0000",
            resolved="2026-07-11T18:30:00.000+0000",
            labels=["ux", "backlog"],
            decision_note="epic_filter_options: sorted(seen) лексикографический (E1, E10, E11, …, E2) "
                          "→ сортировка по числовому суффиксу ключа."),
        _di("DASH-110", "Кликабельные key/name задач и эпиков во всём дашборде (не только Backlog)",
            "To Do", "Story", "DEV", _DASH_EPICS["E9"], 5, 5, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            labels=["ux"], priority="High",
            description="Вынести попап задачи/эпика из Backlog в глобальный компонент. "
                        "Кликабельность: Kanban-карточки, Roadmap Timeline/Sprint Review, вкладки ролей. "
                        "Один rx.dialog.root на страницу (Radix-правило).\n\n"
                        "На подумать (UX): что делать, если из попапа эпика пользователь кликает "
                        "на child issue и хочет попап задачи? Диалог у нас один, контент через rx.cond — "
                        "варианты: (а) замена контента в том же диалоге + кнопка «← назад к эпику» "
                        "(стек навигации в State), (б) хлебные крошки в шапке попапа "
                        "(DASH-EPIC-9 → DASH-57), (в) как в Jira — переход на полную страницу задачи. "
                        "Посмотреть, как это решает Jira в epic-панели.\n\n"
                        "На подумать (UX) №2: перетаскивание попапа по экрану (draggable dialog) — "
                        "если за попапом что-то не видно, закрывать-открывать заново не хочется. "
                        "Radix Dialog из коробки drag не умеет: нужен кастомный drag-handle на шапке "
                        "(state: dx/dy + transform) или отказ от modal-режима (non-modal + "
                        "pointer-events на фоне). Референсы: попап задачи в Linear/Height, "
                        "detail-панель Figma. Возможно, дешёвая альтернатива — сдвинуть попап "
                        "к краю экрана и сделать фон некликабельным, но прозрачным."),
        _di("DASH-111", "Актуализировать OKR-теги эпиков: сейчас у всех один тег",
            "Done", "Task", "PM", _DASH_EPICS["E10"], 4, 2, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            started="2026-07-12T21:30:00.000+0000",
            resolved="2026-07-12T21:50:00.000+0000",
            labels=["data", "process"], priority="High",
            description="Все DASH-задачи носят один okr_tag «Рекрутер понимает продуктовый контекст…». "
                        "Разнести по актуальным O0-O3 (okr_dash.py): E9→O2, E12/E13→O0 и т.д. "
                        "_di() должен принимать okr_tag параметром вместо константы.",
            decision_note="Закрыто 12.07: добавлена карта EPIC_OKR (эпик → tag цели O0-O3), _di() берёт "
                          "okr_tag из неё по эпику вместо хардкод-константы. Распределение: O0 North Star "
                          "(E12/E13, публикация+деплой), O1 Portfolio (E10/E11 + компонентные), O2 Design "
                          "Process (E9/E14/E7), O3 Quality (E4/E8). Все теги резолвятся в названия целей. "
                          "Видно в UI после рестарта reflex (данные грузятся при импорте)."),
        _di("DASH-112", "История изменений статусов в попапах задач и эпиков (как в Jira)",
            "To Do", "Story", "DEV", _DASH_EPICS["E9"], 5, 5, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            labels=["ux", "backlog"],
            description="Jira показывает History в Activity-секции: автор, поле, было → стало, дата. "
                        "Данные уже есть: changelog.histories в issue dict. "
                        "Изучить референс UI Jira (Activity → History) и повторить."),
        _di("DASH-113", "Бэкфилл changelog: восстановить историю статусов из логов сессий",
            "To Do", "Task", "ANALYSIS", _DASH_EPICS["E10"], 5, 5, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            labels=["data", "process"],
            description="Прочитать JSONL сессий (~/.claude/projects/), найти даты-время фактических смен "
                        "статусов и исполнителей для всех существующих задач; заполнить changelog.histories. "
                        "Договорённость в CLAUDE.md: заполняем регулярно при каждой смене статуса. "
                        "Связан с DASH-87 (spike про логи сессий)."),
        _di("DASH-114", "Backlog: drag-n-drop порядок колонок + ручная ширина колонок",
            "To Do", "Story", "DEV", _DASH_EPICS["E9"], 5, 8, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            labels=["ux", "backlog"], priority="Low",
            description="Перестановка колонок таблицы перетаскиванием, ресайз за границу колонки. "
                        "Состояние порядка/ширины — в BacklogState (сохранение на клиенте).\n\n"
                        "Идея на будущее: перетаскивание БЛОКОВ уместно не только в Backlog, а на ВСЕХ "
                        "вкладках (переставлять секции/карточки под себя). Это внимание к индивидуальным "
                        "привычкам пользователя — персонализация раскладки. Сохранять layout на клиенте per-таб."),
        _di("DASH-116", "Календарь спринта в дашборде: дни × эпики на вкладке Kanban",
            "Done", "Story", "PM", _DASH_EPICS["E10"], 3, 3, "Claude Code",
            created="2026-07-11T19:00:00.000+0000",
            started="2026-07-11T19:00:00.000+0000",
            resolved="2026-07-11T20:00:00.000+0000",
            labels=["ux", "process"], priority="High",
            description=(
                "Календарь спринта (ПМ-краш: недели × Deliverables → здесь дни × эпики) "
                "выведен в дашборд для ежедневной актуализации. Размещение на Kanban временное — "
                "Guzel решит, куда переместить."
            ),
            decision_note=(
                "data/sprint_calendar.py: SPRINT_DAYS (дата, этап, фокус) + SPRINT_ROWS (эпики × ключи задач) "
                "+ DEADLINE_KEYS (⏰). Компонент _sprint_calendar() в kanban.py, только dash-режим. "
                "Статусы НЕ дублируются — подтягиваются из mock-данных по ключу: обход автоматический "
                "(Done → зелёный, In Progress → жёлтый, To Do в прошедшем дне → красный). "
                "Договорённость в CLAUDE.md: при изменении календаря актуализировать оба места. "
                "Доработка: чипы кликабельны → попап задачи (переиспользован _popup() из backlog.py + "
                "BacklogState.open_issue; один dialog.root на страницу — Radix-правило). "
                "Первый шаг DASH-110 (кликабельность во всём дашборде)."
            )),
        _di("DASH-117", "Провенанс данных: 3 состояния бейджа вместо real/mock, аудит всех вкладок",
            "To Do", "Story", "PM", _DASH_EPICS["E10"], 4, 5, "Guzel K.",
            created="2026-07-11T20:30:00.000+0000",
            labels=["ux", "content", "data"], priority="High",
            description=(
                "Текущий data_source_badge бинарен (real/mock) и путает две оси: «реальность проекта» "
                "и «происхождение данных секции». Ставится по-секционно (overview.py имеет и real, и mock), "
                "но непоследовательно. Главная ложь: Jira-задачи KP и DASH — это РУЧНОЙ ЛОГ РЕАЛЬНОЙ РАБОТЫ "
                "(реальные проекты, исполнители Guzel+Claude, задачи оформлены вручную), а метятся как "
                "«Демо · модель Jira-интеграции» — занижают.\n\n"
                "Решение: 3 состояния провенанса в _SOURCE_MAP (badge.py):\n"
                "• extracted — «Данные из реального источника» (database): vault_snapshot, real_project_extract;\n"
                "• logged — «Реальная работа · задачи ведём вручную» (pen/notebook): таск-борды KP + DASH;\n"
                "• demo — «Демо · вымышленный проект» (flask): только Motif (generate_raw_issues).\n\n"
                "Аудит ~60 вызовов data_source_badge по всем pages/: выбрать честное состояние для каждой секции. "
                "Календарь спринта (kanban.py) → logged. Это усиливает позиционирование: реальный продуктовый "
                "процесс, а не демо. Связано с DASH-95 (правило соответствия данных проекту)."
            )),
        _di("DASH-123", "Баг: Backlog Issues без детерминированной сортировки (порядок «плывёт» при фильтре)",
            "Done", "Bug", "DEV", _DASH_EPICS["E9"], 5, 2, "Claude Code",
            created="2026-07-12T22:40:00.000+0000",
            started="2026-07-12T22:40:00.000+0000",
            resolved="2026-07-12T23:00:00.000+0000",
            labels=["ux", "backlog"], priority="Medium",
            description=(
                "Симптом (Guzel 12.07): список Issues без фильтра выглядит по возрастанию номера, но при "
                "включении фильтра порядок непонятный; также казалось, что показывает максимум ~115 из 122.\n"
                "Причина: (1) filtered() отдавал строки в порядке ФАЙЛА (get_dash_issues), а он не строго по "
                "номеру (вставки/аппенды: DASH-121→58, хвост 116,117,…,115) → без фильтра похоже на "
                "возрастание (DASH-1..90 писались по порядку), с фильтром обнажается хаос. (2) «115» — "
                "устаревшие данные на запущенном сервере (грузятся при импорте; новые задачи после рестарта)."
            ),
            decision_note="Фикс: filtered() теперь rows.sort(key=_key_num) — числовая сортировка по номеру "
                          "задачи. Одинаковый порядок с фильтром и без. Хелпер _key_num (DASH-100→100). "
                          "Полноценная сортировка по клику на любую колонку — отдельно DASH-115."),
        _di("DASH-124", "Аудит всей кодовой базы (архитектура, техдолг, мёртвый код, безопасность)",
            "To Do", "Task", "ARCH", _DASH_EPICS["E13"], 5, 5, "Claude Code",
            created="2026-07-13T16:00:00.000+0000",
            labels=["architecture", "tech-debt"], priority="High",
            description=(
                "Холистический проход по ВСЕМУ коду (не диф) — диф-ревью такое не ловит, проблемы "
                "накапливаются. Последний полный аудит — DASH-82 (нач. июля), с тех пор ~10 дней бурных "
                "изменений (dash_app rename, эпики/иерархия, календарь, рефакторы Backlog, деплой). Репо "
                "публичный (задеплоен + GitHub) → дизайн-лид может открыть код.\n"
                "Охват: архитектурный дрейф, дублирование через файлы (DASH-70: ~20 самодельных таблиц), "
                "мёртвый код, консистентность паттернов, безопасность (что уезжает в деплой), качество "
                "для рекрутера. Многоагентный, глубокий. План — Сб 18 (вместе с UI/UX-полировкой, "
                "качество кода = часть «5+»), но можем раньше. После — обновить строку 'последний аудит' в CLAUDE.md."
            )),
        _di("DASH-125", "Аналитика посещений + тепловые карты (Framer + Reflex-дашборд)",
            "To Do", "Story", "PA", _DASH_EPICS["E12"], 5, 5, "Guzel K.",
            created="2026-07-13T16:00:00.000+0000",
            labels=["research", "growth"], priority="Medium",
            description=(
                "Мерить вовлечённость рекрутеров на ДВУХ поверхностях:\n"
                "1) ПОРТФОЛИО на Framer — узнать, как аналитика/heatmaps устроены там (встроенная Framer "
                "Analytics? интеграция GA/Plausible? heatmaps через Hotjar/Clarity?).\n"
                "2) ДАШБОРД на Reflex (product-dashboard-teal-ring.reflex.run) — добавить JS-аналитику + heatmap.\n"
                "Кандидаты: аналитика — Plausible/GA/PostHog; heatmaps+записи сессий — Microsoft Clarity "
                "(бесплатно) / Hotjar / PostHog. Важно: JS-инструменты, поэтому чисто (пингера нет, да он и не "
                "нужен — DASH-103). Скорее post-publish / 2-я итерация — аналитику можно добавить после запуска."
            ),
            decision_note=(
                "ИССЛЕДОВАНИЕ (13.07) → wiki/analytics_heatmaps_research.md. Рекомендация: Microsoft Clarity "
                "на ОБЕ поверхности — бесплатно без лимитов, heatmaps + записи сессий + базовая аналитика, "
                "один инструмент. Оговорка: MS обучает AI на данных (для публичного портфолио низкая "
                "чувствительность); privacy-альтернативы — PostHog (self-host) / Hotjar. Framer: встроенная "
                "аналитика есть (free), heatmaps — только через custom-скрипт. Reflex: скрипт через "
                "rx.App(head_components=[rx.script(...)]) → передеплой. Внедрение — post-publish (не блокирует "
                "вс 19). Остаётся: аккаунт + вставка сниппета в Framer (custom code) и в dash_app.py."
            )),
        _di("DASH-126", "Practices & Rules (info): разделить по проектам (_by_project)",
            "To Do", "Task", "ARCH", _DASH_EPICS["E13"], 5, 5, "Claude Code",
            created="2026-07-13T18:00:00.000+0000",
            labels=["architecture", "refactor"], priority="Medium",
            description=(
                "Находка 13.07: вкладка info (Practices & Rules) — одна из трёх (about/info/ds), что НЕ "
                "обёрнуты в _by_project и потому одинаковы на все 3 проекта. Контент info описывает "
                "КОМАНДНЫЙ процесс Motif (Scrumban, CI/CD, squad-standup, календарь церемоний) — для KP "
                "(соло-пайплайн без команды и церемоний) это вводит в заблуждение.\n"
                "Сделать: обернуть ('info', _by_project(motif=info_tab(), kp=<соло-вариант: «церемоний "
                "нет, соло-процесс»>, dash=<вариант для дашборда>)). Образец — About уже разделён "
                "(router.py, motif_about_tab). После About, не блокирует."
            ),
            decision_note=(
                "Архитектура разделения здоровая (_by_project на ~14 вкладок + project_mode в данных). "
                "Проблема локальная: about/info/ds «не подписаны» на механизм. about закрыт DASH-About-работой; "
                "info и ds — отдельными задачами (DASH-126/127)."
            )),
        _di("DASH-127", "Design System (ds): разделить по проектам (_by_project)",
            "To Do", "Task", "ARCH", _DASH_EPICS["E13"], 5, 5, "Claude Code",
            created="2026-07-13T18:00:00.000+0000",
            labels=["architecture", "refactor"], priority="Low",
            description=(
                "Вкладка ds (Design System) — вторая из необёрнутых в _by_project (см. DASH-126). "
                "DS у каждого проекта своя → обернуть ('ds', _by_project(motif=ds_tab(), kp=…, dash=…)). "
                "Приоритет ниже info: DS-инструмента дашборда отчасти законно общая, но по решению Guzel "
                "делаем свой вариант под каждый проект. После info."
            )),
        _di("DASH-128", "About project: рабочий стол истории (DnD-раскладка банков → карточки + таймлайн)",
            "Done", "Story", "DESIGN", _DASH_EPICS["E10"], 4, 8, "Claude Code",
            created="2026-07-15T12:00:00.000+0000",
            started="2026-07-15T12:00:00.000+0000",
            resolved="2026-07-17T14:00:00.000+0000",
            labels=["ux", "content", "tool"], priority="High",
            description=(
                "ТЗ Guzel: превратить About (Motif) в рабочий стол сборки истории. Разделы по порядку: "
                "Команда (карточки слева, скроллится только левый блок; личные банки — черты/личные события "
                "— справа) → JTBD → RACI → GOALS → Артефакты → Расписание (2 нед) → Факторы и история "
                "(таймлайн: дорожки = сюжетные банки, снизу дорожка СПАЙНА из 5 кусков Ставка→…→Послевкусие; "
                "справа сюжетные банки) → Дневники → Цитаты → Сценарий.\n"
                "Интеракция: drag-n-drop строки банка → на карточку героя / на дорожку таймлайна; обратно в "
                "банк = удалить. Одна строка может быть на нескольких карточках (регулируется вручную). На "
                "таймлайне фактор = блок длиной в дни/диапазон дней (по-часовой ресайз — после публикации); "
                "несколько из одного банка штабелируются по вертикали в своей дорожке. Расписание(6) и сетка "
                "дней в Факторы-и-история(7) — одни данные, два вида (правка в 6 → обновляет 7). Высота = vh. "
                "Учёт для истории/дневников/сценария — через СКРИНШОТ финальной раскладки (Guzel шлёт, Claude "
                "читает и пишет). Новые разделы хостят wiki-контент (Guzel удобнее работать в дашборде, не в .md)."
            ),
            decision_note=(
                "ФАЗЫ (реш. 15.07): 1) структура + новые разделы + двухколоночная Команда + скелет таймлайна "
                "со спайн-дорожкой; 2) DnD банк→карточка (без ресайза); 3) упрощённый DnD банк→таймлайн (дни, "
                "не часы). Обоснование Guzel: сценарий — бутылочное горло; интерфейс с фикс-точками де-рискует "
                "«плавание» Claude в логике и ускоряет сценарий. DnD в Reflex тяжёл — пробуем, туго → стоп. "
                "ГОТОВ (16.07): все 3 фазы + reorder дорожек (грип) + общие дорожки (8, до 20) + 14 дней с "
                "выходными + неравный спайн + панель «Раскладка текстом» + наполнены разделы (JTBD/RACI/GOALS/"
                "Дневники/Цитаты/Бэкстори/Сценарий) + грейды/инвестор/MVP. DnD завёлся (кастомный _DragDiv)."
            )),
        _di("DASH-115", "Backlog: сортировка по клику на заголовок колонки",
            "To Do", "Story", "DEV", _DASH_EPICS["E9"], 5, 5, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            labels=["ux", "backlog"], priority="Low",
            description="Возобновляет отложенный план «сортировка таблиц» (memory project_table_sorting): "
                        "клик по заголовку — asc/desc/сброс, индикатор стрелкой. Позже — поиск по колонкам."),
    ]

    # ── Issue links ───────────────────────────────────────────────────────────
    _link = lambda rel, key: {"type": {"name": rel, "inward": rel.lower(), "outward": rel.lower()},
                               "outwardIssue": {"key": key}}
    _block = lambda key: {"type": {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"},
                           "inwardIssue": {"key": key}}

    links_map = {
        "DASH-4":  [_link("Relates", "DASH-5"), _link("Relates", "DASH-6")],
        "DASH-5":  [_link("Relates", "DASH-4")],
        "DASH-10": [_block("DASH-26"), _block("DASH-27")],
        "DASH-29": [_block("DASH-31")],
        "DASH-31": [_link("Relates", "DASH-32")],
        "DASH-33": [_link("Relates", "DASH-31")],
        "DASH-44": [_link("Relates", "DASH-39"), _link("Relates", "DASH-40"),
                    _link("Relates", "DASH-41"), _link("Relates", "DASH-42"),
                    _link("Relates", "DASH-43")],
        "DASH-45": [_block("DASH-44")],
        "DASH-47": [_block("DASH-45"), _block("DASH-46")],
        "DASH-48": [_link("Relates", "DASH-14")],
        "DASH-49": [_link("Relates", "DASH-21")],
        "DASH-50": [_link("Relates", "DASH-13")],
        "DASH-53": [_link("Relates", "DASH-20")],
        "DASH-54": [_block("DASH-47")],
        "DASH-55": [_block("DASH-48"), _block("DASH-53"), _block("DASH-54")],
        "DASH-57": [_link("Relates", "DASH-53")],
        "DASH-58": [_link("Relates", "DASH-57")],
        "DASH-59": [_link("Relates", "DASH-57"), _link("Relates", "DASH-58")],
        "DASH-60": [_link("Relates", "DASH-57"), _link("Relates", "DASH-58"), _link("Relates", "DASH-59")],
        "DASH-62": [_block("DASH-61")],
        "DASH-63": [_block("DASH-62")],
        "DASH-64": [_block("DASH-65")],
        "DASH-65": [_block("DASH-66"), _block("DASH-67")],
        "DASH-66": [_block("DASH-67")],
        "DASH-67": [_block("DASH-68")],
        "DASH-69": [_block("DASH-64")],
        "DASH-72": [_block("DASH-61")],
        "DASH-74": [_link("Relates", "DASH-75"), _link("Relates", "DASH-76"),
                    _link("Relates", "DASH-77"), _link("Relates", "DASH-78"), _link("Relates", "DASH-79")],
        "DASH-82": [_block("DASH-70"), _block("DASH-71"), _block("DASH-55")],
        # Спринт 11-17.07 (перенарезка DASH-95)
        "DASH-92": [_block("DASH-63")],                              # токены до hi-fi
        # История команды — перекомпоновка в 6 блоков (12.07). Блок 1 (DASH-64) — корень.
        "DASH-64": [_block("DASH-65"), _block("DASH-98"), _block("DASH-99"),
                    _block("DASH-100"), _block("DASH-97")],          # Блок 1 блокирует всё
        "DASH-100": [_block("DASH-101")],                            # Блок 3 сценарий → Блок 4 отрисовка
        "DASH-101": [_block("DASH-102"), _block("DASH-122")],        # отрисовка → встройка + музыка
        "DASH-65": [_link("Relates", "DASH-97")],                    # дневники питают данные
        "DASH-103": [_block("DASH-106")],                            # деплой блокирует Framer-сборку
        "DASH-104": [_block("DASH-106")],
        "DASH-105": [_block("DASH-106")],
        "DASH-106": [_block("DASH-107")],                            # сборка до публикации
        "DASH-93": [_link("Relates", "DASH-90"), _link("Relates", "DASH-81")],
        "DASH-110": [_link("Relates", "DASH-90")],
        "DASH-112": [_block("DASH-113")],   # сначала UI истории, потом бэкфилл данных
        "DASH-113": [_link("Relates", "DASH-87")],
        "DASH-114": [_link("Relates", "DASH-115")],
    }
    for issue in issues:
        key = issue["key"]
        if key in links_map:
            issue["issuelinks"] = links_map[key]

    return issues
