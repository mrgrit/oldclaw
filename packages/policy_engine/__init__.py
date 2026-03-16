from dataclasses import dataclass
from typing import Any

from packages.project_service import (
    get_project_playbooks,
    get_project_record,
    get_project_targets,
)


SENSITIVE_PLAYBOOKS = {
    "monitor_siem_and_raise_incident",
    "onboard_new_linux_server",
    "tune_siem_noise",
}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    policy_name: str
    risk_level: str
    playbook_name: str | None
    target_count: int
    mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "reason": self.reason,
            "policy_name": self.policy_name,
            "risk_level": self.risk_level,
            "playbook_name": self.playbook_name,
            "target_count": self.target_count,
            "mode": self.mode,
        }


class PolicyDeniedError(Exception):
    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


def evaluate_project_policy(project_id: str) -> PolicyDecision:
    project = get_project_record(project_id)
    playbooks = get_project_playbooks(project_id)
    targets = get_project_targets(project_id)

    playbook_name = playbooks[0]["playbook"]["name"] if playbooks else None
    risk_level = str(project.get("risk_level") or "medium")
    mode = str(project.get("mode") or "one_shot")
    target_count = len(targets)

    if mode == "continuous":
        return PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason="continuous mode requires approval before execution",
            policy_name="continuous_requires_approval",
            risk_level=risk_level,
            playbook_name=playbook_name,
            target_count=target_count,
            mode=mode,
        )

    if risk_level in {"high", "critical"}:
        return PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason=f"{risk_level} risk project requires approval before execution",
            policy_name="high_risk_requires_approval",
            risk_level=risk_level,
            playbook_name=playbook_name,
            target_count=target_count,
            mode=mode,
        )

    if playbook_name in SENSITIVE_PLAYBOOKS:
        return PolicyDecision(
            allowed=False,
            requires_approval=True,
            reason=f"playbook {playbook_name} requires approval before execution",
            policy_name="sensitive_playbook_requires_approval",
            risk_level=risk_level,
            playbook_name=playbook_name,
            target_count=target_count,
            mode=mode,
        )

    if target_count == 0:
        return PolicyDecision(
            allowed=False,
            requires_approval=False,
            reason="at least one target must be linked before execution",
            policy_name="target_required",
            risk_level=risk_level,
            playbook_name=playbook_name,
            target_count=target_count,
            mode=mode,
        )

    return PolicyDecision(
        allowed=True,
        requires_approval=False,
        reason="policy check passed",
        policy_name="default_allow",
        risk_level=risk_level,
        playbook_name=playbook_name,
        target_count=target_count,
        mode=mode,
    )


def enforce_project_policy(project_id: str) -> PolicyDecision:
    decision = evaluate_project_policy(project_id)
    if not decision.allowed:
        raise PolicyDeniedError(decision)
    return decision
