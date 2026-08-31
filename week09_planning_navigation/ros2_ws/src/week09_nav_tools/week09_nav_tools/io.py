from __future__ import annotations

import json
from pathlib import Path


def append_row(path: str, row: dict) -> None:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    document = {"schema_version": 1, "rows": []}
    if target.exists():
        document = json.loads(target.read_text(encoding="utf-8"))
    document.setdefault("rows", []).append(row)
    target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

