"""Real local model directional rollouts on the same maze."""
import json
import os
import sys
import uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from lab.local_inference import load_model, rollout
from simulation.robot_room import SCENARIOS, initial_state, summarize, contract
from lab.robot_evidence import complete


def main():
    folder = ROOT / "runtime" / "directional_inference_check"
    folder.mkdir(parents=True, exist_ok=True)
    loaded = load_model("language")
    rows = []
    prompts = {**{k:v["request"] for k,v in SCENARIOS.items()}, "custom":"Reach (11,1). Follow these waypoints in order: (1,1), (7,1), (7,7), (11,7), (11,1). Keep moving toward the next waypoint. Use one-cell directions and avoid walls."}
    for case,prompt in prompts.items():
        request = {"job_id":uuid.uuid4().hex, "kind":"language", "case":case, "prompt":prompt, "phase":"custom" if case == "custom" else "baseline", "task":"robot", "robot_state":initial_state(), "simulator_contract":contract(), "comparison_ids":[r["record"]["job_id"] for r in rows] if case == "custom" else []}
        model = rollout(request, loaded, folder / "status.json", folder / "cancel")
        result = summarize(model)
        rows.append({"record":model, "simulation":result})
        print(case, model["output"], result["reason"], flush=True)
        (folder / "results.json").write_text(json.dumps(rows, indent=2))
    assert complete(rows), "The actual rollouts do not satisfy current evidence requirements"
    assert len({tuple(r["simulation"]["after"]["position"]) for r in rows[:3]}) > 1, "Supplied prompts did not produce distinct outcomes"
    print("Four actual robot rollouts completed and evidence verified", flush=True)


if __name__ == "__main__":
    main()
