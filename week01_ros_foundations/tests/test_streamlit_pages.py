from __future__ import annotations

import unittest
from pathlib import Path


try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest = None


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(AppTest is not None, "Streamlit is available in the course container")
class StreamlitPageTests(unittest.TestCase):
    def test_every_stage_renders_without_exception(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"))
        app.run(timeout=20)
        self.assertFalse(app.exception)
        for stage in (
            "part_1",
            "part_2",
            "part_3",
            "preflight",
            "mission_1",
            "mission_2",
            "mission_3",
            "final",
        ):
            with self.subTest(stage=stage):
                app.session_state["stage"] = stage
                app.run(timeout=20)
                self.assertFalse(app.exception)

    def test_part_one_continue_unlocks_after_three_comparisons(self) -> None:
        app = AppTest.from_file(str(ROOT / "app.py"))
        app.run(timeout=20)
        app.session_state["stage"] = "part_1"
        app.session_state["responses"] = {
            "part_1.activity": {
                example: {"normal": True, "changed": True}
                for example in ("sensor", "timing", "hardware")
            }
        }
        app.run(timeout=20)
        button = next(item for item in app.button if item.label == "Continue to Part 2")
        self.assertFalse(button.disabled)


if __name__ == "__main__":
    unittest.main()
