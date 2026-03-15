from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class PiModelProfile:
    role: str
    provider: str
    model: str
    timeout_s: int
    temperature: float
    tool_calling_enabled: bool
    base_url: str
    api_key: str
    pi_command: str
    working_dir: str


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else default


def _int_env(name: str, default: int) -> int:
    raw = _env(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


DEFAULT_PROVIDER = _env("OLDCLAW_PI_PROVIDER", "ollama")
DEFAULT_BASE_URL = _env("OLDCLAW_PI_BASE_URL", "http://211.170.162.139:10534/v1")
DEFAULT_API_KEY = _env("OLDCLAW_PI_API_KEY", "ollama")
DEFAULT_TIMEOUT_S = _int_env("OLDCLAW_PI_DEFAULT_TIMEOUT_S", 120)
DEFAULT_COMMAND = _env("OLDCLAW_PI_COMMAND", "pi")
DEFAULT_WORKING_DIR = _env("OLDCLAW_PI_WORKING_DIR", "")

MODEL_PROFILES: dict[str, PiModelProfile] = {
    "manager": PiModelProfile(
        role="manager",
        provider=DEFAULT_PROVIDER,
        model=_env("OLDCLAW_PI_MANAGER_MODEL", "gpt-oss:120b"),
        timeout_s=DEFAULT_TIMEOUT_S,
        temperature=0.2,
        tool_calling_enabled=True,
        base_url=DEFAULT_BASE_URL,
        api_key=DEFAULT_API_KEY,
        pi_command=DEFAULT_COMMAND,
        working_dir=DEFAULT_WORKING_DIR,
    ),
    "master": PiModelProfile(
        role="master",
        provider=DEFAULT_PROVIDER,
        model=_env("OLDCLAW_PI_MASTER_MODEL", "gpt-oss:120b"),
        timeout_s=DEFAULT_TIMEOUT_S,
        temperature=0.1,
        tool_calling_enabled=True,
        base_url=DEFAULT_BASE_URL,
        api_key=DEFAULT_API_KEY,
        pi_command=DEFAULT_COMMAND,
        working_dir=DEFAULT_WORKING_DIR,
    ),
    "subagent": PiModelProfile(
        role="subagent",
        provider=DEFAULT_PROVIDER,
        model=_env("OLDCLAW_PI_SUBAGENT_MODEL", "gpt-oss:120b"),
        timeout_s=DEFAULT_TIMEOUT_S,
        temperature=0.1,
        tool_calling_enabled=True,
        base_url=DEFAULT_BASE_URL,
        api_key=DEFAULT_API_KEY,
        pi_command=DEFAULT_COMMAND,
        working_dir=DEFAULT_WORKING_DIR,
    ),
}


def get_model_profile(role: str) -> PiModelProfile:
    if role not in MODEL_PROFILES:
        raise KeyError(f"Unknown pi model profile role: {role}")
    return MODEL_PROFILES[role]
