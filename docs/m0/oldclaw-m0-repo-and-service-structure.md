# docs/m0/oldclaw-m0-repo-and-service-structure.md

# Repository & Service Structure (M0 Reference)

```
oldclaw/
├─ apps/
│   ├─ manager-api/      # FastAPI entrypoint, REST façade
│   ├─ master-service/   # Review / Re‑plan / Escalation service
│   ├─ subagent-runtime/ # Lightweight HTTP API for health, capabilities, A2A run
│   ├─ scheduler-worker/ # Background poller for `schedules`
│   └─ watch-worker/     # Background processor for `watch_jobs`
├─ docs/m0/               # M0 설계 문서 (본 디렉터리)
├─ migrations/            # Flyway‑like SQL 마이그레이션 (초기 스키마)
├─ packages/
│   └─ pi_adapter/        # pi runtime 과의 어댑터 계층 (runtime, tools, sessions …)
├─ schemas/                # JSON‑Schema 기반 API 계약 및 Registry 스키마
├─ seed/                   # 초기 registry 데이터 (Tool, Skill, Playbook, Policy)
├─ tests/                  # 테스트 스위트 (현재 placeholder)
└─ README.md
```

## 서비스 간 의존 방향
- **Manager API** → `packages/core`, `packages/pi_adapter` (ToolBridge 사용) → DB (via core services)
- **Master Service** → `packages/policy_engine` (향후) → DB
- **SubAgent Runtime** → `packages/pi_adapter/runtime` (세션 관리) → pi runtime (외부) – **읽기 전용**
- **Scheduler / Watch Workers** → DB (읽기) → `packages/core` (JobRun / WatchJob 생성) → `apps/manager-api` (엔드포인트 트리거) 

**의존성 규칙**
- 하위 서비스는 상위 서비스에 직접 의존하지 않는다. 모두 DB와 공통 `core` 패키지를 통해 데이터 교환.
- `pi_adapter` 는 **외부** pi 엔진에만 의존하고, OldClaw 내부 로직에 절대 침투하지 않는다.

---
*임의 적용*: 일부 디렉터리 구조는 추후 M1 단계에서 세부 패키지로 재구성될 수 있습니다.*
