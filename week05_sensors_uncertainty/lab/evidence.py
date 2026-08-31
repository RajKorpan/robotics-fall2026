from __future__ import annotations
import hashlib, json
from typing import Any
def student_seed(course_id:str,mission:str)->int:
    digest=hashlib.sha256(f"{course_id.strip().lower()}::{mission}".encode()).digest(); return int.from_bytes(digest[:4],"big")
def evidence_id(*values:Any)->str: return hashlib.sha256(json.dumps(values,sort_keys=True,default=str).encode()).hexdigest()[:16]

