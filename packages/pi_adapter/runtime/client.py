from dataclasses import dataclass
from typing import Any


@dataclass
class PiRuntimeConfig:
    model_profile: str
    session_mode: str
    timeout_s: int


class PiRuntimeClient:
    """
    Boundary adapter between OldClaw and the external pi runtime.

    This class exists to make the integration point explicit.
    OldClaw orchestration logic must not be implemented here.
    Asset, project, policy, evidence, and validation domain logic must stay
    outside the pi adapter layer.
    """

    def __init__(self, config: PiRuntimeConfig) -> None:
        self.config = config

    def open_session(self, session_name: str) -> str:
        raise NotImplementedError(
            "pi runtime session integration is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )

    def invoke_model(self, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError(
            "pi runtime model invocation is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )

    def close_session(self, session_id: str) -> None:
        raise NotImplementedError(
            "pi runtime session closing is not implemented in M0. "
            "This boundary is fixed here and will be implemented in M1."
        )
