from datetime import datetime,timezone
from hashlib import sha256
def identity(mission,settings): return sha256(repr((mission,sorted(settings.items()))).encode()).hexdigest()[:12],datetime.now(timezone.utc).isoformat()

