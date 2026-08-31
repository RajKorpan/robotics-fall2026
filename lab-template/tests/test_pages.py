from __future__ import annotations

import unittest
from pathlib import Path


class PageRenderTests(unittest.TestCase):
    def test_every_stage_renders_without_exception(self) -> None:
        try:
            from streamlit.testing.v1 import AppTest
        except ModuleNotFoundError as error:
            raise unittest.SkipTest("Streamlit is not installed in this test runtime") from error

        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app = AppTest.from_file(str(app_path), default_timeout=15).run()
        self.assertFalse(app.exception)
        for stage in ("concepts", "background", "playground", "lab", "final_submission"):
            with self.subTest(stage=stage):
                app.session_state["stage"] = stage
                app.run()
                self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
