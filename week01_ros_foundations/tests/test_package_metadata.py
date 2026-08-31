from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PackageMetadataTests(unittest.TestCase):
    def test_ros_package_manifests_are_well_formed(self) -> None:
        manifests = sorted((ROOT / "ros2_ws" / "src").glob("*/package.xml"))
        self.assertEqual(len(manifests), 5)
        for manifest in manifests:
            with self.subTest(package=manifest.parent.name):
                root = ET.parse(manifest).getroot()
                self.assertEqual(root.tag, "package")
                self.assertTrue(root.findtext("name"))


if __name__ == "__main__":
    unittest.main()

