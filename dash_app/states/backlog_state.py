"""
Reactive state for the Backlog tab.

All 103 issues are pre-serialised to plain dicts at import time so that
Reflex can store them in State and filter them reactively via @rx.var.
The filter values (squad, type, status, …) live in State vars and update
on every dropdown change without a page reload.
"""

from __future__ import annotations

from collections import defaultdict

import reflex as rx

from ..data.adapter import load_issues
from ..data.okr import load_okrs
from ..data.okr_dash import load_dash_okrs
from ..data.jira_mock_raw import DASH_CONFIG
from . import ProjectState

_OKR_TITLES: dict[str, str] = {obj.tag: obj.title for obj in load_okrs()}
_OKR_TITLES_DASH: dict[str, str] = {obj.tag: obj.title for obj in load_dash_okrs()}

# ---------------------------------------------------------------------------
# Serialise issues once at module load
# ---------------------------------------------------------------------------

def _to_dict(i, okr_titles: dict) -> dict:
    return {
        "key": i.key,
        "squad_key": i.squad_key,
        "epic": i.epic,
        "issue_type": i.issue_type,
        "status": i.status,
        "priority": i.priority or "",
        "severity": i.severity or "",
        "story_points": i.story_points,
        "sprint_name": i.sprint_name or "",
        "okr_tag": i.okr_tag,
        "okr_title": okr_titles.get(i.okr_tag, i.okr_tag),
        "cycle_time": f"{i.cycle_time_days} дн." if i.cycle_time_days else "—",
        "lead_time": f"{i.lead_time_days} дн." if i.lead_time_days else "—",
        "rework_count": i.rework_count,
        # DoD indicator: instrumentation added (mock: Done stories/experiments without rework)
        "tracking_added": (
            "yes" if i.status == "Done" and i.issue_type in ("story", "experiment") and i.rework_count == 0
            else "no" if i.status == "Done" and i.issue_type in ("story", "experiment")
            else "na"
        ),
        "blocked": "Да" if i.blocked_by else "",
        "assignee": i.assignee or "",
        "fix_version": i.fix_version or "",
        "release_slipped": "Да" if i.release_slipped else "",
    }


_ALL:      list[dict] = [_to_dict(i, _OKR_TITLES)      for i in load_issues()]
_ALL_DASH: list[dict] = [_to_dict(i, _OKR_TITLES_DASH) for i in load_issues(DASH_CONFIG)]

# Option lists for filter dropdowns
_STATUSES   = ["Done", "In Progress", "In Review", "To Do"]
_PRIORITIES = ["Highest", "High", "Medium", "Low", "Lowest"]
_SEVERITIES = ["Blocker", "Critical", "Major", "Minor", "Trivial"]

def _options(data: list[dict]):
    return {
        "squads":  sorted({d["squad_key"]  for d in data}),
        "types":   sorted({d["issue_type"] for d in data}),
        "sprints": sorted({d["sprint_name"] for d in data if d["sprint_name"]}),
        "epics":   sorted({d["epic"]        for d in data}),
        "okrs":    sorted({d["okr_tag"]     for d in data if d["okr_tag"]}),
    }

_OPTS      = _options(_ALL)
_OPTS_DASH = _options(_ALL_DASH)

# Exposed for the page (default = demo/motif)
SQUAD_OPTIONS    = _OPTS["squads"]
TYPE_OPTIONS     = _OPTS["types"]
STATUS_OPTIONS   = _STATUSES
PRIORITY_OPTIONS = _PRIORITIES
SEVERITY_OPTIONS = _SEVERITIES
SPRINT_OPTIONS   = _OPTS["sprints"]
EPIC_OPTIONS     = _OPTS["epics"]
OKR_OPTIONS      = _OPTS["okrs"]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class BacklogState(ProjectState):
    # project_mode inherited from ProjectState

    # ── filter values ────────────────────────────────────────────────────────
    squad:    str = ""
    type_:    str = ""
    status:   str = ""
    priority: str = ""
    severity: str = ""
    sprint:   str = ""
    epic:     str = ""
    okr:      str = ""

    # ── display mode ────────────────────────────────────────────────────────
    mode: str = "issues"   # "issues" | "epics"

    # ── event handlers ───────────────────────────────────────────────────────
    def set_squad(self, v: str):    self.squad    = v
    def set_type(self, v: str):     self.type_    = v
    def set_status(self, v: str):   self.status   = v
    def set_priority(self, v: str): self.priority = v
    def set_severity(self, v: str): self.severity = v
    def set_sprint(self, v: str):   self.sprint   = v
    def set_epic(self, v: str):     self.epic     = v
    def set_okr(self, v: str):      self.okr      = v
    def set_mode(self, v: str):     self.mode     = v

    def reset_filters(self):
        self.squad = self.type_ = self.status = self.priority = ""
        self.severity = self.sprint = self.epic = self.okr = ""
        self.mode = "issues"

    # ── computed vars ────────────────────────────────────────────────────────
    @rx.var
    def filtered(self) -> list[dict]:
        rows = _ALL_DASH if self.project_mode == "dash" else _ALL
        if self.squad:    rows = [r for r in rows if r["squad_key"]  == self.squad]
        if self.type_:    rows = [r for r in rows if r["issue_type"] == self.type_]
        if self.status:   rows = [r for r in rows if r["status"]     == self.status]
        if self.priority: rows = [r for r in rows if r["priority"]   == self.priority]
        if self.severity: rows = [r for r in rows if r["severity"]   == self.severity]
        if self.sprint:   rows = [r for r in rows if r["sprint_name"]== self.sprint]
        if self.epic:     rows = [r for r in rows if r["epic"]       == self.epic]
        if self.okr:      rows = [r for r in rows if r["okr_tag"]    == self.okr]
        return rows

    @rx.var
    def filtered_count(self) -> int:
        return len(self.filtered)

    @rx.var
    def epic_rows(self) -> list[dict]:
        by_epic: dict[str, list[dict]] = defaultdict(list)
        for r in self.filtered:  # type: ignore[attr-defined]
            by_epic[r["epic"]].append(r)
        result = []
        for epic, rows in sorted(by_epic.items()):
            done = sum(1 for r in rows if r["status"] == "Done")
            total = len(rows)
            sp_total = sum(r["story_points"] for r in rows)
            sp_done  = sum(r["story_points"] for r in rows if r["status"] == "Done")
            squads   = ", ".join(sorted({r["squad_key"] for r in rows}))
            result.append({
                "epic":     epic,
                "okr_tag":  rows[0]["okr_tag"],
                "okr_title": rows[0].get("okr_title", rows[0]["okr_tag"]),
                "squads":   squads,
                "total":    total,
                "done":     done,
                "done_pct": round(100 * done / total) if total else 0,
                "sp_total": sp_total,
                "sp_done":  sp_done,
                "in_progress": sum(1 for r in rows if r["status"] == "In Progress"),
                "bugs":     sum(1 for r in rows if r["issue_type"] == "bug"),
            })
        return result

    @rx.var
    def has_active_filters(self) -> bool:
        return bool(self.squad or self.type_ or self.status or self.priority
                    or self.severity or self.sprint or self.epic or self.okr)

    # ── reactive dropdown options (switch by project_mode) ───────────────────
    @rx.var
    def squad_options(self) -> list[str]:
        return _OPTS_DASH["squads"] if self.project_mode == "dash" else _OPTS["squads"]

    @rx.var
    def type_options(self) -> list[str]:
        return _OPTS_DASH["types"] if self.project_mode == "dash" else _OPTS["types"]

    @rx.var
    def sprint_options(self) -> list[str]:
        return _OPTS_DASH["sprints"] if self.project_mode == "dash" else _OPTS["sprints"]

    @rx.var
    def epic_options(self) -> list[str]:
        return _OPTS_DASH["epics"] if self.project_mode == "dash" else _OPTS["epics"]

    @rx.var
    def okr_options(self) -> list[str]:
        return _OPTS_DASH["okrs"] if self.project_mode == "dash" else _OPTS["okrs"]
