#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from evaluation.contracts import baseline_requirements, redesign_requirements
from evaluation.metrics import matched_comparison, summarize


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("kind", choices=("baseline", "redesign")); parser.add_argument("input", type=Path); parser.add_argument("--output", type=Path); args = parser.parse_args(); evidence = json.loads(args.input.read_text(encoding="utf-8"))
    if args.kind == "baseline": evidence["metrics"] = summarize(evidence); checks = baseline_requirements(evidence)
    else: evidence["comparison"] = matched_comparison(evidence.get("baseline", {}), evidence.get("redesign", {})); checks = redesign_requirements(evidence)
    evidence["checks"] = [r.__dict__ for r in checks]; evidence["passed"] = all(r.passed for r in checks); rendered = json.dumps(evidence, indent=2)
    if args.output: args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(rendered+"\n", encoding="utf-8")
    print(rendered); return 0 if evidence["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())

