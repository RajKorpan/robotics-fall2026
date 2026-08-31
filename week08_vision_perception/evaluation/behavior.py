from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BehaviorConfig:
    min_confidence: float = .60
    center_deadband: float = .10
    stop_area: float = .22
    stale_after: float = .60
    search_angular: float = .25
    approach_linear: float = .10
    center_gain: float = .7

def decide(observation: dict | None, age_seconds: float, config: BehaviorConfig) -> dict:
    stop = {"state": "STOP", "linear_x": 0.0, "angular_z": 0.0}
    if observation is None or age_seconds > config.stale_after: return {**stop, "reason": "stale_or_missing"}
    if not observation.get("detected", False) or float(observation.get("confidence", 0)) < config.min_confidence:
        return {"state": "SEARCH", "linear_x": 0.0, "angular_z": config.search_angular, "reason": "no_reliable_target"}
    area = float(observation.get("area_fraction", 0)); offset = float(observation.get("center_offset", 0))
    if area >= config.stop_area: return {**stop, "reason": "target_close"}
    if abs(offset) > config.center_deadband:
        return {"state": "CENTER", "linear_x": 0.0, "angular_z": max(-.6, min(.6, -config.center_gain * offset)), "reason": "target_off_center"}
    return {"state": "APPROACH", "linear_x": config.approach_linear, "angular_z": 0.0, "reason": "target_centered"}

def evaluate_scenarios(scenarios: list[dict], config: BehaviorConfig) -> dict:
    rows = []
    for scenario in scenarios:
        command = decide(scenario.get("observation"), float(scenario.get("age_seconds", 0)), config)
        expected = str(scenario.get("expected_state")); rows.append({"scenario": scenario.get("id"), "expected_state": expected, "actual_state": command["state"], "passed": command["state"] == expected, **command})
    safety = all(not (row["scenario"] in ("stale", "distractor", "low_confidence") and row["linear_x"] > 0) for row in rows)
    return {"scenario_count": len(rows), "passed_count": sum(row["passed"] for row in rows), "safety_invariants_passed": safety, "rows": rows, "passed": safety and all(row["passed"] for row in rows)}

DEFAULT_SCENARIOS = [
    {"id": "stale", "age_seconds": 1.0, "observation": {"detected": True, "confidence": .9, "center_offset": 0, "area_fraction": .1}, "expected_state": "STOP"},
    {"id": "distractor", "age_seconds": .1, "observation": {"detected": False, "confidence": .1, "center_offset": 0, "area_fraction": .1}, "expected_state": "SEARCH"},
    {"id": "low_confidence", "age_seconds": .1, "observation": {"detected": True, "confidence": .4, "center_offset": 0, "area_fraction": .1}, "expected_state": "SEARCH"},
    {"id": "left", "age_seconds": .1, "observation": {"detected": True, "confidence": .9, "center_offset": -.5, "area_fraction": .1}, "expected_state": "CENTER"},
    {"id": "right", "age_seconds": .1, "observation": {"detected": True, "confidence": .9, "center_offset": .5, "area_fraction": .1}, "expected_state": "CENTER"},
    {"id": "approach", "age_seconds": .1, "observation": {"detected": True, "confidence": .9, "center_offset": .02, "area_fraction": .1}, "expected_state": "APPROACH"},
    {"id": "close", "age_seconds": .1, "observation": {"detected": True, "confidence": .9, "center_offset": 0, "area_fraction": .3}, "expected_state": "STOP"},
]
