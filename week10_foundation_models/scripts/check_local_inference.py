"""Maintainer integration check: real CPU generation with networking disabled in HF."""
import gc
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from lab.local_config import LANGUAGE_TASKS, VISION_TASKS
from lab.local_inference import load_model, generate


def main():
    results = []
    folder = ROOT / "runtime" / "live_inference_check"
    folder.mkdir(parents=True, exist_ok=True)
    for kind in ("language", "vision"):
        started = time.perf_counter()
        loaded = load_model(kind)
        print(kind, "loaded in", round(time.perf_counter()-started, 2), "seconds", flush=True)
        cases = LANGUAGE_TASKS if kind == "language" else VISION_TASKS
        for case in cases:
            prompt = cases[case]["prompt"]
            row = generate(kind, {"kind": kind, "case": case, "prompt": prompt}, loaded, folder / "status.json", folder / "cancel")
            results.append(row)
            print(case, row["generation_seconds"], row["output"], flush=True)
        prompt = "The robot has no gripper. Can it carry the cup? Explain briefly what it can do instead." if kind == "language" else "Describe only visible objects. Where is the drawing compass relative to the brown leather item? What task information would you need before choosing a tool?"
        row = generate(kind, {"kind": kind, "case": "custom", "prompt": prompt}, loaded, folder / "status.json", folder / "cancel")
        results.append(row)
        print("revised", row["generation_seconds"], row["output"], flush=True)
        del loaded
        gc.collect()
    (folder / "results.json").write_text(json.dumps(results, indent=2))
    print("All eight live model generations completed", flush=True)


if __name__ == "__main__":
    main()
