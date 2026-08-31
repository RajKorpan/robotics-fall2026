import unittest
from missions.mission_1 import MISSION
from simulation.language import ALLOWED_ACTIONS, run_language_suite


class LanguageTests(unittest.TestCase):
    def test_suite_preserves_all_requests_and_exposes_failures(self):
        result = run_language_suite({"response_bank":"course-fm-1.0"})
        self.assertEqual(result.metrics["requests_tested"], 6)
        self.assertGreaterEqual(result.metrics["hallucinated_capability_cases"], 2)
        self.assertTrue(MISSION.evaluate(result).passed)
    def test_allowlist_excludes_consequential_tools(self):
        self.assertNotIn("administer_medication", ALLOWED_ACTIONS)
        self.assertNotIn("unlock", ALLOWED_ACTIONS)


if __name__ == "__main__": unittest.main()

