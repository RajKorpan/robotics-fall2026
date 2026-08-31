import json
from datetime import datetime, timezone
from pathlib import Path
from lab_config import LAB


def submission_root(): return Path(__file__).resolve().parents[1] / LAB.submission_directory
def load_responses():
    path = submission_root() / "autosave" / "responses.json"
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError): return {}
def autosave_responses(st):
    payload = {"schema_version": 1, "lab_id": LAB.id, "updated_at": datetime.now(timezone.utc).isoformat(), "student": dict(st.session_state["student"]), "responses": dict(st.session_state["responses"])}
    target = submission_root() / "autosave"; target.mkdir(parents=True, exist_ok=True); path = target / "responses.json"; temp = path.with_suffix(".tmp"); temp.write_text(json.dumps(payload, indent=2), encoding="utf-8"); temp.replace(path)
    lines = [f"# {LAB.title} responses", ""]
    for key, value in payload["student"].items(): lines.append(f"- {key.title()}: {value}")
    for key, value in sorted(payload["responses"].items()): lines.extend(["", f"## {key}", "", str(value)])
    (target / "responses.md").write_text("\n".join(lines)+"\n", encoding="utf-8"); return path

