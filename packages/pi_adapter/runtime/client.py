import os
from dataclasses import dataclass
import subprocess
from typing import Any


from packages.pi_adapter.contracts import (
    ModelInvokeRequest,
    ModelInvokeResponse,
    PiAdapterErrorInfo,
    SessionOpenRequest,
    SessionOpenResponse,
)
from packages.pi_adapter.model_profiles import get_model_profile
from packages.pi_adapter.sessions import SessionRegistry
from packages.pi_adapter.tools.tool_bridge import PiToolBridge
from packages.pi_adapter.translators import build_prompt, normalize_output


class PiAdapterError(Exception):
    def __init__(self, error: PiAdapterErrorInfo) -> None:
        super().__init__(error.message)
        self.error = error


class PiRuntimeInvocationError(PiAdapterError):
    pass


@dataclass
class PiRuntimeConfig:
    default_role: str = "manager"


class PiRuntimeClient:
    """
    OldClaw-side wrapper over the external `pi` CLI runtime.

    This is a service-facing adapter. The implementation currently uses
    subprocess invocation of the `pi` CLI because pi-mono exposes a working
    Node/CLI runtime while Python-native bindings are not available.
    """

    def __init__(self, config: PiRuntimeConfig) -> None:
        self.config = config
        self.sessions = SessionRegistry()
        self.tool_bridge = PiToolBridge()

    def open_session(self, session_name: str, role: str | None = None) -> str:
        selected_role = role or self.config.default_role
        profile = get_model_profile(selected_role)
        session = self.sessions.create(
            session_name=session_name,
            role=selected_role,
            provider=profile.provider,
            model=profile.model,
        )
        response = SessionOpenResponse(
            session_id=session.session_id,
            session_name=session.session_name,
            role=session.role,
            provider=session.provider,
            model=session.model,
        )
        return response.session_id

    def invoke_model(self, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        request = ModelInvokeRequest(
            prompt=prompt,
            session_id=(context or {}).get("session_id"),
            role=(context or {}).get("role", self.config.default_role),
            context=context or {},
        )

        role = request.role or self.config.default_role
        profile = get_model_profile(role)
        session_id = request.session_id

        if session_id:
            session = self.sessions.get(session_id)
            if session is None:
                raise PiAdapterError(
                    PiAdapterErrorInfo(message=f"Unknown session id: {session_id}")
                )
            provider = session.provider
            model = session.model
        else:
            provider = profile.provider
            model = profile.model

        compiled_prompt = build_prompt(request.prompt, request.context)
        command = [
            profile.pi_command,
            "--provider",
            provider,
            "--model",
            model,
            "-p",
            compiled_prompt,
        ]

        tool_names = request.context.get("tool_names")
        if isinstance(tool_names, list):
            tool_args = self.tool_bridge.build_cli_args(
                request=self._tool_request(tool_names)
            )
            command.extend(tool_args.cli_args)

        env = os.environ.copy()
        env["OLDCLAW_PI_PROVIDER"] = provider
        env["OLDCLAW_PI_BASE_URL"] = profile.base_url
        env["OLDCLAW_PI_API_KEY"] = profile.api_key

        working_dir = profile.working_dir or None

        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=profile.timeout_s,
            cwd=working_dir,
            env=env,
        )

        normalized = normalize_output(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
        )

        response = ModelInvokeResponse(
            session_id=session_id,
            provider=provider,
            model=model,
            command=command,
            stdout=normalized["stdout"],
            stderr=normalized["stderr"],
            exit_code=normalized["exit_code"],
        )

        if response.exit_code != 0:
            raise PiRuntimeInvocationError(
                PiAdapterErrorInfo(
                    message="pi runtime invocation failed",
                    command=response.command,
                    stdout=response.stdout,
                    stderr=response.stderr,
                    exit_code=response.exit_code,
                )
            )

        return {
            "session_id": response.session_id,
            "provider": response.provider,
            "model": response.model,
            "command": response.command,
            "stdout": response.stdout,
            "stderr": response.stderr,
            "exit_code": response.exit_code,
        }

    def close_session(self, session_id: str) -> None:
        self.sessions.remove(session_id)

    @staticmethod
    def _tool_request(tool_names: list[str]):
        from packages.pi_adapter.contracts import ToolCallRequest

        return ToolCallRequest(tool_names=tool_names)
