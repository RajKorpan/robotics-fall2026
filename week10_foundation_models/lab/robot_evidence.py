"""Replayable directional-run evidence and three-examples-plus-own-prompt checks."""
from lab.evidence import root, read_json, write_json
from lab.local_jobs import record
from lab.local_config import MODEL_CONFIG
from simulation.robot_room import SCENARIOS, ROBOT_SYSTEM, initial_state, contract, summarize, model_message


def simulation_path(job_id):
    return root() / "mission_3" / "attempts" / (job_id + ".simulation.json")


def compatible(row):
    if not (row.get("task") == "robot" and row.get("kind") == "language" and row.get("case") in (*SCENARIOS, "custom")
            and row.get("model") == MODEL_CONFIG["language"]["id"] and row.get("model_revision") == MODEL_CONFIG["language"]["revision"]
            and row.get("system_prompt") == ROBOT_SYSTEM and row.get("simulator_contract") == contract()
            and row.get("output_constraint") == "directional rollout v4" and row.get("live_inference") is True
            and row.get("robot_state") == initial_state()):
        return False
    for step in row.get("steps", []):
        model = step.get("model", {})
        if not (model.get("live_inference") is True and model.get("model") == row["model"]
                and model.get("model_revision") == row["model_revision"] and model.get("prompt") == row["prompt"]
                and model.get("system_prompt") == ROBOT_SYSTEM and model.get("simulator_contract") == contract()
                and model.get("output_constraint") == "one supplied robot command"
                and model.get("model_input") == model_message(row["prompt"], model.get("robot_state", {}))):
            return False
    try:
        summarize(row)
    except (ValueError, KeyError, TypeError):
        return False
    return True


def checked_rows(state):
    controls = state.get("controls", {})
    ids = state.get("control_robot_runs", controls.get("control_robot_runs", []))
    rows = []
    for job_id in ids:
        model = record("language", job_id, "mission_3")
        if model and compatible(model):
            receipt = summarize(model)
            if not simulation_path(job_id).exists():
                write_json(simulation_path(job_id), receipt)
            if read_json(simulation_path(job_id), {}) == receipt:
                rows.append({"record": model, "simulation": receipt})
    return rows


def complete(rows, verify_files=False):
    valid = []
    for row in rows:
        model = row.get("record", {})
        if not compatible(model) or row.get("simulation") != summarize(model):
            return False
        if verify_files and (record("language", model["job_id"], "mission_3") != model or read_json(simulation_path(model["job_id"]), {}) != row["simulation"]):
            return False
        valid.append(model)
    baseline = {r["job_id"]: r for r in valid if r.get("phase") == "baseline" and r["case"] in SCENARIOS and r["prompt"] == SCENARIOS[r["case"]]["request"]}
    cases = set(SCENARIOS)
    own = [r for r in valid if r.get("phase") == "custom" and r["case"] == "custom"
           and r["prompt"] not in [s["request"] for s in SCENARIOS.values()]
           and {baseline[i]["case"] for i in r.get("comparison_ids", []) if i in baseline} >= cases]
    return {r["case"] for r in baseline.values()} >= cases and bool(own)
