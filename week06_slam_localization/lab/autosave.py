import json
from datetime import datetime, timezone
from pathlib import Path
from lab_config import LAB
ROOT = Path(__file__).resolve().parents[1]
def submission_root(): return ROOT / LAB.submission_directory
def load_state():
    path = submission_root() / "autosave" / "responses.json"
    try: return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError): return {}
def save(st):
    payload = {"schema_version": 1, "lab_id": LAB.id, "updated_at": datetime.now(timezone.utc).isoformat(), "student": dict(st.session_state["student"]), "responses": dict(st.session_state["responses"]), "completed_missions": list(st.session_state["completed_missions"]), "checked_evidence_ids": dict(st.session_state["checked_evidence_ids"]), "evidence": dict(st.session_state["evidence"])}
    target = submission_root() / "autosave"; target.mkdir(parents=True, exist_ok=True)
    path = target / "responses.json"; temporary = path.with_suffix(".tmp"); temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8"); temporary.replace(path)
    lines = [f"# {LAB.title}", ""] + [f"- {key}: {value}" for key, value in payload["student"].items()]
    for key, value in sorted(payload["responses"].items()): lines.extend(["", f"## {key}", "", str(value)])
    (target / "responses.md").write_text("\n".join(lines) + "\n", encoding="utf-8"); (submission_root() / "student.json").write_text(json.dumps(payload["student"], indent=2), encoding="utf-8"); return path
