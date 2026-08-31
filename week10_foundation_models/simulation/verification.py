from lab.models import RunResult
from simulation.common import run_identity
from simulation.scenarios import load_bank

SAFE_ACTIONS = {"inspect", "pick", "move_to", "place", "speak", "stop", "request_help"}


def verify(case, settings):
    if settings["block_unsafe_actions"] and case["action"] not in SAFE_ACTIONS: return "REJECT", "action outside allowlist"
    if settings["check_prerequisites"] and not case["prerequisites_met"]: return "REJECT", "prerequisite or constraint failed"
    if case["confidence"] < settings["confidence_threshold"]: return "ABSTAIN", settings["fallback"]
    if settings["validate_grounding"] and not case["known"]: return "CONFIRM", "unknown or ambiguous argument"
    if settings["confirm_consequential"] and case["risk"] == "high": return "CONFIRM", "human authorization required"
    return "EXECUTE", "validated"


def run_verification_suite(settings):
    rows = []
    for case in load_bank("safety_cases.json"):
        verdict, reason = verify(case, settings); rows.append({**case, "verdict": verdict, "reason": reason, "correct": verdict == case["expected"]})
    run_id, timestamp = run_identity("mission_3", settings)
    metrics = {"cases_tested": len(rows), "correct_dispositions": sum(r["correct"] for r in rows), "unsafe_executions": sum(r["verdict"] == "EXECUTE" and r["expected"] in ("REJECT", "ABSTAIN") for r in rows), "human_confirmations": sum(r["verdict"] == "CONFIRM" for r in rows), "abstentions": sum(r["verdict"] == "ABSTAIN" for r in rows), "rejections": sum(r["verdict"] == "REJECT" for r in rows), "low_risk_executions": sum(r["verdict"] == "EXECUTE" and r["risk"] == "low" for r in rows)}
    traces = {k: [r[k] if not isinstance(r[k], dict) else str(r[k]) for r in rows] for k in ("id", "request", "action", "confidence", "risk", "expected", "verdict", "reason", "correct")}
    return RunResult(run_id, "mission_3", timestamp, settings, metrics, traces)

