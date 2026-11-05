"""Keep widget edits, saved experiment evidence and downstream completion distinct."""
import hashlib
import json

RESPONSE_KEYS = {
    "mission_1": ("m1_analysis",),
    "mission_2": ("m2_analysis",),
    "mission_3": ("m3_analysis",),
}
CONTROL_KEYS = {
    "mission_1": ("control_live_language_runs", "control_live_language_custom_prompt"),
    "mission_2": ("control_live_vision_runs", "control_live_vision_custom_prompt"),
    "mission_3": ("control_robot_runs", "control_robot_custom_prompt"),
}


def capture_inputs(state):
    responses = dict(state.get("responses", {}))
    for key in state.get("response_widgets") or []:
        if key in state:
            responses[key] = state[key]
    if "field.final.course_reflection" in state:
        responses["final.course_reflection"] = state["field.final.course_reflection"]
    state["responses"] = responses
    controls = dict(state.get("controls", {}))
    for key in list(state):
        if key.startswith(("control_", "outcome_")):
            controls[key] = state[key]
    state["controls"] = controls
    student = dict(state.get("student", {}))
    for key, name in (("identity_name", "name"), ("identity_email", "email")):
        if key in state:
            student[name] = state[key]
    state["student"] = student


def signature(mission, state):
    responses = state.get("responses", {})
    controls = state.get("controls", {})
    payload = {
        "responses": {key: responses.get(key, "") for key in RESPONSE_KEYS[mission]},
        "controls": {key: state.get(key, controls.get(key)) for key in CONTROL_KEYS[mission]},
    }
    if mission in ("mission_1", "mission_2"):
        from lab.local_config import contract_signature
        payload["live_contract"] = contract_signature("language" if mission == "mission_1" else "vision")
    else:
        from simulation.robot_room import contract
        from lab.local_config import MODEL_CONFIG
        payload["live_contract"] = {"simulator": contract(), "model": MODEL_CONFIG["language"]}
        from lab.robot_evidence import checked_rows
        payload["checked_actions"] = checked_rows(state)
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def current(mission, state):
    from lab.evidence import saved_run
    saved = saved_run(mission)
    if not saved or saved.get("extra", {}).get("draft_signature") != signature(mission, state):
        return False
    previous = {"mission_2": "mission_1", "mission_3": "mission_2"}.get(mission)
    if previous:
        return current(previous, state) and saved.get("extra", {}).get("upstream_run") == saved_run(previous).get("run_id")
    return True


def checkpoint(mission, state, settings, rows, responses, extra=None):
    from lab.evidence import save_run
    capture_inputs(state)
    metadata = dict(extra or {})
    metadata["draft_signature"] = signature(mission, state)
    previous = {"mission_2": "mission_1", "mission_3": "mission_2"}.get(mission)
    if previous:
        from lab.evidence import saved_run
        metadata["upstream_run"] = saved_run(previous).get("run_id")
    return save_run(mission, settings, rows, responses, metadata)
