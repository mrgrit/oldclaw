import unittest
from unittest.mock import patch

from packages.policy_engine import evaluate_project_policy


class PolicyEngineUnitTest(unittest.TestCase):
    def test_allows_default_targeted_project(self):
        with patch("packages.policy_engine.get_project_record", return_value={"risk_level": "medium", "mode": "one_shot"}), patch(
            "packages.policy_engine.get_project_playbooks",
            return_value=[{"playbook": {"name": "diagnose_web_latency"}}],
        ), patch(
            "packages.policy_engine.get_project_targets",
            return_value=[{"target": {"id": "tgt_1"}}],
        ):
            decision = evaluate_project_policy("prj_allow")

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.policy_name, "default_allow")

    def test_denies_sensitive_playbook_with_approval_requirement(self):
        with patch("packages.policy_engine.get_project_record", return_value={"risk_level": "medium", "mode": "one_shot"}), patch(
            "packages.policy_engine.get_project_playbooks",
            return_value=[{"playbook": {"name": "onboard_new_linux_server"}}],
        ), patch(
            "packages.policy_engine.get_project_targets",
            return_value=[{"target": {"id": "tgt_1"}}],
        ):
            decision = evaluate_project_policy("prj_sensitive")

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_approval)
        self.assertEqual(decision.policy_name, "sensitive_playbook_requires_approval")

    def test_denies_missing_target_without_approval_path(self):
        with patch("packages.policy_engine.get_project_record", return_value={"risk_level": "medium", "mode": "one_shot"}), patch(
            "packages.policy_engine.get_project_playbooks",
            return_value=[{"playbook": {"name": "diagnose_web_latency"}}],
        ), patch(
            "packages.policy_engine.get_project_targets",
            return_value=[],
        ):
            decision = evaluate_project_policy("prj_missing_target")

        self.assertFalse(decision.allowed)
        self.assertFalse(decision.requires_approval)
        self.assertEqual(decision.policy_name, "target_required")


if __name__ == "__main__":
    unittest.main()
