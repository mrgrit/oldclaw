# packages/pi_adapter/tools/tool_bridge.py
"""Concrete tool bridge implementations.

Each tool class should inherit from `BaseTool` and implement `execute`.
In M0 they raise NotImplementedError.
"""

from . import BaseTool

class RunCommandTool(BaseTool):
    def execute(self, command: str, timeout: int = 60):
        raise NotImplementedError("RunCommandTool execution not implemented in M0")

# Additional tool classes can be added here following the same pattern.
