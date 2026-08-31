from __future__ import annotations
from statistics import mean

REQUIRED_SCENARIOS = {"clear_request", "no_response", "correction", "ambiguous_request", "alternate_modality"}


def validate_trial(row):
    required = {"scenario_id", "task_success", "intent_understood", "listening_state_clear", "recovered_without_facilitator", "predictability_rating", "feedback_rating", "access_barrier", "safety_stop", "completion_time_s", "note"}
    return required <= set(row) and 1 <= int(row["predictability_rating"]) <= 5 and 1 <= int(row["feedback_rating"]) <= 5 and float(row["completion_time_s"]) >= 0


def summarize(document):
    rows = document.get("trials", []); n = len(rows)
    return {
        "trial_count": n,
        "scenario_coverage": len({r.get("scenario_id") for r in rows} & REQUIRED_SCENARIOS),
        "valid_trials": sum(validate_trial(r) for r in rows),
        "task_success_rate": round(sum(bool(r.get("task_success")) for r in rows) / n, 3) if n else 0,
        "intent_comprehension_rate": round(sum(bool(r.get("intent_understood")) for r in rows) / n, 3) if n else 0,
        "listening_clarity_rate": round(sum(bool(r.get("listening_state_clear")) for r in rows) / n, 3) if n else 0,
        "recovery_rate": round(sum(bool(r.get("recovered_without_facilitator")) for r in rows) / n, 3) if n else 0,
        "mean_predictability": round(mean(float(r.get("predictability_rating", 0)) for r in rows), 2) if n else 0,
        "mean_feedback_clarity": round(mean(float(r.get("feedback_rating", 0)) for r in rows), 2) if n else 0,
        "access_barriers": sum(bool(r.get("access_barrier")) for r in rows),
        "safety_stops": sum(bool(r.get("safety_stop")) for r in rows),
        "mean_completion_time_s": round(mean(float(r.get("completion_time_s", 0)) for r in rows), 2) if n else 0,
    }


def matched_comparison(baseline, redesign):
    b, r = summarize(baseline), summarize(redesign)
    pairs = set(x.get("scenario_id") for x in baseline.get("trials", [])) & set(x.get("scenario_id") for x in redesign.get("trials", []))
    targeted = ("task_success_rate", "intent_comprehension_rate", "listening_clarity_rate", "recovery_rate", "mean_predictability", "mean_feedback_clarity")
    improved = [key for key in targeted if r[key] > b[key]]
    return {"baseline": b, "redesign": r, "matched_scenarios": len(pairs), "improved_metrics": improved, "participant_match": bool(baseline.get("participant_code")) and baseline.get("participant_code") == redesign.get("participant_code")}

