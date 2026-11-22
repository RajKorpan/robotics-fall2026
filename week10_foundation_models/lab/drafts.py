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

STAGE_RESPONSES = {**RESPONSE_KEYS, "final_submission": ("final_synthesis", "final.course_reflection")}


def visible_response(state, key):
    stage = state.get("stage")
    return stage is None or key in STAGE_RESPONSES.get(stage, ())


def capture_inputs(state):
    responses = dict(state.get("responses", {}))
    for key in state.get("response_widgets") or []:
        if visible_response(state, key) and key in state:
            responses[key] = state[key]
    # New response widgets have their own lifecycle. Hidden widgets never
    # overwrite durable answers belonging to another page.
    for widget, key in state.get("response_widget_map", {}).items():
        if visible_response(state, key) and widget in state:
            responses[key] = state[widget]
    if state.get("stage") in (None, "final_submission") and "field.final.course_reflection" in state:
        responses["final.course_reflection"] = state["field.final.course_reflection"]
    state["responses"] = responses
    controls = dict(state.get("controls", {}))
    stage = state.get("stage")
    prefixes = {"mission_1":("control_live_language_",), "mission_2":("control_live_vision_",),
                "mission_3":("control_robot_",), "guided":("control_", "outcome_")}.get(stage,())
    for key in list(state):
        hidden_mission_control = stage == "guided" and key.startswith(("control_live_", "control_robot_"))
        if key.startswith(("control_", "outcome_")) and not hidden_mission_control and (stage is None or key.startswith(prefixes)):
            controls[key] = state[key]
    state["controls"] = controls
    student = dict(state.get("student", {}))
    for key, name in (("identity_name", "name"), ("identity_email", "email")):
        if key in state:
            student[name] = state[key]
    state["student"] = student


def signature_payload(mission, state):
    responses = state.get("responses", {})
    controls = state.get("controls", {})
    payload = {
        "responses": {key: responses.get(key, "") for key in RESPONSE_KEYS[mission]},
        "controls": {key: controls.get(key, state.get(key)) for key in CONTROL_KEYS[mission]},
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
    return payload


def signature(mission, state):
    return hashlib.sha256(json.dumps(signature_payload(mission,state), sort_keys=True).encode()).hexdigest()


def current(mission, state):
    from lab.evidence import saved_run
    saved = saved_run(mission)
    if not saved or saved.get("extra", {}).get("draft_signature") != signature(mission, state):
        return False
    previous = {"mission_2": "mission_1", "mission_3": "mission_2"}.get(mission)
    if previous:
        return current(previous, state) and saved.get("extra", {}).get("upstream_run") == saved_run(previous).get("run_id")
    return True


def stale_reason(mission, state):
    from lab.evidence import saved_run
    saved = saved_run(mission)
    if not saved:
        return "No checked experiment has been saved yet."
    snapshot = saved.get("extra", {}).get("draft_inputs")
    if snapshot:
        now = signature_payload(mission,state)
        if snapshot["responses"] != now["responses"]:
            return "The current written answer differs from the checked answer. Review it and save the mission again."
        if snapshot["controls"] != now["controls"]:
            return "The selected runs or custom prompt differ from the checked experiment. Restore your selection or save the current experiment."
        if snapshot.get("live_contract") != now.get("live_contract"):
            return "The experiment specification changed after this evidence was saved. Review the current instructions and retained results."
    previous = {"mission_2":"mission_1","mission_3":"mission_2"}.get(mission)
    if previous and not current(previous,state):
        return previous.replace("_"," ").title()+" needs review first. "+stale_reason(previous,state)
    return "The saved check does not match the current work. Review and check/save again. Existing answers and model outputs are retained."


def checkpoint(mission, state, settings, rows, responses, extra=None):
    from lab.evidence import save_run
    capture_inputs(state)
    metadata = dict(extra or {})
    metadata["draft_signature"] = signature(mission, state)
    # A readable snapshot enables recovery and explains a stale check without
    # repeating inference. The signature still validates the exact experiment.
    payload = signature_payload(mission,state)
    metadata["draft_inputs"] = {key:value for key,value in payload.items() if key != "checked_actions"}
    previous = {"mission_2": "mission_1", "mission_3": "mission_2"}.get(mission)
    if previous:
        from lab.evidence import saved_run
        metadata["upstream_run"] = saved_run(previous).get("run_id")
    return save_run(mission, settings, rows, responses, metadata)
