#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from evaluation.contracts import human_aware_requirements, navigation_requirements, plan_requirements
from evaluation.metrics import social_summary, summarize_plans, summarize_trials


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Week 9 JSON evidence without ROS.")
    parser.add_argument("kind", choices=("plans", "navigation", "human-aware"))
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence = json.loads(args.input.read_text(encoding="utf-8"))
    if args.kind == "plans":
        evidence["metrics"] = summarize_plans(evidence.get("rows", []))
        requirements = plan_requirements(evidence)
    elif args.kind == "navigation":
        evidence["metrics"] = summarize_trials(evidence.get("rows", []))
        requirements = navigation_requirements(evidence)
    else:
        for label in ("baseline", "redesign"):
            run = evidence.get(label, {})
            if not run.get("metrics"): run["metrics"] = social_summary(run)
        requirements = human_aware_requirements(evidence)
    evidence["checks"] = [{**item.__dict__} for item in requirements]
    evidence["passed"] = all(item.passed for item in requirements)
    rendered = json.dumps(evidence, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
