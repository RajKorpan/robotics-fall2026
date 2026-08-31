from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from evaluation.metrics import evaluate_rows, threshold_sweep
def truth(value): return str(value).strip().lower() in ("1", "true", "yes", "y")
def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--csv", required=True, type=Path); parser.add_argument("--method", choices=("classical", "learned"), required=True); parser.add_argument("--selected-threshold", type=float, default=.5); parser.add_argument("--output", required=True, type=Path); args = parser.parse_args()
    with args.csv.open(newline="", encoding="utf-8") as handle: rows = list(csv.DictReader(handle))
    for row in rows: row["expected"] = truth(row.get("expected")); row["detected"] = truth(row.get("detected")); row["confidence"] = float(row.get("confidence", 0)); row["latency_ms"] = float(row.get("latency_ms", 0))
    payload = {"schema_version": 1, "method": args.method, "selected_threshold": args.selected_threshold, "rows": rows, "metrics": evaluate_rows(rows, args.selected_threshold if args.method == "learned" else None)}
    if args.method == "learned": payload["threshold_sweep"] = threshold_sweep(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8"); print(json.dumps(payload["metrics"], indent=2))
if __name__ == "__main__": main()
