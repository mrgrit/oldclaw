# OldClaw M1 Plan

## 1. 목적

M1의 목적은 pi runtime을 OldClaw에서 재사용 가능한 실행 엔진으로 캡슐화하는 것이다.

현재 pi는 Python SDK가 아니라 Node/CLI 중심으로 동작하므로, 이번 단계의 adapter는
OldClaw 내부에서 사용할 수 있는 Python 인터페이스를 제공하되 내부적으로는 `pi` CLI를 호출한다.

## 2. 이번 단계 구현 범위

- pi runtime wrapper client
- role별 model profile
- in-memory session registry
- tool bridge
- request/response contracts
- translator
- smoke test script

## 3. 구현 원칙

- OldClaw 비즈니스 로직을 pi_adapter 안에 넣지 않는다.
- subprocess 기반이라도 OldClaw 외부 계약은 service-facing interface로 유지한다.
- Ollama 성공 설정을 기본 기준선으로 사용한다.
- session은 현재 in-memory registry 수준으로 관리한다.
- explicit remote session close가 없는 만큼 OldClaw 쪽 session metadata만 관리한다.

## 4. 성공 기준

- Python에서 `PiRuntimeClient.open_session()` 호출 가능
- Python에서 `PiRuntimeClient.invoke_model()` 호출 가능
- Python에서 `PiRuntimeClient.close_session()` 호출 가능
- `pi --provider ollama --model gpt-oss:120b -p ...` 성공 경로를 adapter가 재사용
- smoke test가 최소 1회 성공

## 5. 다음 단계로 넘기는 것

- real project lifecycle 연결
- manager/master/subagent 서비스 wiring
- DB-backed session/history linkage
- tool result → evidence 저장 통합
- validation/report pipeline 연결
