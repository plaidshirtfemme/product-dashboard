"""
Reactive state for the Backlog tab.

All issues are pre-serialised to plain dicts at import time so that
Reflex can store them in State and filter them reactively via @rx.var.
"""

from __future__ import annotations

from collections import defaultdict

import reflex as rx

from ..data.adapter import load_issues
from ..data.okr import load_okrs
from ..data.okr_dash import load_dash_okrs
from ..data.jira_mock_raw import DASH_CONFIG, EPIC_NAMES, EPIC_TYPES, EPIC_UNLOCKS
from . import ProjectState

# Порядок групп в режиме Epics: business → enabler → component (DASH-93)
_EPIC_TYPE_ORDER = {"business": 0, "enabler": 1, "component": 2}


def _epic_sort_key(epic_key: str) -> tuple[int, int]:
    tail = epic_key.rsplit("-", 1)[-1]
    num = int(tail) if tail.isdigit() else 0
    return (_EPIC_TYPE_ORDER.get(EPIC_TYPES.get(epic_key, ""), 3), num)

_OKR_TITLES: dict[str, str] = {obj.tag: obj.title for obj in load_okrs()}
_OKR_TITLES_DASH: dict[str, str] = {obj.tag: obj.title for obj in load_dash_okrs()}

# ---------------------------------------------------------------------------
# Serialise issues once at module load
# ---------------------------------------------------------------------------

def _to_dict(i, okr_titles: dict) -> dict:
    return {
        "key": i.key,
        "summary": i.summary,
        "squad_key": i.squad_key,
        "epic": i.epic,
        "epic_name": i.epic_name,
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
        "tracking_added": (
            "yes" if i.status == "Done" and i.issue_type in ("story", "experiment") and i.rework_count == 0
            else "no" if i.status == "Done" and i.issue_type in ("story", "experiment")
            else "na"
        ),
        "blocked": "Да" if i.blocked_by else "",
        "assignee": i.assignee or "",
        "fix_version": i.fix_version or "",
        "release_slipped": "Да" if i.release_slipped else "",
        "description": i.description or "",
        "decision_note": i.decision_note or "",
        "labels": ", ".join(i.labels) if i.labels else "",
        "created_at": i.created_at.strftime("%Y-%m-%d") if i.created_at else "",
    }


_ALL:      list[dict] = [_to_dict(i, _OKR_TITLES)      for i in load_issues()]
_ALL_DASH: list[dict] = [_to_dict(i, _OKR_TITLES_DASH) for i in load_issues(DASH_CONFIG)]

# Reverse map epic name → key, per mode. Used to keep the Epic KEY column in sync
# when a user reassigns an issue's Epic Link by name in the popup (the select
# yields a name, but grouping/filter key off r["epic"]).
_NAME_TO_KEY:      dict[str, str] = {d["epic_name"]: d["epic"] for d in _ALL      if d["epic_name"]}
_NAME_TO_KEY_DASH: dict[str, str] = {d["epic_name"]: d["epic"] for d in _ALL_DASH if d["epic_name"]}

# Static option lists
_STATUSES   = ["Done", "In Progress", "In Review", "To Do"]
_PRIORITIES = ["Highest", "High", "Medium", "Low", "Lowest"]
_SEVERITIES = ["Blocker", "Critical", "Major", "Minor", "Trivial"]


def _options(data: list[dict]) -> dict:
    return {
        "squads":     sorted({d["squad_key"]  for d in data}),
        "types":      sorted({d["issue_type"] for d in data}),
        "sprints":    sorted({d["sprint_name"] for d in data if d["sprint_name"]}),
        "epics":      sorted({d["epic"]        for d in data}),
        "epic_names": sorted({d["epic_name"]   for d in data if d["epic_name"]}),
        "okrs":       sorted({d["okr_tag"]     for d in data if d["okr_tag"]}),
    }


_OPTS      = _options(_ALL)
_OPTS_DASH = _options(_ALL_DASH)

# Exposed for the page
SQUAD_OPTIONS    = _OPTS["squads"]
TYPE_OPTIONS     = _OPTS["types"]
STATUS_OPTIONS   = _STATUSES
PRIORITY_OPTIONS = _PRIORITIES
SEVERITY_OPTIONS = _SEVERITIES
EPIC_OPTIONS     = _OPTS["epic_names"]
OKR_OPTIONS      = _OPTS["okrs"]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class BacklogState(ProjectState):

    # ── ALL STATE VARS first (Reflex processes declarations in order) ─────────

    # filter values
    squad:    str = ""
    type_:    str = ""
    status:   str = ""
    priority: str = ""
    severity: str = ""
    sprint:   str = ""
    epic:     str = ""   # holds epic KEY (e.g. "DASH-EPIC-1") for filtering
    okr:      str = ""

    # display mode
    mode: str = "issues"   # "issues" | "epics"

    # issue popup
    selected_key: str = ""
    _priority_overrides: dict[str, str] = {}
    _epic_overrides: dict[str, str] = {}   # issue_key → new epic_name

    # epic popup  ← MUST be declared before any method that references it
    selected_epic_key: str = ""   # e.g. "DASH-EPIC-1"

    # ── event handlers ───────────────────────────────────────────────────────

    def open_issue(self, key: str):
        self.selected_key = key
        self.selected_epic_key = ""

    def close_issue(self):
        self.selected_key = ""

    def set_issue_priority(self, priority: str):
        if self.selected_key:
            self._priority_overrides[self.selected_key] = priority

    def set_issue_epic(self, epic_name: str):
        if self.selected_key:
            self._epic_overrides[self.selected_key] = epic_name

    def open_epic(self, epic_key: str):
        self.selected_epic_key = epic_key
        self.selected_key = ""

    def close_epic(self):
        self.selected_epic_key = ""

    def close_popup(self):
        self.selected_key = ""
        self.selected_epic_key = ""

    # ── event handlers ────────────────────────────────────────────────────────
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

    # ── computed vars ─────────────────────────────────────────────────────────
    @rx.var
    def filtered(self) -> list[dict]:
        is_dash = self.project_mode == "dash"
        rows = _ALL_DASH if is_dash else _ALL
        name_to_key = _NAME_TO_KEY_DASH if is_dash else _NAME_TO_KEY
        rows = [
            {
                **r,
                "priority": self._priority_overrides.get(r["key"], r["priority"]),
                # Reassigned epic: override both name AND key so grouping/filter/
                # the Epic-Key column stay in sync (fallback to originals).
                "epic_name": self._epic_overrides.get(r["key"], r["epic_name"]),
                "epic": name_to_key.get(
                    self._epic_overrides[r["key"]], r["epic"]
                ) if r["key"] in self._epic_overrides else r["epic"],
            }
            for r in rows
        ]
        if self.squad:    rows = [r for r in rows if r["squad_key"]  == self.squad]
        if self.type_:    rows = [r for r in rows if r["issue_type"] == self.type_]
        if self.status:   rows = [r for r in rows if r["status"]     == self.status]
        if self.priority: rows = [r for r in rows if r["priority"]   == self.priority]
        if self.severity: rows = [r for r in rows if r["severity"]   == self.severity]
        if self.sprint:   rows = [r for r in rows if r["sprint_name"]== self.sprint]
        if self.epic:     rows = [r for r in rows if r["epic"]       == self.epic]   # filter by KEY
        if self.okr:      rows = [r for r in rows if r["okr_tag"]    == self.okr]
        return rows

    @rx.var
    def filtered_count(self) -> int:
        return len(self.filtered)

    @rx.var
    def selected_issue(self) -> dict:
        if not self.selected_key:
            return {}
        is_dash = self.project_mode == "dash"
        rows = _ALL_DASH if is_dash else _ALL
        name_to_key = _NAME_TO_KEY_DASH if is_dash else _NAME_TO_KEY
        for r in rows:
            if r["key"] == self.selected_key:
                new_name = self._epic_overrides.get(r["key"], r["epic_name"])
                return {
                    **r,
                    "priority": self._priority_overrides.get(r["key"], r["priority"]),
                    "epic_name": new_name,
                    "epic": name_to_key.get(new_name, r["epic"]),
                }
        return {}

    @rx.var
    def selected_epic(self) -> dict:
        if not self.selected_epic_key:
            return {}
        rows = _ALL_DASH if self.project_mode == "dash" else _ALL
        epic_rows = [r for r in rows if r["epic"] == self.selected_epic_key]
        if not epic_rows:
            return {}
        done       = sum(1 for r in epic_rows if r["status"] == "Done")
        in_prog    = sum(1 for r in epic_rows if r["status"] == "In Progress")
        total      = len(epic_rows)
        sp_total   = sum(r["story_points"] for r in epic_rows)
        sp_done    = sum(r["story_points"] for r in epic_rows if r["status"] == "Done")
        squads     = ", ".join(sorted({r["squad_key"] for r in epic_rows}))
        unlocks_key = EPIC_UNLOCKS.get(self.selected_epic_key, "")
        return {
            "epic_key":   self.selected_epic_key,
            "epic_name":  epic_rows[0]["epic_name"],
            "epic_type":  EPIC_TYPES.get(self.selected_epic_key, ""),
            "unlocks":    unlocks_key.replace("DASH-EPIC-", "E") if unlocks_key else "",
            "unlocks_name": EPIC_NAMES.get(unlocks_key, unlocks_key) if unlocks_key else "",
            "total":      total,
            "done":       done,
            "in_progress": in_prog,
            "to_do":      total - done - in_prog,
            "done_pct":   round(100 * done / total) if total else 0,
            "sp_total":   sp_total,
            "sp_done":    sp_done,
            "squads":     squads,
        }

    @rx.var
    def selected_epic_children(self) -> list[dict]:
        if not self.selected_epic_key:
            return []
        rows = _ALL_DASH if self.project_mode == "dash" else _ALL
        return [
            {"key": r["key"], "summary": r["summary"],
             "status": r["status"], "issue_type": r["issue_type"]}
            for r in rows if r["epic"] == self.selected_epic_key
        ]

    @rx.var
    def epic_rows(self) -> list[dict]:
        by_epic: dict[str, list[dict]] = defaultdict(list)
        for r in self.filtered:
            by_epic[r["epic"]].append(r)
        result = []
        for epic_key, rows in sorted(by_epic.items(), key=lambda kv: _epic_sort_key(kv[0])):
            done  = sum(1 for r in rows if r["status"] == "Done")
            total = len(rows)
            sp_total = sum(r["story_points"] for r in rows)
            sp_done  = sum(r["story_points"] for r in rows if r["status"] == "Done")
            squads   = ", ".join(sorted({r["squad_key"] for r in rows}))
            unlocks_key = EPIC_UNLOCKS.get(epic_key, "")
            result.append({
                "epic":       epic_key,
                "epic_name":  rows[0]["epic_name"],
                "epic_type":  EPIC_TYPES.get(epic_key, ""),
                "unlocks":    unlocks_key.replace("DASH-EPIC-", "E") if unlocks_key else "",
                "okr_tag":    rows[0]["okr_tag"],
                "okr_title":  rows[0].get("okr_title", rows[0]["okr_tag"]),
                "squads":     squads,
                "total":      total,
                "done":       done,
                "done_pct":   round(100 * done / total) if total else 0,
                "sp_total":   sp_total,
                "sp_done":    sp_done,
                "in_progress": sum(1 for r in rows if r["status"] == "In Progress"),
                "bugs":       sum(1 for r in rows if r["issue_type"] == "bug"),
            })
        return result

    @rx.var
    def has_active_filters(self) -> bool:
        return bool(self.squad or self.type_ or self.status or self.priority
                    or self.severity or self.sprint or self.epic or self.okr)

    # ── reactive dropdown options ─────────────────────────────────────────────
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
        """Epic keys for filtering (value stored in self.epic)."""
        return _OPTS_DASH["epics"] if self.project_mode == "dash" else _OPTS["epics"]

    @rx.var
    def epic_filter_options(self) -> list[dict]:
        """Pairs {value: key, label: 'KEY · Name'} for the filter dropdown."""
        rows = _ALL_DASH if self.project_mode == "dash" else _ALL
        seen: dict[str, str] = {}
        for r in rows:
            if r["epic"] and r["epic"] not in seen:
                seen[r["epic"]] = r["epic_name"]

        # Числовая сортировка (E1…E14), не лексикографическая (E1, E10, E11, …, E2)
        def _num(key: str) -> int:
            tail = key.rsplit("-", 1)[-1]
            return int(tail) if tail.isdigit() else 0

        return [{"value": k, "label": f"{k} · {seen[k]}"} for k in sorted(seen, key=_num)]

    @rx.var
    def all_epic_names(self) -> list[str]:
        """Full list of epic names for the issue-popup epic select (unfiltered)."""
        rows = _ALL_DASH if self.project_mode == "dash" else _ALL
        return sorted({r["epic_name"] for r in rows if r["epic_name"]})

    @rx.var
    def okr_options(self) -> list[str]:
        return _OPTS_DASH["okrs"] if self.project_mode == "dash" else _OPTS["okrs"]
