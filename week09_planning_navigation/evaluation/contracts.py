from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evaluation.metrics import social_summary, summarize_plans, summarize_trials


@dataclass(frozen=True)
class Requirement:
    label: str
    passed: bool
    actual: Any
    expected: str


def plan_requirements(evidence: dict) -> tuple[Requirement, ...]:
    rows = evidence.get("rows", [])
    ids = {row.get("goal_id") for row in rows}
    metrics = summarize_plans(rows)
    required = {"open_short", "detour", "narrow", "occupied_goal", "blocked_goal"}
    return (
        Requirement("All five standard goals attempted", required <= ids, sorted(ids), str(sorted(required))),
        Requirement("At least three valid paths", metrics.get("planned", 0) >= 3, metrics.get("planned", 0), ">= 3"),
        Requirement("Both impossible goals rejected", metrics.get("correctly_rejected", 0) >= 2, metrics.get("correctly_rejected", 0), ">= 2"),
        Requirement("Each successful path has geometry", all(r.get("waypoint_count", 0) > 1 and r.get("path_length_m", 0) > 0 for r in rows if r.get("status") == "succeeded"), "checked", "waypoints > 1 and length > 0"),
        Requirement("Clearance measured for each valid path", all(r.get("minimum_clearance_m") is not None and r.get("minimum_clearance_m") >= 0 for r in rows if r.get("status") == "succeeded"), "checked", "non-negative measurement for every successful path"),
    )


def navigation_requirements(evidence: dict) -> tuple[Requirement, ...]:
    rows = evidence.get("rows", [])
    metrics = summarize_trials(rows)
    conditions = {r.get("condition") for r in rows}
    return (
        Requirement("Five navigation trials", len(rows) >= 5, len(rows), ">= 5"),
        Requirement("Required conditions represented", sum(r.get("condition") == "open" for r in rows) >= 2 and sum(r.get("condition") == "unexpected_obstacle" for r in rows) >= 2 and "narrow" in conditions, sorted(conditions), ">=2 open, >=2 unexpected_obstacle, >=1 narrow"),
        Requirement("At least four successful trials", metrics.get("successes", 0) >= 4, metrics.get("successes", 0), ">= 4"),
        Requirement("No collision events", metrics.get("collision_events", 0) == 0, metrics.get("collision_events", 0), "0"),
    )


def human_aware_requirements(evidence: dict) -> tuple[Requirement, ...]:
    baseline = evidence.get("baseline", {})
    redesign = evidence.get("redesign", {})
    b = baseline.get("metrics") or social_summary(baseline)
    r = redesign.get("metrics") or social_summary(redesign)
    clearance = float(evidence.get("policy", {}).get("required_clearance_m", 0.75))
    speed = float(evidence.get("policy", {}).get("maximum_nearby_speed_mps", 0.12))
    return (
        Requirement("Same scenario and goal", bool(baseline.get("scenario_id") and baseline.get("goal_id")) and baseline.get("scenario_id") == redesign.get("scenario_id") and baseline.get("goal_id") == redesign.get("goal_id"), (baseline.get("scenario_id"), redesign.get("scenario_id")), "matching non-empty identifiers"),
        Requirement("Baseline exposes the design problem", b.get("minimum_person_clearance_m") is not None and b["minimum_person_clearance_m"] < clearance, b.get("minimum_person_clearance_m"), f"< {clearance} m"),
        Requirement("Redesign completes the goal", redesign.get("status") == "succeeded", redesign.get("status"), "succeeded"),
        Requirement("Redesign respects personal space", r.get("minimum_person_clearance_m") is not None and r["minimum_person_clearance_m"] >= clearance, r.get("minimum_person_clearance_m"), f">= {clearance} m"),
        Requirement("Redesign limits nearby speed", r.get("maximum_speed_near_people_mps") is not None and r["maximum_speed_near_people_mps"] <= speed, r.get("maximum_speed_near_people_mps"), f"<= {speed} m/s"),
        Requirement("At least two engineering changes", len(evidence.get("parameter_changes", [])) >= 2, len(evidence.get("parameter_changes", [])), ">= 2"),
    )
