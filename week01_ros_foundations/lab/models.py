from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RequirementResult:
    id: str
    label: str
    passed: bool
    actual: Any
    expected: str


@dataclass(frozen=True)
class MissionCheck:
    passed: bool
    summary: str
    requirements: tuple[RequirementResult, ...]


@dataclass(frozen=True)
class ReflectionPrompt:
    id: str
    label: str
    help: str = ""


def check_from_requirements(summary: str, requirements: list[RequirementResult]) -> MissionCheck:
    return MissionCheck(
        passed=all(requirement.passed for requirement in requirements),
        summary=summary,
        requirements=tuple(requirements),
    )

