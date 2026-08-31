from __future__ import annotations

CONDITIONS = ("normal", "dim", "glare", "far", "occluded", "rotated", "cluttered", "distractor")

def evaluate_rows(rows: list[dict], threshold: float | None = None) -> dict:
    selected = []
    for row in rows:
        confidence = float(row.get("confidence", 0.0))
        predicted = bool(row.get("detected", False)) and (threshold is None or confidence >= threshold)
        selected.append((bool(row.get("expected", False)), predicted, float(row.get("latency_ms", 0.0)), row.get("condition")))
    tp = sum(expected and predicted for expected, predicted, _, _ in selected)
    fp = sum(not expected and predicted for expected, predicted, _, _ in selected)
    fn = sum(expected and not predicted for expected, predicted, _, _ in selected)
    tn = sum(not expected and not predicted for expected, predicted, _, _ in selected)
    precision = tp / max(1, tp + fp); recall = tp / max(1, tp + fn)
    latencies = [latency for _, _, latency, _ in selected if latency >= 0]
    return {"sample_count": len(rows), "conditions": sorted({str(row.get('condition', '')) for row in rows}), "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": precision, "recall": recall, "false_positive_rate": fp / max(1, fp + tn), "mean_latency_ms": sum(latencies) / max(1, len(latencies))}

def threshold_sweep(rows: list[dict], thresholds=(.20, .35, .50, .65, .80)) -> list[dict]:
    return [{"threshold": value, **evaluate_rows(rows, value)} for value in thresholds]

def conditions_complete(rows: list[dict]) -> bool:
    return set(CONDITIONS).issubset({str(row.get("condition")) for row in rows})
