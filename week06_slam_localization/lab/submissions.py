import json
from datetime import datetime, timezone
from pathlib import Path
from lab.autosave import submission_root
from lab_config import LAB

def save_mission(mission, evidence, responses, uploads=()):
    target = submission_root() / mission; target.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "lab_id": LAB.id, "mission_id": mission, "saved_at": datetime.now(timezone.utc).isoformat(), "evidence": evidence}
    (target / "submission.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    prefix = mission + "."; lines = [f"# {mission.replace('_', ' ').title()}", ""]
    for key, value in sorted(responses.items()):
        if key.startswith(prefix): lines.extend([f"## {key[len(prefix):].replace('_', ' ').title()}", "", str(value), ""])
    (target / "explanation.md").write_text("\n".join(lines), encoding="utf-8")
    for index, upload in enumerate(uploads, start=1):
        if upload is not None:
            destination = target / Path(upload.name).name
            if destination.exists(): destination = target / f"{index:02d}_{Path(upload.name).name}"
            destination.write_bytes(upload.getvalue())
    return target

def write_manifest(st):
    root = submission_root(); files = sorted(str(path.relative_to(root)).replace("\\", "/") for path in root.rglob("*") if path.is_file() and path.name != "manifest.json")
    payload = {"schema_version": 1, "lab_id": LAB.id, "generated_at": datetime.now(timezone.utc).isoformat(), "student": dict(st.session_state["student"]), "completed_missions": list(st.session_state["completed_missions"]), "files": files}
    path = root / "manifest.json"; path.write_text(json.dumps(payload, indent=2), encoding="utf-8"); return path
