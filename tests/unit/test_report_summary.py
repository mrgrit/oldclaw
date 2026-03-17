import unittest

from packages.project_service import summarize_project_report


class ReportSummaryUnitTest(unittest.TestCase):
    def test_report_summary_counts_assets_evidence_and_skill_fragments(self):
        summary = summarize_project_report(
            project_id="prj_1",
            playbook_name="diagnose_web_latency",
            target_name="web-target",
            asset_count=2,
            evidence=[
                {"id": "ev_1", "evidence_type": "execution_log"},
                {"id": "ev_2", "evidence_type": "report_fragment"},
                {"id": "ev_3", "evidence_type": "report_fragment"},
            ],
        )

        self.assertIn("playbook=diagnose_web_latency", summary)
        self.assertIn("target=web-target", summary)
        self.assertIn("assets=2", summary)
        self.assertIn("evidence=3", summary)
        self.assertIn("skill_fragments=2", summary)

    def test_report_summary_handles_empty_evidence(self):
        summary = summarize_project_report(
            project_id="prj_2",
            playbook_name="none",
            target_name="none",
            asset_count=0,
            evidence=[],
        )

        self.assertIn("assets=0", summary)
        self.assertIn("evidence=0", summary)
        self.assertIn("skill_fragments=0", summary)


if __name__ == "__main__":
    unittest.main()
