from dataclasses import dataclass


@dataclass
class Transition:
    state: str; display: str


def classify_command(text):
    normalized = text.strip().lower()
    if normalized in ("yes", "confirm"): return "CONFIRM"
    if normalized in ("no", "cancel"): return "CANCEL"
    if "cup" in normalized and not any(color in normalized for color in ("red", "blue")): return "AMBIGUOUS"
    if normalized.startswith("correct:"): return "REQUEST"
    return "REQUEST" if normalized else "EMPTY"


def command_transition(state, text, confirmation_required=True):
    kind = classify_command(text)
    if kind == "CONFIRM" and state == "CONFIRMING": return Transition("ACTING", "Confirmed. Starting the bounded task. Stop remains available.")
    if kind == "CANCEL": return Transition("LISTENING", "Cancelled. Listening for a new request.")
    if kind == "AMBIGUOUS": return Transition("ERROR", "I found more than one cup. Say red cup or blue cup.")
    if kind == "REQUEST":
        cleaned = text.split(":", 1)[1].strip() if text.strip().lower().startswith("correct:") else text.strip()
        return Transition("CONFIRMING", f"I heard: {cleaned}. Reply yes to confirm or correct: followed by a new request.") if confirmation_required else Transition("ACTING", f"Starting: {cleaned}")
    return Transition("ERROR", "I did not receive a command. Please try again.")
