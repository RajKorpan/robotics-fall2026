from __future__ import annotations
import hashlib, importlib, json, math, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PACKAGE=ROOT/"ros2_ws"/"src"/"week03_pattern"; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(PACKAGE))
from lab.ai_log import assigned_pattern

def integrate(segments):
    x=y=theta=0.0
    for segment in segments:
        v=float(segment.linear_x); w=float(segment.angular_z); d=float(segment.duration)
        if abs(w)<1e-9: x+=v*d*math.cos(theta); y+=v*d*math.sin(theta)
        else:
            final=theta+w*d; radius=v/w; x+=radius*(math.sin(final)-math.sin(theta)); y-=radius*(math.cos(final)-math.cos(theta)); theta=final
        theta=math.atan2(math.sin(theta),math.cos(theta))
    return x,y,theta
def shape_ok(name,segments,pose):
    x,y,theta=pose
    if name=="rounded_rectangle": return len(segments)>=8 and math.hypot(x,y)<=0.30 and abs(theta)<=0.35
    if name=="l_path": return len(segments)>=3 and x>=0.15 and y>=0.15 and abs(abs(theta)-math.pi/2)<=0.35
    signs=[1 if s.angular_z>0 else -1 for s in segments if abs(s.angular_z)>1e-6]
    return len(segments)>=4 and len(signs)>=4 and all(a!=b for a,b in zip(signs,signs[1:])) and abs(theta)<=0.5
def main():
    student=json.loads((ROOT/"student_submission"/"student.json").read_text(encoding="utf-8")); pattern_name=assigned_pattern(str(student.get("course_id","")))
    environment=dict(os.environ); environment["WEEK03_ASSIGNED_PATTERN"]=pattern_name
    tests=subprocess.run([sys.executable,"-m","unittest","discover","-s",str(PACKAGE/"test"),"-v"],cwd=PACKAGE,capture_output=True,text=True,env=environment)
    output=tests.stdout+tests.stderr; match=re.search(r"Ran (\d+) tests?",output); test_count=int(match.group(1)) if match else 0
    try:
        module=importlib.import_module("week03_pattern.pattern"); segments=module.build_pattern(pattern_name); pose=integrate(segments); bounded=all(abs(float(s.linear_x))<=0.22 and abs(float(s.angular_z))<=0.8 and float(s.duration)>0 for s in segments); shape=shape_ok(pattern_name,segments,pose)
    except Exception as error:
        segments=[]; pose=(0.0,0.0,0.0); bounded=False; shape=False; output+=f"\nEvaluator error: {type(error).__name__}: {error}\n"
    run_path=ROOT/"runtime"/"evidence"/"pattern_run.json"; run=json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else {}
    integration=bool(run.get("completed")) and run.get("pattern")==pattern_name and shape
    original_path=ROOT/"student_submission"/"mission_3"/"ai"/"original_output.txt"; source_path=PACKAGE/"week03_pattern"/"pattern.py"
    original=original_path.read_text(encoding="utf-8") if original_path.exists() else ""; source=source_path.read_text(encoding="utf-8")
    payload={"schema_version":1,"captured_at":datetime.now(timezone.utc).isoformat(),"pattern":pattern_name,"unit_tests_passed":tests.returncode==0,"test_count":test_count,"unit_test_output":output,"commands_bounded":bounded,"shape_check_passed":shape,"predicted_endpoint":{"x":pose[0],"y":pose[1],"theta":pose[2]},"integration_passed":integration,"final_stop_verified":bool(run.get("final_stop_verified")),"source_sha256":hashlib.sha256(source.encode()).hexdigest(),"source_differs_from_original":bool(original) and source.strip()!=original.strip(),"segment_count":len(segments)}
    target=ROOT/"runtime"/"evidence"/"ai_evaluation.json"; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(output); print(json.dumps(payload,indent=2))
    raise SystemExit(0 if payload["unit_tests_passed"] and bounded and shape and integration and payload["final_stop_verified"] else 1)
if __name__=="__main__": main()
