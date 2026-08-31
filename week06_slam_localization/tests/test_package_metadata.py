import unittest, xml.etree.ElementTree as ET
from pathlib import Path
class PackageTests(unittest.TestCase):
    def test_package_metadata(self):
        root = Path(__file__).resolve().parents[1] / "ros2_ws" / "src" / "course_slam_tools"
        self.assertEqual(ET.parse(root / "package.xml").getroot().findtext("name"), "course_slam_tools")
        for path in (root / "setup.py", root / "launch" / "mapping.launch.py", root / "launch" / "localization.launch.py"): self.assertTrue(path.exists())
if __name__ == "__main__": unittest.main()
