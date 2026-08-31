import json
from pathlib import Path
from lab_config import LAB
ROOT = Path(__file__).resolve().parents[1]
def save_mission(mission, evidence, responses, uploads=()):
    target=ROOT/LAB.submission_directory/mission; target.mkdir(parents=True, exist_ok=True); (target/"checked_evidence.json").write_text(json.dumps(evidence, indent=2)+"\n", encoding="utf-8"); subset={k:v for k,v in responses.items() if k.startswith(mission+".")}; (target/"responses.json").write_text(json.dumps(subset, indent=2)+"\n", encoding="utf-8")
    used=set()
    for index, upload in enumerate(uploads, 1):
        if upload is None: continue
        name=Path(upload.name).name; name=name if name not in used else f"{index:02d}_{name}"; used.add(name); (target/name).write_bytes(upload.getvalue())
def manifest(st):
    root=ROOT/LAB.submission_directory; root.mkdir(parents=True, exist_ok=True); files=sorted(str(p.relative_to(root)).replace("\\","/") for p in root.rglob("*") if p.is_file() and p.name!="manifest.json"); payload={"schema_version":1,"lab_id":LAB.id,"student":dict(st.session_state["student"]),"completed_missions":list(st.session_state["completed_missions"]),"files":files}; path=root/"manifest.json"; path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); return path
