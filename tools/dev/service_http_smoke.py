import subprocess
import sys
import time

import requests


SERVICES = [
    {
        "name": "manager",
        "module": "apps.manager-api.src.main:app",
        "port": 18080,
        "health_path": "/health",
        "runtime_payload": {"prompt": "Reply with exactly: OK", "role": "manager"},
    },
    {
        "name": "master",
        "module": "apps.master-service.src.main:app",
        "port": 18081,
        "health_path": "/health",
        "runtime_payload": {"prompt": "Reply with exactly: OK", "role": "master"},
    },
    {
        "name": "subagent",
        "module": "apps.subagent-runtime.src.main:app",
        "port": 18082,
        "health_path": "/health",
        "runtime_payload": {"prompt": "Reply with exactly: OK", "role": "subagent"},
    },
]


def wait_for_health(base_url: str, health_path: str, timeout_s: int = 20) -> dict:
    started = time.time()
    last_error = None
    while time.time() - started < timeout_s:
        try:
            response = requests.get(f"{base_url}{health_path}", timeout=3)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"health check failed for {base_url}{health_path}: {last_error}")


def invoke_runtime(base_url: str, payload: dict) -> dict:
    response = requests.post(f"{base_url}/runtime/invoke", json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def main() -> int:
    processes: list[subprocess.Popen] = []
    try:
        for service in SERVICES:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    service["module"],
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(service["port"]),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            processes.append(process)
        for service in SERVICES:
            base_url = f"http://127.0.0.1:{service['port']}"
            health = wait_for_health(base_url, service["health_path"])
            print(f"{service['name'].upper()}_HEALTH:", health)
            time.sleep(0.5)

        for service in SERVICES:
            base_url = f"http://127.0.0.1:{service['port']}"
            result = invoke_runtime(base_url, service["runtime_payload"])
            print(f"{service['name'].upper()}_RUNTIME_STATUS:", result["status"])
            print(f"{service['name'].upper()}_RUNTIME_STDOUT:", result["result"]["stdout"])
            print(f"{service['name'].upper()}_RUNTIME_EXIT_CODE:", result["result"]["exit_code"])
        return 0
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
