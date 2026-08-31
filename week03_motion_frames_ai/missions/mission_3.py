from __future__ import annotations

from pathlib import Path
from typing import Any

from lab.models import RequirementResult, make_check


REFLECTIONS = ("assumptions", "problems", "modifications", "test_argument", "remaining_limits", "ai_disclosure")


def evaluate(ai_result: dict[str, Any], lock: dict[str, str], responses: dict[str, Any], source_root: Path):
    source_files = (
        source_root / "week03_pattern" / "pattern.py",
        source_root / "week03_pattern" / "pattern_node.py",
        source_root / "test" / "test_pattern.py",
    )
    source_complete = all(path.exists() and path.stat().st_size > 150 for path in source_files)
    tests = bool(ai_result.get("unit_tests_passed"))
    integration = bool(ai_result.get("integration_passed"))
    bounded = bool(ai_result.get("commands_bounded")) and bool(ai_result.get("final_stop_verified"))
    pattern_match = ai_result.get("pattern") == lock.get("pattern") and bool(lock)
    original_preserved = bool(
        lock.get("output_sha256")
        and lock.get("prompt_sha256")
        and lock.get("integrity_valid")
    )
    changed = bool(ai_result.get("source_differs_from_original"))
    test_count = int(ai_result.get("test_count", 0))
    reflections = all(len(str(responses.get(f"mission_3.{key}", "")).strip()) >= 60 for key in REFLECTIONS)
    requirements = [
        RequirementResult("original", "Original prompt and AI output preserved", original_preserved, lock.get("locked_at", "missing"), "immutable record"),
        RequirementResult("source", "Final source and tests present", source_complete, source_complete, "true"),
        RequirementResult("pattern", "Assigned pattern implemented", pattern_match and integration, ai_result.get("pattern", "missing"), lock.get("pattern", "assigned pattern")),
        RequirementResult("tests", "Meaningful automated tests pass", tests and test_count >= 6, test_count, ">= 6 passing"),
        RequirementResult("safety", "Commands bounded and final stop verified", bounded, bounded, "true"),
        RequirementResult("modified", "Final source differs from original output", changed, changed, "true"),
        RequirementResult("reflection", "AI review and correctness argument completed", reflections, "complete" if reflections else "incomplete", "six substantive responses"),
    ]
    return make_check("You used AI as a reviewed and tested development aid rather than an authority.", requirements)
