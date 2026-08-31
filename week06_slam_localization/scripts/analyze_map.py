from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from analysis.map_metrics import analyze_pixels, quality_score, read_pgm

def parse_map_metadata(path: Path) -> dict:
    metadata = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line: continue
        key, value = line.split(":", 1); metadata[key.strip()] = value.strip().strip("'\"")
    if "image" not in metadata or "resolution" not in metadata: raise ValueError("Map YAML must define image and resolution")
    return metadata

def main():
    parser = argparse.ArgumentParser(description="Analyze a Nav2 map pair")
    parser.add_argument("--yaml", required=True, type=Path); parser.add_argument("--strategy", required=True)
    parser.add_argument("--duration-min", required=True, type=float); parser.add_argument("--output", required=True, type=Path); args = parser.parse_args()
    metadata = parse_map_metadata(args.yaml); image = Path(metadata["image"])
    if not image.is_absolute(): image = args.yaml.parent / image
    width, height, maximum, pixels = read_pgm(image.resolve()); metrics = analyze_pixels(width, height, maximum, pixels, float(metadata["resolution"]))
    payload = {"schema_version": 1, "captured_at": datetime.now(timezone.utc).isoformat(), "strategy": args.strategy, "duration_minutes": args.duration_min, "map_yaml": args.yaml.name, "map_image": image.name, "metrics": metrics, "quality_score": quality_score(metrics)}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
if __name__ == "__main__": main()
