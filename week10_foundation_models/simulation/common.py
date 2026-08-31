from datetime import datetime, timezone
from hashlib import sha256


def run_identity(mission_id, settings):
    canonical = repr((mission_id, sorted(settings.items())))
    return sha256(canonical.encode()).hexdigest()[:12], datetime.now(timezone.utc).isoformat()

