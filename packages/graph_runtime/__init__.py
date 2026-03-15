DEFAULT_MANAGER_STAGES = [
    "intake",
    "plan",
    "execute",
    "validate",
    "report",
    "close",
]

DEFAULT_STAGE_TRANSITIONS = {
    "intake": "plan",
    "plan": "execute",
    "execute": "validate",
    "validate": "report",
    "report": "close",
    "close": None,
}


class GraphRuntimeError(Exception):
    pass


def get_next_stage(stage: str) -> str | None:
    if stage not in DEFAULT_STAGE_TRANSITIONS:
        raise GraphRuntimeError(f"Unknown stage: {stage}")
    return DEFAULT_STAGE_TRANSITIONS[stage]


def require_transition(current_stage: str, next_stage: str) -> None:
    expected = get_next_stage(current_stage)
    if expected != next_stage:
        raise GraphRuntimeError(
            f"Invalid stage transition: {current_stage} -> {next_stage} (expected {expected})"
        )


def build_minimal_project_graph() -> dict[str, object]:
    return {
        "stages": list(DEFAULT_MANAGER_STAGES),
        "transitions": dict(DEFAULT_STAGE_TRANSITIONS),
    }
