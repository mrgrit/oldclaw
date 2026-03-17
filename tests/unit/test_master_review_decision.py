import unittest

from tests.integration.support import load_module


master_module = load_module(
    "oldclaw_master_review_unit",
    "apps/master-service/src/main.py",
)


class MasterReviewDecisionUnitTest(unittest.TestCase):
    def make_context(
        self,
        *,
        project_stage: str = "close",
        project_status: str = "completed",
        evidence_count: int = 1,
        validation_status: str | None = "passed",
        approval_status: str | None = None,
    ) -> dict:
        validations = [] if validation_status is None else [{"status": validation_status}]
        approvals = [] if approval_status is None else [{"status": approval_status}]
        return {
            "project": {
                "current_stage": project_stage,
                "status": project_status,
            },
            "report": None,
            "evidence": [{} for _ in range(evidence_count)],
            "validations": validations,
            "approvals": approvals,
            "latest_validation": validations[-1] if validations else None,
            "latest_approval": approvals[-1] if approvals else None,
        }

    def test_approved_when_validation_passed_and_project_closed(self):
        status, summary, findings = master_module._decide_review_status(self.make_context())
        self.assertEqual(status, "approved")
        self.assertIn("approved", summary.lower())
        self.assertEqual(findings["validation_status"], "passed")

    def test_needs_replan_when_approval_is_pending(self):
        status, summary, findings = master_module._decide_review_status(
            self.make_context(validation_status="passed", approval_status="approval_required")
        )
        self.assertEqual(status, "needs_replan")
        self.assertIn("approval", summary.lower())
        self.assertEqual(findings["approval_status"], "approval_required")

    def test_rejected_when_validation_failed(self):
        status, summary, findings = master_module._decide_review_status(
            self.make_context(validation_status="failed")
        )
        self.assertEqual(status, "rejected")
        self.assertIn("failed", summary.lower())
        self.assertEqual(findings["validation_status"], "failed")


if __name__ == "__main__":
    unittest.main()
