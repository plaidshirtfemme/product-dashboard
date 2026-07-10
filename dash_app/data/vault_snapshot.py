"""Loads frozen vault statistics from vault_snapshot.json."""

import json
from pathlib import Path

_SNAPSHOT_FILE = Path(__file__).parent / "vault_snapshot.json"

_data: dict = json.loads(_SNAPSHOT_FILE.read_text(encoding="utf-8"))

VAULT_NAME: str = _data["_vault_name"]
SNAPSHOT_DATE: str = _data["_snapshot_date"]
TOTAL_NOTES: int = _data["total_notes"]
FOLDER_COUNTS: list[tuple[str, int]] = [
    (f["name"], f["count"]) for f in _data["folders"]
]
