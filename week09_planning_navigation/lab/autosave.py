import json
from pathlib import Path
from lab_config import LAB

ROOT = Path(__file__).resolve().parents[1]


def load_state():
    path = ROOT / LAB.submission_directory / "autosave" / "responses.json"
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError): return {}


def save(st):
    payload = {"schema_version": 1, "lab_id": LAB.id, "student": dict(st.session_state["student"]), "responses": dict(st.session_state["responses"]), "completed_missions": list(st.session_state["completed_missions"]), "evidence": dict(st.session_state["evidence"])}
    target = ROOT / LAB.submission_directory / "autosave"; target.mkdir(parents=True, exist_ok=True)
    path = target / "responses.json"; temporary = path.with_suffix(".tmp"); temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8"); temporary.replace(path)

