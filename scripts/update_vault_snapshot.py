"""
Update vault_snapshot.json from the local Obsidian vault.
Run manually when the vault content changes significantly.

Usage:
    python scripts/update_vault_snapshot.py
"""

import json
from datetime import date
from pathlib import Path

import os

VAULT_PATH = Path(os.environ.get("OBSIDIAN_VAULT_PATH", r"C:\Users\guzel\Desktop\obsidian_notes\design_programming"))
SNAPSHOT_PATH = Path(__file__).parent.parent / "dash_app" / "data" / "vault_snapshot.json"


def main() -> None:
    if not VAULT_PATH.exists():
        print(f"Vault not found: {VAULT_PATH}")
        return

    total = sum(1 for _ in VAULT_PATH.rglob("*.md"))
    folders = sorted(
        [
            {"name": f.name, "count": sum(1 for _ in f.rglob("*.md"))}
            for f in VAULT_PATH.iterdir()
            if f.is_dir()
        ],
        key=lambda x: -x["count"],
    )

    snapshot = {
        "_comment": "Frozen snapshot of Obsidian vault — update by running scripts/update_vault_snapshot.py",
        "_snapshot_date": str(date.today()),
        "_vault_name": VAULT_PATH.name,
        "total_notes": total,
        "folders": folders,
    }

    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated: {total} notes, {len(folders)} folders → {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
