from lab.models import RunResult
from simulation.common import run_identity
from simulation.scenarios import load_bank

ALLOWED_ACTIONS = {"move_to", "pick", "place", "ask_identity", "hand_over", "return_to", "report_complete", "inspect", "speak", "stop", "request_help"}


def action_name(step): return step.split("(", 1)[0]


def run_language_suite(settings):
    rows = []
    for case in load_bank("language_plans.json"):
        unavailable = sorted({action_name(s) for s in case["model_plan"]} - ALLOWED_ACTIONS)
        rows.append({**case, "plan": " → ".join(case["model_plan"]), "unavailable_actions": ", ".join(unavailable), "issue_count": len(case["issues"])})
    run_id, timestamp = run_identity("mission_1", settings)
    metrics = {"requests_tested": len(rows), "executable_plans": sum(r["executable"] for r in rows), "ungrounded_plans": sum(not r["grounded"] for r in rows), "hallucinated_capability_cases": sum(bool(r["unavailable_actions"]) for r in rows), "missing_prerequisite_cases": sum(any("prerequisite" in i or "authorization" in i for i in r["issues"]) for r in rows)}
    traces = {k: [r[k] if not isinstance(r[k], (dict, list)) else str(r[k]) for r in rows] for k in ("id", "request", "plan", "executable", "grounded", "unavailable_actions", "issue_count")}
    return RunResult(run_id, "mission_1", timestamp, settings, metrics, traces)

