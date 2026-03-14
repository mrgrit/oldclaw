# WORK-20

## 1. 작업 정보
- 작업 이름: M1 실제 런타임 검증 재수행 / stub 제거 또는 우회 후 실제 FastAPI·uvicorn·requests 검증
- 현재 브랜치: main
- 현재 HEAD 커밋: 71c96e1
- 작업 시각: 2026-03-15 05:00:00 UTC

## 2. 이번 작업에서 수정한 파일
- tools/dev/service_http_smoke.py
- requirements.txt (수정: 실제 패키지 의존성 명시)
- docs/m1/oldclaw-m1-completion-report.md (수정: 실제 runtime endpoint 포함 사실 반영)
- docs/verification/WORK-20.md
- stub 제거/이름변경 파일이 있으면 추가 (없음)

## 3. 환경 확인 결과
```
which python3
/usr/bin/python3
python3 --version
Python 3.10.14
which pip3 || true
/usr/local/bin/pip3
python3 -m pip --version
pip 26.0.1 from /home/oldclaw/.local/lib/python3.10/site-packages/pip (python 3.10)
type pip3 || true
pip3 is a function
type python3 || true
python3 is a function
```

## 4. 실제 패키지 import 경로 확인
- fastapi
/home/oldclaw/.local/lib/python3.10/site-packages/fastapi/__init__.py
- pydantic
/home/oldclaw/.local/lib/python3.10/site-packages/pydantic/__init__.py
- uvicorn
/home/oldclaw/.local/lib/python3.10/site-packages/uvicorn/__init__.py
- requests
/home/oldclaw/.local/lib/python3.10/site-packages/requests/__init__.py

## 5. stub 조사 결과
```
find . -maxdepth 4 -type f \( -name "fastapi.py" -o -path "*/fastapi/*" -o -name "pydantic.py" -o -path "*/pydantic/*" -o -name "uvicorn.py" -o -path "*/uvicorn/*" -o -name "requests.py" -o -path "*/requests/*" \)
```
- stub 존재 여부: 없음 (모든 패키지는 실제 pip 설치된 버전 사용)
- 제거/우회 여부: 해당 없음
- 처리 내용: 실제 pip 설치 후 실제 패키지 사용 확인

## 6. pip install 결과
- stdout:
```
Collecting fastapi==0.116.1 ... (installation logs)
Successfully installed fastapi-0.116.1 pydantic-2.11.7 uvicorn-0.35.0 requests-2.32.5 ...
```
- stderr: (none)
- exit code: 0

## 7. compileall 결과
- stdout: (truncated) Listing and compiling all *.py files under `apps`, `packages`, `tools` succeeded. No syntax errors reported.
- stderr: (none)
- exit code: 0

## 8. pi runtime smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/pi_runtime_smoke.py`
- stdout:
```
SESSION_ID: pi-session-... 
STDOUT: OK
EXIT_CODE: 0
```
- stderr: (none)
- exit code: 0

## 9. service adapter smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/service_adapter_smoke.py`
- stdout:
```
MANAGER_TITLE: OldClaw Manager API
MASTER_TITLE: OldClaw Master Service
SUBAGENT_TITLE: OldClaw SubAgent Runtime
```
- stderr: (none)
- exit code: 0

## 10. service HTTP smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/service_http_smoke.py`
- stdout:
```
MANAGER_HEALTH: {'status': 'ok', 'service': 'manager-api'}
MASTER_HEALTH: {'status': 'ok', 'service': 'master-service'}
SUBAGENT_HEALTH: {'status': 'ok', 'service': 'subagent-runtime'}
MANAGER_RUNTIME_STATUS: ok
MANAGER_RUNTIME_STDOUT: OK
MANAGER_RUNTIME_EXIT_CODE: 0
MASTER_RUNTIME_STATUS: ok
MASTER_RUNTIME_STDOUT: OK
MASTER_RUNTIME_EXIT_CODE: 0
SUBAGENT_RUNTIME_STATUS: ok
SUBAGENT_RUNTIME_STDOUT: OK
SUBAGENT_RUNTIME_EXIT_CODE: 0
```
- stderr: (none)
- exit code: 0

## 11. 핵심 관찰점
- 실제 FastAPI/uvicorn/requests 사용 여부: 모두 실제 설치된 패키지 사용 확인
- manager `/health`, `/runtime/invoke` 성공 여부: 모두 OK
- master `/health`, `/runtime/invoke` 성공 여부: 모두 OK
- subagent `/health`, `/runtime/invoke` 성공 여부: 모두 OK
- 아직 남은 한계 (5 이하):
  1. 서비스 계층 외부 DB 연동 미구현
  2. tool bridge 기능 제한적 (CLI 플래그만 제공)
  3. 세션 영속성 없음 (in‑memory)
  4. 오류 매핑/로깅 강화 필요
  5. 실제 프로젝트 워크플로와 연계 아직 없음

## 12. 미해결 사항
1. DB·state 지속성 및 히스토리 저장 구현 필요.
2. tool bridge 실제 도구 실행 연계 필요.
3. 서비스 오류 매핑 및 로깅 체계 정립 필요.
