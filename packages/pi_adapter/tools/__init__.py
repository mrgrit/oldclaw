from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSelection:
    names: list[str]


class ToolBridgeError(Exception):
    pass


def normalize_tool_names(tool_names: list[str] | None) -> list[str]:
    if not tool_names:
        return []

    normalized: list[str] = []
    for name in tool_names:
        cleaned = name.strip()
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized
