# OldClaw

OldClaw is a **Control‑Plane Orchestration Platform** built on top of the **pi** runtime. This repository currently resides in **M0 – design lock & skeleton** stage. All core data models, service boundaries, registry specifications and API contracts are defined and ready for concrete implementation in the upcoming M1 phase.

## Repository Structure
```
oldclaw/
├─ apps/                # Service entrypoints (FastAPI)
├─ docs/m0/            # M0 설계 문서 (baseline, DB schema, registry spec, etc.)
├─ migrations/         # Flyway‑like SQL migrations (human‑readable)
├─ packages/pi_adapter # pi runtime 과의 어댑터 계층 (runtime, tools, sessions …)
├─ schemas/            # JSON‑Schema 기반 API 계약 및 Registry 스키마
├─ seed/               # 초기 registry 데이터 (Tool, Skill, Playbook, Policy)
└─ README.md           # This overview
```

## 현재 단계
**M0 설계 고정 + skeleton 정리**: 설계, DB 스키마, 레지스트리 사양, API 계약이 고정됐으며, 코드베이스는 FastAPI 스켈레톤과 `pi_adapter` 경계만 포함합니다.

## 다음 단계
**M1 pi Runtime Adapter**: 실제 pi SDK 연동, 세션 관리, 모델 호출 등을 구현할 예정입니다.

---
*이 레포는 설계/계약/스켈레톤 기준선이며, 프로덕션 레디 상태가 아닙니다.*
