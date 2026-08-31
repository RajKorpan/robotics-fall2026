import tempfile, unittest
from pathlib import Path
from analysis.localization import summarize, trial_passes
from analysis.map_metrics import analyze_pixels, quality_score, read_pgm
from scripts.analyze_map import parse_map_metadata

class AnalysisTests(unittest.TestCase):
    def test_ascii_pgm_and_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.pgm"; path.write_bytes(b"P2\n# test\n4 2\n255\n0 0 254 205 254 254 205 0\n")
            width, height, maximum, pixels = read_pgm(path); metrics = analyze_pixels(width, height, maximum, pixels, .05)
            self.assertEqual((width, height, maximum), (4, 2, 255)); self.assertAlmostEqual(metrics["known_fraction"], .75); self.assertGreaterEqual(quality_score(metrics), 0)
    def test_localization_summary(self):
        rows = [{"time": i, "x": 1 + .001 * i, "y": 2, "yaw": 0, "covariance_trace": .8 if i < 2 else .2} for i in range(21)]
        metrics = summarize(rows); self.assertEqual(metrics["sample_count"], 21); self.assertEqual(metrics["convergence_time"], 2)
        self.assertTrue(trial_passes("good_initial_pose", metrics))
    def test_map_yaml_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.yaml"; path.write_text("image: map.pgm\nresolution: 0.05\norigin: [0, 0, 0]\n", encoding="utf-8")
            self.assertEqual(parse_map_metadata(path)["image"], "map.pgm")
    def test_empty_summary(self): self.assertEqual(summarize([])["sample_count"], 0)

if __name__ == "__main__": unittest.main()
