import unittest

from packages.approval_engine import build_approval_request, is_approval_override_active
from packages.policy_engine import PolicyDecision


class ApprovalEngineUnitTest(unittest.TestCase):
    def test_build_approval_request_uses_policy_fields(self):
        decision = PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason="sensitive playbook requires approval",
            policy_name="sensitive_playbook_requires_approval",
            risk_level="medium",
            playbook_name="onboard_new_linux_server",
            target_count=1,
            mode="one_shot",
        )
        payload = build_approval_request("prj_1", decision)

        self.assertEqual(payload["project_id"], "prj_1")
        self.assertEqual(payload["policy_name"], "sensitive_playbook_requires_approval")
        self.assertEqual(payload["playbook_name"], "onboard_new_linux_server")
        self.assertEqual(payload["status"], "approval_required")

    def test_is_approval_override_active_only_for_approved_status(self):
        self.assertTrue(is_approval_override_active({"status": "approved"}))
        self.assertFalse(is_approval_override_active({"status": "approval_required"}))
        self.assertFalse(is_approval_override_active(None))


if __name__ == "__main__":
    unittest.main()
