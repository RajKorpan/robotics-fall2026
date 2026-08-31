import unittest
from missions.mission_3 import MISSION
from simulation.scenarios import load_bank
from simulation.verification import run_verification_suite, verify

PASSING = {"confidence_threshold":.65, "validate_grounding":True, "check_prerequisites":True, "block_unsafe_actions":True, "confirm_consequential":True, "fallback":"stop and request clarification"}


class VerificationTests(unittest.TestCase):
    def test_bounded_configuration_passes(self):
        result = run_verification_suite(PASSING)
        self.assertEqual(result.metrics["correct_dispositions"], 12)
        self.assertEqual(result.metrics["unsafe_executions"], 0)
        self.assertTrue(MISSION.evaluate(result).passed)
    def test_unprotected_system_executes_forbidden_proposal(self):
        case = next(c for c in load_bank("safety_cases.json") if c["id"] == "give_medicine")
        unsafe = {**PASSING, "block_unsafe_actions":False, "check_prerequisites":False, "confirm_consequential":False}
        self.assertEqual(verify(case, unsafe)[0], "EXECUTE")
    def test_low_confidence_abstains(self):
        case = next(c for c in load_bank("safety_cases.json") if c["id"] == "low_confidence_person")
        self.assertEqual(verify(case, PASSING)[0], "ABSTAIN")


if __name__ == "__main__": unittest.main()

