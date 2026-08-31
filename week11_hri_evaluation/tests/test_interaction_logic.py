import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"ros2_ws"/"src"/"week11_hri_demo"))
from week11_hri_demo.interaction_logic import classify_command,command_transition


class LogicTests(unittest.TestCase):
    def test_ambiguous_cup_requests_clarification(self): self.assertEqual(command_transition("LISTENING","bring the cup").state,"ERROR")
    def test_request_requires_confirmation(self): self.assertEqual(command_transition("LISTENING","bring the blue cup").state,"CONFIRMING")
    def test_confirm_acts_only_from_confirmation(self): self.assertEqual(command_transition("CONFIRMING","yes").state,"ACTING")
    def test_cancel_returns_to_listening(self): self.assertEqual(command_transition("CONFIRMING","cancel").state,"LISTENING")
    def test_case_insensitive_correction_is_cleaned(self): self.assertIn("bring the blue cup",command_transition("CONFIRMING","Correct: bring the blue cup").display)


if __name__=="__main__": unittest.main()
