from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from lab_config import LAB
ROOT=Path(__file__).resolve().parents[1]
def submission_root(): return ROOT/LAB.submission_directory
def load_state():
    path=submission_root()/"autosave"/"responses.json"
    if not path.exists(): return {}
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError): return {}
def _atomic(path,text):
    path.parent.mkdir(parents=True,exist_ok=True); temporary=path.with_suffix(path.suffix+".tmp"); temporary.write_text(text,encoding="utf-8"); temporary.replace(path)
def save(st):
    payload={"schema_version":1,"lab_id":LAB.id,"updated_at":datetime.now(timezone.utc).isoformat(),"student":dict(st.session_state.get("student",{})),"responses":dict(st.session_state.get("responses",{})),"completed_missions":list(st.session_state.get("completed_missions",[])),"checked_evidence_ids":dict(st.session_state.get("checked_evidence_ids",{})),"mission_2_attempts":list(st.session_state.get("mission_2_attempts",[])),"mission_3_results":dict(st.session_state.get("mission_3_results",{}))}
    path=submission_root()/"autosave"/"responses.json"; _atomic(path,json.dumps(payload,indent=2,sort_keys=True)); lines=[f"# {LAB.title}",""]
    for key,value in payload["student"].items(): lines.append(f"- {key.replace('_',' ').title()}: {value}")
    for key,value in sorted(payload["responses"].items()): lines.extend(["",f"## {key}","",str(value)])
    _atomic(path.with_suffix(".md"),"\n".join(lines)+"\n"); (submission_root()/"student.json").write_text(json.dumps(payload["student"],indent=2),encoding="utf-8"); return path
