import unittest

from packages.history_service import summarize_task_memory


class HistorySummaryUnitTest(unittest.TestCase):
    def test_summarize_task_memory_includes_counts_and_validation(self):
        result = summarize_task_memory(
            project={
                "id": "prj_1",
                "status": "completed",
                "current_stage": "close",
                "request_text": "collect evidence",
                "mode": "one_shot",
                "risk_level": "medium",
                "summary": "final report summary",
            },
            playbook_name="diagnose_web_latency",
            targets=[{"id": "tgt_1"}],
            assets=[{"id": "ast_1", "name": "host-1"}],
            evidence=[{"id": "ev_1"}, {"id": "ev_2"}],
            validations=[{"status": "passed"}],
        )

        self.assertIn("playbook=diagnose_web_latency", result["summary"])
        self.assertIn("targets=1", result["summary"])
        self.assertIn("evidence=2", result["summary"])
        self.assertEqual(result["metadata"]["validation_status"], "passed")
        self.assertEqual(result["metadata"]["evidence_count"], 2)

    def test_summarize_task_memory_handles_missing_playbook_and_validation(self):
        result = summarize_task_memory(
            project={
                "id": "prj_2",
                "status": "completed",
                "current_stage": "close",
                "request_text": "collect evidence",
                "mode": "one_shot",
                "risk_level": "low",
                "summary": None,
            },
            playbook_name=None,
            targets=[],
            assets=[],
            evidence=[],
            validations=[],
        )

        self.assertIn("playbook=none", result["summary"])
        self.assertEqual(result["metadata"]["validation_status"], None)
        self.assertEqual(result["metadata"]["playbook_name"], None)


if __name__ == "__main__":
    unittest.main()
