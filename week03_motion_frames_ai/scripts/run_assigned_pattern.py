from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
student=json.loads((ROOT/"student_submission"/"student.json").read_text(encoding="utf-8"))
from lab.ai_log import assigned_pattern
pattern=assigned_pattern(str(student.get("course_id","")))
print(f"Running assigned pattern: {pattern}")
raise SystemExit(subprocess.run(["ros2","run","week03_pattern","pattern_node","--ros-args","-p",f"pattern:={pattern}"],cwd=ROOT/"ros2_ws").returncode)
