from __future__ import annotations

import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from lab.autosave import submission_root


def assigned_pattern(course_id: str) -> str:
    options = ("rounded_rectangle", "l_path", "alternating_arcs")
    digest = hashlib.sha256(course_id.strip().lower().encode("utf-8")).digest()
    return options[digest[0] % len(options)]


def lock_original(course_id: str, specification: str, prompt: str, output: str) -> dict[str, str]:
    target = submission_root() / "mission_3" / "ai"
    target.mkdir(parents=True, exist_ok=True)
    if (target / "original_output.txt").exists():
        raise FileExistsError("The original AI output has already been locked")
    metadata = {
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "pattern": assigned_pattern(course_id),
        "specification_sha256": hashlib.sha256(specification.encode("utf-8")).hexdigest(),
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "output_sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
    }
    (target / "specification.txt").write_text(specification, encoding="utf-8")
    (target / "original_prompt.txt").write_text(prompt, encoding="utf-8")
    (target / "original_output.txt").write_text(output, encoding="utf-8")
    (target / "lock.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def load_lock() -> dict[str, str]:
    directory = submission_root() / "mission_3" / "ai"
    path = directory / "lock.json"
    if not path.exists():
        return {}
    metadata = json.loads(path.read_text(encoding="utf-8"))
    files = {
        "specification_sha256": directory / "specification.txt",
        "prompt_sha256": directory / "original_prompt.txt",
        "output_sha256": directory / "original_output.txt",
    }
    metadata["integrity_valid"] = all(
        file.exists()
        and hashlib.sha256(file.read_text(encoding="utf-8").encode("utf-8")).hexdigest() == metadata.get(key)
        for key, file in files.items()
    )
    return metadata


def write_diff(final_source: Path) -> Path:
    ai_dir = submission_root() / "mission_3" / "ai"
    original_path = ai_dir / "original_output.txt"
    if not original_path.exists():
        raise FileNotFoundError("Lock the original AI output first")
    original = original_path.read_text(encoding="utf-8").splitlines(keepends=True)
    final = final_source.read_text(encoding="utf-8").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(original, final, fromfile="original_ai_output", tofile="final_pattern.py"))
    path = ai_dir / "ai_to_final.diff"
    path.write_text(diff or "# No textual difference detected.\n", encoding="utf-8")
    return path
