import csv,io,json
from datetime import datetime,timezone
from lab.autosave import submission_root
from lab_config import LAB
def _csv(result):
    columns=list(result.traces); length=max((len(v) for v in result.traces.values()),default=0); stream=io.StringIO(newline=""); writer=csv.writer(stream); writer.writerow(columns)
    for i in range(length): writer.writerow([result.traces[c][i] if i<len(result.traces[c]) else "" for c in columns])
    return stream.getvalue()
def save_mission(result,check,explanations):
    target=submission_root()/result.mission_id; target.mkdir(parents=True,exist_ok=True); payload=result.serializable(); payload.update({"schema_version":1,"lab_id":LAB.id,"passed":check.passed,"requirements":[r.__dict__ for r in check.requirements]}); (target/"submission.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); (target/"run.csv").write_text(_csv(result),encoding="utf-8"); lines=[f"# {result.mission_id} explanations",""]
    for key,value in explanations.items(): lines.extend([f"## {key}","",value,""])
    (target/"explanation.md").write_text("\n".join(lines),encoding="utf-8")
def write_manifest(st):
    root=submission_root(); root.mkdir(parents=True,exist_ok=True); files=sorted(str(p.relative_to(root)).replace("\\","/") for p in root.rglob("*") if p.is_file() and p.name!="manifest.json"); payload={"schema_version":1,"lab_id":LAB.id,"generated_at":datetime.now(timezone.utc).isoformat(),"student":dict(st.session_state["student"]),"completed_missions":list(st.session_state["completed_missions"]),"checked_run_ids":dict(st.session_state["checked_run_ids"]),"files":files}; path=root/"manifest.json"; path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); return path

