import json
def load_json(upload):
    if upload is None: return None
    try: return json.loads(upload.getvalue().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError): return None

