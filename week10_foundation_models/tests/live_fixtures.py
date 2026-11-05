"""Explicit fake records for UI/evidence tests only. Never used by the guide."""
import hashlib
import copy
import uuid
from lab.evidence import root, atomic, write_json
from lab.local_config import MODEL_CONFIG, LANGUAGE_TASKS, LANGUAGE_SYSTEM, VISION_TASKS, VISION_PREPROCESSING, scene_path

ANSWER = "The specific outputs show a difference between the requested task and the claims supported by the supplied robot capabilities or visible image evidence."


def fixture_runs(kind):
    cases = LANGUAGE_TASKS if kind == "language" else VISION_TASKS
    rows = []
    for case in cases:
        rows.append({"job_id": "fixture-" + kind + "-" + case, "kind": kind, "case": case,
                     "prompt": cases[case]["prompt"], "phase": "baseline", "parent_id": None,
                     "model": MODEL_CONFIG[kind]["id"], "model_revision": MODEL_CONFIG[kind]["revision"],
                     "system_prompt": LANGUAGE_SYSTEM if kind == "language" else "", "image_preprocessing": VISION_PREPROCESSING if kind == "vision" else None,
                     "output": "Explicit UI test fixture answer, not actual inference.", "live_inference": True,
                     "generated_tokens": 10, "generation_seconds": 1.2, "truncated": False})
    rows.append({**rows[0], "job_id": "fixture-" + kind + "-revision", "case": "custom", "prompt": "A changed test prompt", "phase": "custom", "comparison_ids": [r["job_id"] for r in rows]})
    if kind == "vision":
        for row in rows:
            row["image_sha256"] = hashlib.sha256(scene_path(row["case"]).read_bytes()).hexdigest()
    return rows


def store_runs(state, kind):
    mission = "mission_1" if kind == "language" else "mission_2"
    rows = fixture_runs(kind)
    for row in rows:
        if kind == "vision":
            photo = scene_path(row["case"]).read_bytes()
            row["image_sha256"] = hashlib.sha256(photo).hexdigest()
            atomic(root() / mission / "attempts" / (row["job_id"] + ".jpg"), photo)
        write_json(root() / mission / "attempts" / (row["job_id"] + ".result.json"), {"status": "complete", "record": row})
    key = "control_live_" + kind + "_runs"
    state[key] = [r["job_id"] for r in rows]
    state["controls"][key] = state[key]
    state["control_live_" + kind + "_custom_prompt"] = rows[-1]["prompt"]
    return rows


def robot_model(case, output, state=None, phase="baseline", parent=None, prompt=None):
    from simulation.robot_room import ROBOT_SYSTEM, SCENARIOS, initial_state, contract, model_message
    before = copy.deepcopy(state if state is not None else initial_state())
    request = prompt or SCENARIOS[case]["request"]
    return {"job_id": uuid.uuid4().hex, "kind": "language", "task": "robot", "case": case, "phase": phase,
            "parent_id": parent, "prompt": request, "robot_state": before, "simulator_contract": contract(),
            "model": MODEL_CONFIG["language"]["id"], "model_revision": MODEL_CONFIG["language"]["revision"],
            "system_prompt": ROBOT_SYSTEM, "model_input": model_message(request, before),
            "output_constraint": "one supplied robot command",
            "output": output, "live_inference": True, "generated_tokens": 4, "generation_seconds": 1.1}


def robot_rollout(case, actions=("STOP",), prompt=None, comparison_ids=None):
    from simulation.robot_room import initial_state, evaluate, SCENARIOS, MAX_STEPS
    state = initial_state()
    steps = []
    prompt = prompt or ("My custom test prompt" if case == "custom" else SCENARIOS[case]["request"])
    actions = list(actions)
    actions += ["STOP"] * max(0, MAX_STEPS-len(actions))
    for action in actions:
        model = robot_model(case, action, state, prompt=prompt)
        result = evaluate(model, state)
        steps.append({"model":model, "simulation":result})
        state = result["after"]
    return {**steps[0]["model"], "job_id":uuid.uuid4().hex, "robot_state":initial_state(), "steps":steps,
            "phase":"custom" if case == "custom" else "baseline", "comparison_ids":comparison_ids or [],
            "output_constraint":"directional rollout v4", "output":" â†’ ".join(actions)}


def store_robot_runs(state):
    from simulation.robot_room import SCENARIOS
    from lab.robot_evidence import checked_rows
    models = [robot_rollout(case) for case in SCENARIOS]
    models.append(robot_rollout("custom", comparison_ids=[r["job_id"] for r in models]))
    for model in models:
        write_json(root() / "mission_3" / "attempts" / (model["job_id"] + ".result.json"), {"status":"complete", "record":model})
    state["control_robot_runs"] = [r["job_id"] for r in models]
    state["controls"]["control_robot_runs"] = state["control_robot_runs"]
    state["control_robot_custom_prompt"] = models[-1]["prompt"]
    return checked_rows(state)
