import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "assets" / "scenarios"


def load_bank(name): return json.loads((ROOT / name).read_text(encoding="utf-8"))

