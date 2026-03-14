# OldClaw M1 Completion Report

## 1. 이번 단계에서 실제 반영한 것

- `packages/pi_adapter/runtime/client.py`
  - `pi` CLI subprocess wrapper 구현
- `packages/pi_adapter/runtime/__init__.py`
  - public export 정리
- `packages/pi_adapter/contracts/__init__.py`
  - session/model/tool contract dataclass 정의
- `packages/pi_adapter/sessions/__init__.py`
  - in-memory session registry 구현
- `packages/pi_adapter/model_profiles/__init__.py`
  - role별 profile/env 기반 설정 구현
- `packages/pi_adapter/tools/*`
  - tool selection → CLI flag 변환 구현
- `packages/pi_adapter/translators/__init__.py`
  - prompt/context 조합 및 output normalization 구현
- `.env.example`
  - Ollama 성공 설정 기준으로 갱신
- `tools/dev/pi_runtime_smoke.py`
  - open/invoke/close smoke test 추가

## 2. 이번 단계에서 고정된 사실

- 현재 OldClaw의 pi adapter는 Python-native SDK가 아니라 `pi` CLI wrapper 방식이다.
- 성공 기준 provider/model은 `ollama / gpt-oss:120b` 이다.
- `~/.pi/agent/models.json` 이 실제 설정 경로다.
- 비대화형 호출은 `-p` 플래그를 사용한다.

## 3. 한계

- 실제 remote session close가 아니라 OldClaw 내부 session metadata 제거 수준이다.
- tool bridge는 CLI `--tools` 플래그 생성까지만 구현되어 있다.
- manager/master/subagent 앱은 아직 adapter를 호출하지 않는다.
- evidence/validation/history 연계는 아직 없다.

## 4. 다음 단계로 넘기는 것

- manager service wiring
- adapter error → service error mapping
- actual tool usage integration
- DB/state transition 연동
- report/validation pipeline 연결
