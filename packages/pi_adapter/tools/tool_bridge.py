from packages.pi_adapter.contracts import ToolCallRequest, ToolCallResponse
from packages.pi_adapter.tools import normalize_tool_names


class PiToolBridge:
    """
    Translate OldClaw tool selections into pi CLI arguments.

    This bridge does not implement OldClaw business logic.
    It only converts the desired tool set into CLI flags.
    """

    def build_cli_args(self, request: ToolCallRequest) -> ToolCallResponse:
        tool_names = normalize_tool_names(request.tool_names)
        if not tool_names:
            return ToolCallResponse(cli_args=[])

        return ToolCallResponse(cli_args=["--tools", ",".join(tool_names)])
