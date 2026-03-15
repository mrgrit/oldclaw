from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionOpenRequest:
    session_name: str
    role: str


@dataclass
class SessionOpenResponse:
    session_id: str
    session_name: str
    role: str
    provider: str
    model: str


@dataclass
class ModelInvokeRequest:
    prompt: str
    session_id: str | None = None
    role: str = "manager"
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelInvokeResponse:
    session_id: str | None
    provider: str
    model: str
    command: list[str]
    stdout: str
    stderr: str
    exit_code: int


@dataclass
class ToolCallRequest:
    tool_names: list[str]


@dataclass
class ToolCallResponse:
    cli_args: list[str]


@dataclass
class PiAdapterErrorInfo:
    message: str
    command: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
