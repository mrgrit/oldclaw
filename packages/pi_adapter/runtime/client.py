# packages/pi_adapter/runtime/client.py
"""Runtime client for pi engine.

In M0 this is a stub that raises NotImplementedError. In M1 it will wrap the real SDK.
"""

class PiRuntime:
    def __init__(self, model_profile: str):
        self.model_profile = model_profile
        # TODO: Initialize real pi SDK client based on model_profile
        raise NotImplementedError("PiRuntime client not implemented in M0")
