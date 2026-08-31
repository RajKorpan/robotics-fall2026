from __future__ import annotations
import argparse, json
from pathlib import Path
from evaluation.behavior import BehaviorConfig, DEFAULT_SCENARIOS, evaluate_scenarios
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True, type=Path); parser.add_argument("--min-confidence", type=float, default=.6); parser.add_argument("--stop-area", type=float, default=.22); parser.add_argument("--stale-after", type=float, default=.6); args = parser.parse_args()
    config = BehaviorConfig(min_confidence=args.min_confidence, stop_area=args.stop_area, stale_after=args.stale_after); result = evaluate_scenarios(DEFAULT_SCENARIOS, config); payload = {"schema_version": 1, "config": config.__dict__, "result": result}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8"); print(json.dumps(result, indent=2)); raise SystemExit(0 if result["passed"] else 1)
if __name__ == "__main__": main()
