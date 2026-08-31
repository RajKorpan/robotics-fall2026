from __future__ import annotations
import json, math, os
from pathlib import Path

SEQUENCES={"straight":[(0.15,0.0,3.0)],"turn_then_drive":[(0.0,0.5,math.pi),(0.15,0.0,2.0)],"arc":[(0.15,0.4,4.0)]}
def output_dir():
    configured=os.environ.get("WEEK03_EVIDENCE_DIR")
    if configured: return Path(configured).expanduser().resolve()
    root=Path.cwd().parent if Path.cwd().name=="ros2_ws" else Path.cwd(); return root/"runtime"/"evidence"
def atomic_json(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True); temporary=path.with_suffix(path.suffix+".tmp"); temporary.write_text(json.dumps(payload,indent=2),encoding="utf-8"); temporary.replace(path)
def wrap(angle): return math.atan2(math.sin(angle),math.cos(angle))
def integrate(segments):
    x=y=theta=0.0
    for v,w,d in segments:
        if abs(w)<1e-9: x+=v*d*math.cos(theta); y+=v*d*math.sin(theta)
        else:
            final=theta+w*d; radius=v/w; x+=radius*(math.sin(final)-math.sin(theta)); y-=radius*(math.cos(final)-math.cos(theta)); theta=final
        theta=wrap(theta)
    return {"x":x,"y":y,"theta":theta}

