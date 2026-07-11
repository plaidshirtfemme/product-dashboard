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
            CF_OKR_TAG: "Рекрутер понимает продуктовый контекст без объяснений",
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
            "In Progress", "task", "ANALYSIS", _DASH_EPICS["E10"], 3, 8, "Claude Code",
            created="2026-07-09T13:00:00.000+0000",
            started="2026-07-09T13:30:00.000+0000",
            resolved=None,
            labels=["content", "process"],
            priority="High"),
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
            "To Do", "task", "ANALYSIS", _DASH_EPICS["E10"], 4, 3, "Guzel K.",
            created="2026-07-07T12:00:00.000+0000",
            labels=["process"]),
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
                "Установить и настроить официальный Figma MCP-сервер. "
                "После — Claude Code сможет читать фреймы из Figma и писать Reflex-компоненты на их основе. "
                "Параллельно: подключить Tokens Studio плагин к design_tokens.json."
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
                "Демонстрирует Figma proficiency для вакансии Muse."
            )),

        # ── Командный сценарий и комикс ───────────────────────────────────────
        _di("DASH-64", "Написать единый сценарий 2-недельного спринта команды",
            "To Do", "Story", "PM", _DASH_EPICS["E10"], 8, 5, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["content", "discovery"],
            priority="High",
            description=(
                "Единая канва событий спринта, которую каждая роль переживает по-своему. "
                "От этого сценария зависят: задачи Jira в MOTIF_DEMO_CONFIG, дневники ролей, комикс. "
                "Включает: цель спринта, ключевые события (планирование, инциденты, решения, ретро), "
                "конфликты и развязки для каждой роли."
            )),

        _di("DASH-65", "Написать дневники ролей: BA, SA, PA, PD, Dev, QA, Growth",
            "To Do", "Story", "PM", _DASH_EPICS["E10"], 8, 5, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["content", "ux"],
            priority="High",
            description=(
                "7 дневников — одни и те же события спринта глазами разных ролей. "
                "PM-дневник уже готов: wiki/pm_role_sprint_diary.md. "
                "Каждый дневник: голос персонажа, его задачи Jira, блокеры, эмоции, рабочий контекст. "
                "Хранение: wiki/[role]_role_sprint_diary.md"
            )),

        _di("DASH-66", "Разработать концепцию комикса: персонажи, раскадровка, стиль",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E11"], 8, 5, "Guzel K.",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux", "content"],
            description=(
                "Комикс о 2-недельном спринте команды — один сценарий, взгляд от лица каждой роли. "
                "Артефакты: визуальные персонажи (портреты/стиль), раскадровка эпизодов, "
                "плейлисты для каждого персонажа (музыка во время рабочего дня). "
                "Демонстрирует: сильные User Personas, Journey Map, онбординг через нарратив."
            )),

        _di("DASH-67", "Создать UI комикса в дашборде (новая вкладка или страница)",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E11"], 8, 8, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            labels=["ux", "content"],
            description=(
                "Реализовать интерактивный комикс в Reflex: "
                "слайды с иллюстрациями, текстом от лица персонажей, встроенные треки/плейлисты. "
                "Делает дашборд запоминающимся артефактом портфолио."
            )),

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
            "To Do", "Spike", "DEV", _DASH_EPICS["E10"], 8, 5, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            labels=["spike", "content"],
            description=(
                "Сейчас ~103 задачи в generate_raw_issues() случайны. "
                "После написания единого сценария (DASH-64) — переписать данные чтобы "
                "они рассказывали ту же историю что комикс и дневники. "
                "Блокирован: DASH-64 должен быть готов первым."
            )),

        # ── Технический долг (рефакторинг из плана) ──────────────────────────
        _di("DASH-70", "Рефакторинг компонентов: универсальный data_table, вынос молекул",
            "To Do", "Task", "DEV", _DASH_EPICS["E13"], 5, 5, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            labels=["tech-debt", "architecture"],
            description=(
                "32 инлайн-молекулы в page-файлах → вынести в components/. "
                "Дублирование: _tasks_table (4×), _bug_table (3×), _legend (4×). "
                "Универсальный data_table_wrapper (шапка + строки + overflow)."
            )),

        _di("DASH-71", "Рефакторинг кода: router, god-файл kp_dashboard.py",
            "To Do", "Task", "DEV", _DASH_EPICS["E13"], 3, 3, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            labels=["tech-debt"],
            description=(
                "real_page_wrapper() — общий wrapper для всех real_*.py. "
                "stat_card — keyword-only аргументы после value. "
                "Разбить god-файл kp_dashboard.py если разросся."
            )),

        _di("DASH-72", "Spike: Claude Design интеграция — код → макеты → код",
            "To Do", "Spike", "DESIGN", _DASH_EPICS["E14"], 3, 3, "Claude Code",
            created="2026-07-09T10:00:00.000+0000",
            labels=["spike", "architecture"],
            description=(
                "Исследовать workflow: Claude Design читает компоненты → генерирует макеты. "
                "Зависит от: DASH-61 (Figma MCP настроен)."
            )),

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
            "To Do", "Task", "DEV", _DASH_EPICS["E13"], 3, 3, "Claude Code",
            created="2026-07-10T10:00:00.000+0000",
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
            )),

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
            "To Do", "Spike", "ARCH", _DASH_EPICS["E13"], 3, 3, "Guzel K.",
            created="2026-07-10T12:00:00.000+0000",
            labels=["spike", "architecture", "process"],
            priority="Low",
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
            "To Do", "Story", "PM", _DASH_EPICS["E10"], 3, 5, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["content", "discovery"], priority="High",
            description="Расширяет DASH-64 (сценарий спринта): бизнес-контекст легенды — кто финансирует, "
                        "какие Goals с цифрами, 2-3 решённых кризиса (антидот риску «картонной команды»). "
                        "Текстом, вс 12.07 — вместе со сценарием комикса (DASH-100), не переключаясь."),
        _di("DASH-100", "Сценарий комикса по истории команды",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E11"], 3, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["content", "ux"], priority="High",
            description="Сценарий (текст) из той же истории, что DASH-96. Питает DASH-66 (концепция/раскадровка)."),
        _di("DASH-97", "Легенда → mock-данные: вшить кризисы и Goals в MOTIF-данные",
            "To Do", "Task", "DEV", _DASH_EPICS["E10"], 4, 5, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            labels=["content", "data"], priority="High",
            description="Перенести историю из DASH-96 в данные (связан с DASH-69)."),
        _di("DASH-98", "Карточки персон команды: цитаты, JTBD, RACI",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E10"], 4, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["ux", "content"],
            description="Закрывает пробел Double Diamond «User personas — частично»: "
                        "визуальные карточки поверх USER_STORIES.md + RACI-матрица по Deliverables."),
        _di("DASH-99", "Карта обмена артефактами PD ↔ команда (визуализация на дашборде)",
            "To Do", "Story", "ANALYSIS", _DASH_EPICS["E10"], 4, 3, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["ux", "content"],
            description="PD в центре, стрелки входящие/исходящие по ролям (таблица в CLAUDE.md). "
                        "Место: вкладка ролей/RACI или Design Process tab."),
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
        _di("DASH-101", "Отрисовка комикса",
            "To Do", "Story", "DESIGN", _DASH_EPICS["E11"], 4, 5, "Guzel K.",
            created="2026-07-11T10:00:00.000+0000",
            labels=["ux", "content"], priority="High"),
        _di("DASH-102", "Встроить комикс в дашборд/кейс",
            "To Do", "Task", "DEV", _DASH_EPICS["E11"], 4, 3, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            labels=["ux", "content"], priority="High",
            description="Наполнение контентом UI из DASH-67."),
        _di("DASH-103", "Деплой дашборда (Railway/Fly.io/VPS) — публичный URL",
            "To Do", "Task", "ARCH", _DASH_EPICS["E13"], 4, 3, "Claude Code",
            created="2026-07-11T10:00:00.000+0000",
            labels=["release", "architecture"], priority="High",
            description="По решению DASH-88: дашборд отдельно, Framer даёт кнопку-ссылку. Блокирует Framer-сборку."),
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
            description="⏰ Жёсткий дедлайн пт 17.07. KR2: отклики Muse + Tola ≤ 20.07."),

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
            "To Do", "Task", "PM", _DASH_EPICS["E10"], 4, 2, "Claude Code",
            created="2026-07-11T18:00:00.000+0000",
            labels=["data", "process"], priority="High",
            description="Все DASH-задачи носят один okr_tag «Рекрутер понимает продуктовый контекст…». "
                        "Разнести по актуальным O0-O3 (okr_dash.py): E9→O2, E12/E13→O0 и т.д. "
                        "_di() должен принимать okr_tag параметром вместо константы."),
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
                        "Состояние порядка/ширины — в BacklogState (сохранение на клиенте)."),
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
        "DASH-96": [_link("Relates", "DASH-64"), _block("DASH-97"),
                    _block("DASH-100")],                             # история питает данные и комикс
        "DASH-100": [_block("DASH-66"), _block("DASH-101")],         # сценарий до раскадровки и отрисовки
        "DASH-101": [_block("DASH-102")],                            # отрисовка до встройки
        "DASH-97": [_link("Relates", "DASH-69")],
        "DASH-98": [_link("Relates", "DASH-65")],
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
