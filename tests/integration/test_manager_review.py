import unittest
from uuid import uuid4

from packages.approval_engine import create_approval_request_record, list_project_approvals
from packages.policy_engine import PolicyDecision
from packages.project_service import get_master_reviews_for_project
from tests.integration.support import (
    ManagerIntegrationTestCase,
    build_master_runner,
)


class ManagerReviewIntegrationTest(ManagerIntegrationTestCase):

    def test_sensitive_playbook_requires_approval_then_allows_rerun(self):
        prefix = f"appr_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="onboard_new_linux_server",
            request_text="integration approval check",
            mode="one_shot",
        )

        denied = self.client.post(f"/projects/{project_id}/run/auto")
        self.assertEqual(denied.status_code, 403)
        denied_payload = denied.json()["detail"]
        self.assertEqual(denied_payload["approval_request"]["status"], "approval_required")

        approvals_response = self.client.get(f"/projects/{project_id}/approvals")
        approvals_response.raise_for_status()
        approvals = approvals_response.json()["items"]
        self.assertEqual(len(approvals), 1)

        approval_id = approvals[0]["id"]
        approve_response = self.client.post(
            f"/projects/{project_id}/approvals/{approval_id}/approve",
            json={"approver_id": "integration-reviewer"},
        )
        approve_response.raise_for_status()
        self.assertEqual(approve_response.json()["approval"]["status"], "approved")

        rerun = self.client.post(f"/projects/{project_id}/run/auto")
        rerun.raise_for_status()
        rerun_payload = rerun.json()

        self.assertEqual(rerun_payload["closed"]["current_stage"], "close")
        self.assertEqual(rerun_payload["policy"]["approval_status"], "approved")

    def test_duplicate_approval_requests_are_reused_for_same_policy(self):
        prefix = f"dupapr_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="onboard_new_linux_server",
            request_text="integration duplicate approval request check",
            mode="one_shot",
        )

        denied_first = self.client.post(f"/projects/{project_id}/run/auto")
        self.assertEqual(denied_first.status_code, 403)
        denied_second = self.client.post(f"/projects/{project_id}/run/auto")
        self.assertEqual(denied_second.status_code, 403)

        approvals = self.client.get(f"/projects/{project_id}/approvals")
        approvals.raise_for_status()
        items = approvals.json()["items"]
        self.assertEqual(len(items), 1)
        self.assertEqual(
            denied_first.json()["detail"]["approval_request"]["approval_id"],
            denied_second.json()["detail"]["approval_request"]["approval_id"],
        )

    def test_create_approval_request_record_reuses_existing_pending_row(self):
        prefix = f"reuseapr_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="onboard_new_linux_server",
            request_text="integration direct approval reuse check",
            mode="one_shot",
        )

        decision = PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason="playbook onboard_new_linux_server requires approval before execution",
            policy_name="sensitive_playbook_requires_approval",
            risk_level="medium",
            playbook_name="onboard_new_linux_server",
            target_count=1,
            mode="one_shot",
        )
        first = create_approval_request_record(project_id, decision)
        second = create_approval_request_record(project_id, decision)

        self.assertEqual(second["id"], first["id"])
        approvals = list_project_approvals(project_id)
        self.assertEqual(len(approvals), 1)

    def test_master_review_returns_needs_replan_while_approval_is_pending(self):
        prefix = f"pending_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="onboard_new_linux_server",
            request_text="integration approval pending review",
            mode="one_shot",
        )

        denied = self.client.post(f"/projects/{project_id}/run/auto")
        self.assertEqual(denied.status_code, 403)

        review_response = self.client.post(
            f"/projects/{project_id}/run/auto/review",
            json={"reviewer_id": "integration-master", "comments": "pending approval review"},
        )
        self.assertEqual(review_response.status_code, 403)

        master_runner = build_master_runner()
        master_payload = master_runner(
            project_id,
            {
                "project_id": project_id,
                "reviewer_id": "integration-master",
                "comments": "manual pending review",
            },
        )
        self.assertEqual(master_payload["review"]["status"], "needs_replan")
        self.assertEqual(master_payload["context"]["approval_count"], 1)

    def test_run_auto_review_handoff_returns_master_approved(self):
        prefix = f"handoff_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="integration master handoff",
            mode="one_shot",
        )

        response = self.client.post(
            f"/projects/{project_id}/run/auto/review",
            json={"reviewer_id": "integration-master", "comments": "auto review"},
        )
        response.raise_for_status()
        payload = response.json()

        self.assertEqual(payload["closed"]["current_stage"], "close")
        self.assertEqual(payload["validated"]["validation_run"]["status"], "passed")
        self.assertEqual(payload["master_review"]["review"]["status"], "approved")
        self.assertGreaterEqual(payload["master_review"]["context"]["evidence_count"], 1)

    def test_master_reviews_are_appended_in_order(self):
        prefix = f"appendrvw_{uuid4().hex[:8]}"
        project_id, _, _, _ = self.create_linked_project(
            prefix=prefix,
            playbook_name="diagnose_web_latency",
            request_text="integration master review append check",
            mode="one_shot",
        )

        response = self.client.post(
            f"/projects/{project_id}/run/auto/review",
            json={"reviewer_id": "integration-master", "comments": "first review"},
        )
        response.raise_for_status()
        first_review = response.json()["master_review"]["review"]

        master_runner = build_master_runner()
        second_payload = master_runner(
            project_id,
            {
                "project_id": project_id,
                "reviewer_id": "integration-master-2",
                "comments": "second review",
            },
        )
        second_review = second_payload["review"]

        reviews = get_master_reviews_for_project(project_id)
        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0]["id"], first_review["id"])
        self.assertEqual(reviews[1]["id"], second_review["id"])
        self.assertEqual(reviews[0]["status"], "approved")
        self.assertEqual(reviews[1]["status"], "approved")


if __name__ == "__main__":
    unittest.main()
