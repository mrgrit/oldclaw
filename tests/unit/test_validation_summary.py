import unittest

from packages.project_service import summarize_validation_evidence


class ValidationSummaryUnitTest(unittest.TestCase):
    def test_inconclusive_without_evidence(self):
        status, summary, actual, latest_evidence_id = summarize_validation_evidence([])
        self.assertEqual(status, "inconclusive")
        self.assertEqual(summary, "Validation completed with no evidence")
        self.assertEqual(actual, {"evidence_count": 0, "failing_evidence_count": 0})
        self.assertIsNone(latest_evidence_id)

    def test_failed_with_non_zero_exit_code(self):
        status, summary, actual, latest_evidence_id = summarize_validation_evidence(
            [
                {"id": "ev_1", "exit_code": 0},
                {"id": "ev_2", "exit_code": 9},
            ]
        )
        self.assertEqual(status, "failed")
        self.assertEqual(summary, "Validation failed with 1 failing evidence item(s)")
        self.assertEqual(actual, {"evidence_count": 2, "failing_evidence_count": 1})
        self.assertEqual(latest_evidence_id, "ev_2")

    def test_passed_with_only_successful_evidence(self):
        status, summary, actual, latest_evidence_id = summarize_validation_evidence(
            [
                {"id": "ev_1", "exit_code": 0},
                {"id": "ev_2", "exit_code": None},
            ]
        )
        self.assertEqual(status, "passed")
        self.assertEqual(summary, "Validation passed with 2 evidence item(s)")
        self.assertEqual(actual, {"evidence_count": 2, "failing_evidence_count": 0})
        self.assertEqual(latest_evidence_id, "ev_2")


if __name__ == "__main__":
    unittest.main()
