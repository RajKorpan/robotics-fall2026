from __future__ import annotations
import csv
from pathlib import Path
import cv2, numpy as np
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "runtime" / "condition_bank"
def scene(condition):
    image = np.full((360, 640, 3), 220, dtype=np.uint8); expected = condition != "distractor"; center = (320, 180); radius = 62
    if condition == "dim": image[:] = 45
    if condition == "far": radius = 18
    if condition == "cluttered":
        rng = np.random.default_rng(8)
        for _ in range(35):
            x, y = int(rng.integers(0, 640)), int(rng.integers(0, 360)); color = tuple(int(x) for x in rng.integers(0, 255, 3)); cv2.rectangle(image, (x, y), (min(639, x + 35), min(359, y + 35)), color, -1)
    if expected:
        if condition == "rotated":
            box = cv2.boxPoints(((320, 180), (130, 75), 38)).astype(np.int32); cv2.fillPoly(image, [box], (40, 190, 40))
        else: cv2.circle(image, center, radius, (40, 190, 40), -1)
        if condition == "occluded": cv2.rectangle(image, (300, 115), (390, 245), (120, 120, 120), -1)
        if condition == "glare": cv2.circle(image, (290, 150), 35, (245, 245, 245), -1)
    else:
        cv2.circle(image, (320, 180), 60, (30, 180, 180), -1); cv2.rectangle(image, (300, 140), (340, 220), (40, 190, 40), -1)
    return image, expected
def main():
    OUT.mkdir(parents=True, exist_ok=True); conditions = ("normal", "dim", "glare", "far", "occluded", "rotated", "cluttered", "distractor"); rows = []
    for condition in conditions:
        image, expected = scene(condition); filename = f"{condition}.png"; cv2.imwrite(str(OUT / filename), image); rows.append({"condition": condition, "expected": expected, "image": filename})
    with (OUT / "ground_truth.csv").open("w", newline="", encoding="utf-8") as handle: writer = csv.DictWriter(handle, fieldnames=rows[0]); writer.writeheader(); writer.writerows(rows)
    print(f"Wrote {len(rows)} conditions to {OUT}")
if __name__ == "__main__": main()
