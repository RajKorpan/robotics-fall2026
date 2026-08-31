from __future__ import annotations

import json
from pathlib import Path

from lab_config import LAB

ROOT = Path(__file__).resolve().parents[1]


def save_mission(mission, evidence, responses, uploads=()):
    root = ROOT / LAB.submission_directory / mission; root.mkdir(parents=True, exist_ok=True)
    (root / "checked_evidence.json").write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8")
    subset = {k: v for k, v in responses.items() if k.startswith(mission + ".")}
    (root / "responses.json").write_text(json.dumps(subset, indent=2)+"\n", encoding="utf-8")
    for upload in uploads:
        if upload is not None: (root / Path(upload.name).name).write_bytes(upload.getvalue())


def write_manifest(st):
    root = ROOT / LAB.submission_directory; root.mkdir(exist_ok=True)
    document = {"lab_id": LAB.id, "student": st.session_state["student"], "completed_missions": st.session_state["completed_missions"], "responses": st.session_state["responses"]}
    path = root / "manifest.json"; path.write_text(json.dumps(document, indent=2)+"\n", encoding="utf-8"); return path
