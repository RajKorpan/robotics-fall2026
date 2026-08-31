from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from missions import mission_1 as m1, mission_2 as m2, mission_3 as m3
from simulation.kinematics import SEQUENCES, integrate_sequence

class MissionTests(unittest.TestCase):
    def test_motion_gate(self):
        locked="2026-08-31T00:00:00+00:00"; responses={"mission_1.predictions":{name:integrate_sequence(value) for name,value in SEQUENCES.items()},"mission_1.predictions_locked_at":locked,**{f"mission_1.{key}":"Explanation" for key in m1.REFLECTIONS}}
        runs=[{"sequence_id":name,"captured_at":"2026-08-31T00:01:00+00:00","completed":True,"stop_sent":True,"position_error":0.01,"heading_error":0.01} for name in SEQUENCES]
        self.assertTrue(m1.evaluate(runs,responses).passed); runs[0]["stop_sent"]=False; self.assertFalse(m1.evaluate(runs,responses).passed)
    def test_frame_gate(self):
        snapshot={"captured_at":"now","frames":["odom","base_link","base_scan"],"transformed_points":{"one":{"x":1.0,"y":0.0},"two":{"x":2.0,"y":1.0}}}; responses={"mission_2.relationships":dict(m2.RELATIONSHIPS),"mission_2.diagnostics":dict(m2.DIAGNOSTICS),"mission_2.point_answers":dict(snapshot["transformed_points"]),**{f"mission_2.{key}":"Explanation" for key in m2.REFLECTIONS}}
        self.assertTrue(m2.evaluate(snapshot,responses).passed); responses["mission_2.diagnostics"]["typo"]="Velocity limit exceeded"; self.assertFalse(m2.evaluate(snapshot,responses).passed)
    def test_ai_gate(self):
        lock={"pattern":"l_path","locked_at":"now","prompt_sha256":"a","output_sha256":"b","integrity_valid":True}; result={"pattern":"l_path","unit_tests_passed":True,"integration_passed":True,"commands_bounded":True,"final_stop_verified":True,"source_differs_from_original":True,"test_count":7}; responses={f"mission_3.{key}":"Substantive evidence-based individual analysis. "*3 for key in m3.REFLECTIONS}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for relative in ("week03_pattern/pattern.py","week03_pattern/pattern_node.py","test/test_pattern.py"):
                path=root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_text("# source\n"+"x=1\n"*40,encoding="utf-8")
            self.assertTrue(m3.evaluate(result,lock,responses,root).passed); result["final_stop_verified"]=False; self.assertFalse(m3.evaluate(result,lock,responses,root).passed)
if __name__=="__main__": unittest.main()
