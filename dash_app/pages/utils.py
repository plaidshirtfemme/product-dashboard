"""Shared page-level utilities — pure functions, no Reflex imports."""


def jira_status_key(status: str) -> str:
    """Map Jira status string → internal key used by status_badge()."""
    return {
        "Done":        "done",
        "In Progress": "in_progress",
        "In Review":   "in_review",
        "To Do":       "not_started",
    }.get(status, "backlog")
