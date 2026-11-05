"""Small, inspectable teaching examples. No neural inference or training is claimed."""
from __future__ import annotations

import math
import array
import wave

from simulation.guided_validation import STATE


def audio_envelope(path, bins=55):
    with wave.open(str(path), 'rb') as audio:
        if audio.getsampwidth() != 2:
            raise ValueError("The guided speech example must use 16-bit PCM")
        samples = array.array('h', audio.readframes(audio.getnframes()))
        duration = audio.getnframes() / audio.getframerate()
    size = max(1, len(samples) // bins)
    peaks = [max((abs(v) for v in samples[i:i+size]), default=0) / 32768 for i in range(0, len(samples), size)]
    return duration, peaks


def region_matches(instruction):
    matches = {"Point to the blue cup": ["A"], "Point to the red cup": ["B"], "Point to the cup": ["A", "B"]}
    return matches[instruction][:]


def demonstration_records():
    rows = []
    for index in range(4):
        before = min(index * .2, .6)
        speed = .2 if index < 3 else 0.
        rows.append({"Step": index + 1, "Time (s)": index, "Observed x (m)": round(before, 2),
                     "Forward command (m/s)": speed, "Held for (s)": 1,
                     "Resulting x (m)": round(before + speed, 2),
                     "Observation": "shelf is still ahead" if index < 3 else "at the shelf",
                     "Action": "drive forward" if index < 3 else "stop"})
    return rows


def decoded_movement(token, angle_degrees):
    # A course illustration, not the OpenVLA tokenizer or dataset unnormalizer.
    source_dx = (token / 255 * 2 - 1) * .1
    theta = math.radians(angle_degrees)
    return {"camera_dx_m": source_dx, "world_dx_m": source_dx * math.cos(theta), "world_dy_m": source_dx * math.sin(theta)}


def chunk_trial(chunk, hz):
    """Hold each predicted displacement for a chunk while a target changes at 0.5 s."""
    x = y = 0.
    dx = dy = 0.
    selected = (.6, 0.)
    rows = []
    reaction = None
    for index in range(hz * 2):
        t = index / hz
        target = (.6, 0.) if t < .5 else (.2, .6)
        update = index % chunk == 0
        if update:
            selected = target
            distance = math.hypot(selected[0] - x, selected[1] - y)
            amount = min(.5 / hz, distance)
            dx, dy = ((selected[0] - x) / distance * amount, (selected[1] - y) / distance * amount) if distance else (0., 0.)
            if t >= .5 and reaction is None:
                reaction = t
        x, y = x + dx, y + dy
        rows.append({"time_s": round(t, 3), "x_m": x, "y_m": y, "target_x_m": target[0], "target_y_m": target[1],
                     "command_dx_m": dx, "command_dy_m": dy, "new_observation": update,
                     "error_m": math.hypot(x - target[0], y - target[1])})
    return rows, round(reaction - .5, 3)


def decision_walkthrough(proposal, state=None):
    """Trace the same rules as the mission validator, stopping at the first failure."""
    state = STATE if state is None else state
    tool = proposal.get("tool")
    args = proposal.get("args")
    required = {"navigate_to": "location", "inspect": "object", "report": "message", "stop": None}.get(tool)
    checks = [
        ("Supported skill", lambda: tool in state["allowed"], "REJECT", "The proposed tool must be in the robot's allowed list."),
        ("Authorized instruction", lambda: proposal.get("source") == "user", "REJECT", "A poster or other environmental text is evidence, not an authorized user command."),
        ("Argument fields", lambda: isinstance(args, dict) and set(args) == ({required} if required else set()), "REJECT", "Use exactly the fields required by the selected tool."),
        ("Argument types", lambda: not required or isinstance(args[required], str) and bool(args[required].strip()), "REJECT", "A destination, object or message must be nonempty text."),
        ("Destination is available", lambda: tool != "navigate_to" or args[required] in state["locations"] and args[required] in state["reachable"] and args[required] not in state["forbidden"], "REJECT", "A destination must exist, be reachable and be permitted."),
        ("Object is known", lambda: tool != "inspect" or args[required] in state["objects"], "REJECT", "An object name must match verified state."),
        ("Observation is current", lambda: proposal["observation_age_s"] <= state["observation_max_age_s"], "ABSTAIN", "The evidence may be no more than two seconds old."),
        ("Evidence clears the score threshold", lambda: proposal["confidence"] >= .6, "ABSTAIN", "This exercise requires a score of at least 0.6. A score is not a correctness guarantee."),
        ("No unresolved ambiguity or consequence", lambda: not proposal.get("ambiguous", False) and proposal["risk"] != "high", "CONFIRM", "A person must resolve ambiguity or authorize a consequential action."),
    ]
    rows = []
    verdict = "EXECUTE"
    stopped = False
    for title, check, failure, reason in checks:
        passed = None if stopped else check()
        rows.append({"Check": title, "Result": "Not reached" if stopped else "Pass" if passed else failure, "Why": reason})
        if not stopped and not passed:
            verdict, stopped = failure, True
    return verdict, rows
