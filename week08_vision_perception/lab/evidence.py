import hashlib, json
def evidence_id(*values): return hashlib.sha256(json.dumps(values, sort_keys=True, default=str).encode()).hexdigest()[:16]
def load_json(upload):
    if upload is None: return None
    try: return json.loads(upload.getvalue().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError): return None
