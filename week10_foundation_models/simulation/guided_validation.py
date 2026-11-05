"""Worked validation examples used only in Guided Activity 6."""

STATE = {"position": "base", "locations": {"base": [0, 0], "shelf": [2, 1], "desk": [3, 2], "closed_room": [4, 1]},
         "objects": ["cup", "shelf"], "allowed": ["navigate_to", "inspect", "report", "stop"],
         "reachable": ["base", "shelf", "desk"], "forbidden": ["closed_room"], "observation_max_age_s": 2.0}


def action(tool, args, **kwargs):
    return {"tool": tool, "args": args, "source": "user", "observation_age_s": .1, "confidence": .9, "risk": "low", **kwargs}


CASES = (
    ("navigate", action("navigate_to", {"location": "shelf"}), "EXECUTE"),
    ("inspect", action("inspect", {"object": "cup"}), "EXECUTE"),
    ("unreachable", action("navigate_to", {"location": "closed_room"}), "REJECT"),
    ("stale", action("inspect", {"object": "cup"}, observation_age_s=30), "ABSTAIN"),
    ("poster", action("navigate_to", {"location": "desk"}, source="environment"), "REJECT"),
    ("ambiguous", action("inspect", {"object": "cup"}, ambiguous=True), "CONFIRM"),
)


def reference_validate(proposal, state):
    """Reference checks for the six guided worked examples."""
    tool = proposal.get("tool")
    if tool not in state["allowed"] or proposal.get("source") != "user":
        return "REJECT"
    args = proposal.get("args")
    schema = {"navigate_to": "location", "inspect": "object", "report": "message", "stop": None}
    field = schema[tool]
    if not isinstance(args, dict) or set(args) != ({field} if field else set()):
        return "REJECT"
    if field and (not isinstance(args[field], str) or not args[field].strip()):
        return "REJECT"
    if tool == "navigate_to" and (args[field] not in state["locations"] or args[field] not in state["reachable"] or args[field] in state["forbidden"]):
        return "REJECT"
    if tool == "inspect" and args[field] not in state["objects"]:
        return "REJECT"
    if proposal["observation_age_s"] > state["observation_max_age_s"] or proposal["confidence"] < .6:
        return "ABSTAIN"
    if proposal.get("ambiguous") or proposal["risk"] == "high":
        return "CONFIRM"
    return "EXECUTE"


def execute(proposal, state):
    """A bounded conventional skill layer. No hardware or external tools."""
    error = reference_validate({**proposal, "source": "user", "observation_age_s": 0, "confidence": 1, "ambiguous": False, "risk": "low"}, state)
    if error != "EXECUTE":
        return False, "Skill failed: unsupported tool, invalid arguments or unavailable destination"
    tool, args = proposal["tool"], proposal["args"]
    if tool == "navigate_to":
        state["position"] = args["location"]
        return True, "Arrived at " + state["position"]
    if tool == "inspect":
        state["last_observation"] = args["object"]
        return True, "Fresh observation recorded for " + args["object"]
    if tool == "report":
        state["last_report"] = args["message"]
        return True, "Report delivered"
    state["stopped"] = True
    return True, "Motion stopped"
