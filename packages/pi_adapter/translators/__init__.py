import os
import json
from typing import Any


def build_prompt(prompt: str, context: dict[str, Any] | None = None) -> str:
    if not context:
        return prompt

    context_text = json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True)
    return (
        "OldClaw execution context:\n"
        f"{context_text}\n\n"
        "User prompt:\n"
        f"{prompt}"
    )


def normalize_output(stdout: str, stderr: str, exit_code: int) -> dict[str, Any]:
    return {
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
        "exit_code": exit_code,
    }
