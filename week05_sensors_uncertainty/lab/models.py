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
    requirements: tuple[RequirementResult,...]

def make_check(summary:str,requirements:list[RequirementResult])->MissionCheck:
    return MissionCheck(all(item.passed for item in requirements),summary,tuple(requirements))

