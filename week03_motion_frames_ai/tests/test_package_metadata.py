from __future__ import annotations
import unittest, xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PackageTests(unittest.TestCase):
    def test_manifests(self):
        manifests=sorted((ROOT/"ros2_ws"/"src").glob("*/package.xml")); self.assertEqual(len(manifests),4)
        for path in manifests:
            with self.subTest(path=path): self.assertTrue(ET.parse(path).getroot().findtext("name"))
if __name__=="__main__": unittest.main()

