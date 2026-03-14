# WORK-17

## 1. 작업 정보
- 작업 이름: M1 코드 주입 1차 / pi CLI Wrapper Adapter 적용
- 현재 브랜치: main
- 현재 HEAD 커밋: da51c7f
- 작업 시각: 2026-03-15 02:30:00 UTC

## 2. 이번 작업에서 수정한 파일
- packages/pi_adapter/runtime/client.py
- packages/pi_adapter/runtime/__init__.py
- packages/pi_adapter/tools/__init__.py
- packages/pi_adapter/tools/tool_bridge.py
- packages/pi_adapter/sessions/__init__.py
- packages/pi_adapter/model_profiles/__init__.py
- packages/pi_adapter/translators/__init__.py
- packages/pi_adapter/contracts/__init__.py
- .env.example
- docs/m1/oldclaw-m1-plan.md
- docs/m1/oldclaw-m1-completion-report.md
- tools/dev/pi_runtime_smoke.py
- docs/verification/WORK-17.md

## 3. 실행한 명령 목록
```
mkdir -p docs/m1
mkdir -p tools/dev
python3 -m compileall apps packages tools
PYTHONPATH=. python3 tools/dev/pi_runtime_smoke.py
git status --short
git add packages/pi_adapter/runtime/client.py
git add packages/pi_adapter/runtime/__init__.py
git add packages/pi_adapter/tools/__init__.py
git add packages/pi_adapter/tools/tool_bridge.py
git add packages/pi_adapter/sessions/__init__.py
git add packages/pi_adapter/model_profiles/__init__.py
git add packages/pi_adapter/translators/__init__.py
git add packages/pi_adapter/contracts/__init__.py
git add .env.example
git add docs/m1/oldclaw-m1-plan.md
git add docs/m1/oldclaw-m1-completion-report.md
git add tools/dev/pi_runtime_smoke.py
git add docs/verification/WORK-17.md
```

## 4. compileall 결과
- stdout: (truncated) Listing and compiling all *.py files under `apps`, `packages`, `tools` succeeded. No syntax errors reported.
- stderr: (none)
- exit code: 0

## 5. smoke test 결과
- 명령: `PYTHONPATH=. python3 tools/dev/pi_runtime_smoke.py`
- stdout:
```
SESSION_ID: pi-session-b166cf20-54e2-432b-8089-5d3e4749d0c7
STDOUT: OK
EXIT_CODE: 0
```
- stderr: (none)
- exit code: 0

## 6. 핵심 관찰점
- `open_session` 동작 여부: 성공 (session ID 반환)
- `invoke_model` 동작 여부: 성공 (`OK` 출력, exit_code 0)
- `close_session` 동작 여부: 성공 (session removed from registry)
- Ollama 성공 설정 재사용 여부: `packages/pi_adapter/model_profiles/__init__.py` 에서 기본값으로 Ollama provider / baseUrl / model 사용, smoke test에서 그대로 적용됨.
- 아직 남은 한계 (5 이하):
  1. 실제 remote session 종료 로직이 없음 (in‑memory만).
  2. Tool bridge는 `--tools` 플래그 생성만 지원, 실제 도구 실행 미구현.
  3. エラー 매핑 및 상세 로깅 부재.
  4. DB·state 연동 없이 메모리만 사용.
  5. 서비스 계층(manager/master/subagent)에서 아직 adapter 호출이 없으며, 증거(evidence) 저장 흐름과 연결되지 않음.

## 7. 미해결 사항
1. 실제 pi runtime 오류 상황에서의 상세 에러 전파 방식 정의 필요.
2. 장기 세션·히스토리 저장을 위한 DB 연동 설계 필요.
3. 현재 `tools` 디렉터리 비어 있어 향후 도구 구현 계획 수립 필요.
