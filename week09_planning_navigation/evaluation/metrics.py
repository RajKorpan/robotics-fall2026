from __future__ import annotations

from math import hypot
from statistics import mean
from typing import Iterable


def path_length(points: Iterable[dict]) -> float:
    points = list(points)
    return sum(hypot(b["x"] - a["x"], b["y"] - a["y"]) for a, b in zip(points, points[1:]))


def summarize_plans(rows: list[dict]) -> dict:
    attempted = len(rows)
    successes = [row for row in rows if row.get("status") == "succeeded"]
    correctly_rejected = [row for row in rows if not row.get("expected_reachable", True) and row.get("status") != "succeeded"]
    return {
        "attempted": attempted,
        "planned": len(successes),
        "correctly_rejected": len(correctly_rejected),
        "mean_planning_time_s": round(mean(float(r.get("planning_time_s", 0)) for r in successes), 3) if successes else None,
        "mean_path_length_m": round(mean(float(r.get("path_length_m", 0)) for r in successes), 3) if successes else None,
        "minimum_clearance_m": min((float(r["minimum_clearance_m"]) for r in successes if r.get("minimum_clearance_m") is not None), default=None),
    }


def summarize_trials(rows: list[dict]) -> dict:
    successes = [row for row in rows if row.get("status") == "succeeded"]
    return {
        "trials": len(rows),
        "successes": len(successes),
        "success_rate": round(len(successes) / len(rows), 3) if rows else 0.0,
        "mean_completion_time_s": round(mean(float(r.get("completion_time_s", 0)) for r in successes), 3) if successes else None,
        "mean_path_length_m": round(mean(float(r.get("path_length_m", 0)) for r in successes), 3) if successes else None,
        "collision_events": sum(int(r.get("collision_events", 0)) for r in rows),
        "near_miss_events": sum(int(r.get("near_miss_events", 0)) for r in rows),
        "recovery_count": sum(int(r.get("recovery_count", 0)) for r in rows),
        "minimum_scan_range_m": min((float(r["minimum_scan_range_m"]) for r in rows if r.get("minimum_scan_range_m") is not None), default=None),
    }


def social_summary(run: dict) -> dict:
    samples = run.get("samples", [])
    if not samples:
        return {"minimum_person_clearance_m": None, "maximum_speed_near_people_mps": None, "time_inside_personal_space_s": None}
    near = [s for s in samples if s.get("nearest_person_m") is not None and s["nearest_person_m"] <= run.get("monitor_radius_m", 1.2)]
    inside = [s for s in samples if s.get("nearest_person_m") is not None and s["nearest_person_m"] < run["required_clearance_m"]]
    dt = float(run.get("sample_period_s", 0.1))
    return {
        "minimum_person_clearance_m": round(min(float(s["nearest_person_m"]) for s in samples), 3),
        "maximum_speed_near_people_mps": round(max((abs(float(s.get("speed_mps", 0))) for s in near), default=0.0), 3),
        "time_inside_personal_space_s": round(len(inside) * dt, 3),
    }
