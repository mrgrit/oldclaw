from packages.pi_adapter.runtime import PiRuntimeClient, PiRuntimeConfig


def main() -> int:
    client = PiRuntimeClient(PiRuntimeConfig(default_role="manager"))
    session_id = client.open_session("smoke-test")
    result = client.invoke_model(
        "Reply with exactly: OK",
        {
            "session_id": session_id,
            "role": "manager",
        },
    )
    print("SESSION_ID:", session_id)
    print("STDOUT:", result["stdout"])
    print("EXIT_CODE:", result["exit_code"])
    client.close_session(session_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
