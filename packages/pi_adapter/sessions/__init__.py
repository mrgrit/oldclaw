from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class PiSession:
    session_id: str
    session_name: str
    role: str
    provider: str
    model: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SessionRegistry:
    def __init__(self) -> None:
        self._sessions: dict[str, PiSession] = {}

    def create(self, session_name: str, role: str, provider: str, model: str) -> PiSession:
        session = PiSession(
            session_id=f"pi-session-{uuid4()}",
            session_name=session_name,
            role=role,
            provider=provider,
            model=model,
        )
        self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> PiSession | None:
        return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def list_ids(self) -> list[str]:
        return list(self._sessions.keys())
