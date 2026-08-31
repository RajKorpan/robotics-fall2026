from __future__ import annotations

import math


def summarize(samples: list[dict], started_at: float = 0.0) -> dict:
    valid = [row for row in samples if all(key in row for key in ("time", "x", "y", "yaw", "covariance_trace"))]
    if not valid: return {"sample_count": 0, "duration": 0.0, "convergence_time": None, "final_covariance": None, "settled_position_spread": None, "pose_jump": None}
    final = valid[-1]; settled = valid[max(0, len(valid) - 20):]
    convergence = next((row["time"] - started_at for row in valid if row["covariance_trace"] <= 0.5), None)
    cx = sum(row["x"] for row in settled) / len(settled); cy = sum(row["y"] for row in settled) / len(settled)
    spread = math.sqrt(sum((row["x"] - cx) ** 2 + (row["y"] - cy) ** 2 for row in settled) / len(settled))
    jumps = [math.hypot(b["x"] - a["x"], b["y"] - a["y"]) for a, b in zip(valid, valid[1:])]
    return {"sample_count": len(valid), "duration": final["time"] - valid[0]["time"], "convergence_time": convergence, "final_covariance": final["covariance_trace"], "settled_position_spread": spread, "pose_jump": max(jumps, default=0.0)}


def trial_passes(condition: str, metrics: dict) -> bool:
    common = metrics.get("sample_count", 0) >= 20 and metrics.get("duration", 0) >= 10 and metrics.get("final_covariance") is not None
    if not common: return False
    if condition == "good_initial_pose": return metrics["final_covariance"] <= 0.5 and metrics["settled_position_spread"] <= 0.20
    if condition == "incorrect_initial_pose": return metrics["pose_jump"] >= 0.15 or metrics["final_covariance"] >= 0.5
    if condition == "ambiguous_location": return common
    if condition == "degraded_sensor": return metrics.get("scan_retention", 1.0) <= 0.60 and metrics["sample_count"] >= 20
    return False
