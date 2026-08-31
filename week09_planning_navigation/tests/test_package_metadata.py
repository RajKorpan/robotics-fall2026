import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class PackageTests(unittest.TestCase):
    def test_ros_package_and_entrypoints(self):
        root = Path(__file__).resolve().parents[1] / "ros2_ws" / "src" / "week09_nav_tools"
        self.assertEqual(ET.parse(root / "package.xml").getroot().findtext("name"), "week09_nav_tools")
        setup = (root / "setup.py").read_text(encoding="utf-8")
        for name in ("plan_probe", "navigate_probe", "social_monitor"): self.assertIn(name, setup)
        self.assertTrue((root / "launch" / "course_navigation.launch.py").exists())


if __name__ == "__main__": unittest.main()

