import unittest,xml.etree.ElementTree as ET
from pathlib import Path


class PackageTests(unittest.TestCase):
    def test_metadata_and_files(self):
        root=Path(__file__).resolve().parents[1]/"ros2_ws"/"src"/"week11_hri_demo"; self.assertEqual(ET.parse(root/"package.xml").getroot().findtext("name"),"week11_hri_demo")
        for path in ("launch/interaction.launch.py","config/baseline.yaml","config/redesign_starter.yaml","week11_hri_demo/interaction_demo.py","week11_hri_demo/event_recorder.py"): self.assertTrue((root/path).exists())


if __name__=="__main__": unittest.main()

