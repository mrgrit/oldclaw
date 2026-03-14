# OldClaw M0 Registry Specification

## 1. 문서 목적

이 문서는 OldClaw의 registry 계층에서 **Tool / Skill / Playbook**을 어떻게 구분하고, 어떤 메타데이터와 계약을 가져야 하는지 정의한다.  
이 문서는 단순 예시 모음이 아니라, 이후 registry_service와 playbook execution, validation, policy binding이 흔들리지 않도록 하는 **기준 문서**다.

---

## 2. 핵심 원칙

OldClaw는 반드시 다음 구조를 유지한다.

- **Tool** = primitive
- **Skill** = reusable capability
- **Playbook** = orchestrated procedure

이 구분이 무너지면, 신규 업무가 들어올 때마다 코어를 수정하게 되고, registry 기반 확장이라는 설계 목표가 깨진다.

---

## 3. Tool 정의

Tool은 가장 작은 원자 기능이다.

예:
- run_command
- read_file
- write_file
- restart_service
- fetch_log
- query_metric

### Tool의 역할
- 실행 단위를 제공한다.
- skill이 사용하는 실제 primitive다.
- 직접적인 shell / file / API / metric / service interaction을 담당한다.

### Tool이 가져야 하는 메타데이터
- id
- name
- version
- description
- runtime_type
- risk_level
- input_schema_ref
- output_schema_ref
- timeouts
- policy_tags
- enabled

### Tool의 금지사항
- 여러 단계를 묶은 절차를 가지면 안 된다.
- 특정 업무 시나리오 전체를 품으면 안 된다.
- playbook 수준의 실패 정책을 가지면 안 된다.

---

## 4. Skill 정의

Skill은 재사용 가능한 능력이다.

예:
- probe_linux_host
- collect_web_latency_facts
- check_tls_cert
- analyze_wazuh_alert_burst
- monitor_disk_growth
- summarize_incident_timeline

### Skill의 역할
- 하나의 재사용 가능한 운영 능력을 정의한다.
- 내부적으로 여러 tool을 사용할 수 있다.
- validation hint와 evidence expectation을 가질 수 있다.
- 그러나 전체 업무 절차 전체를 가져서는 안 된다.

### Skill이 가져야 하는 메타데이터
- id
- name
- version
- category
- description
- input_schema_ref
- output_schema_ref
- required_tools
- optional_tools
- default_validation
- policy_hint
- evidence_expectations
- enabled

### Skill의 금지사항
- 전체 incident 처리 절차를 모두 넣지 마라.
- playbook처럼 approval gate, report, branching logic 전체를 품지 마라.
- shell command 나열 자체를 skill 본문으로 두지 마라.

---

## 5. Playbook 정의

Playbook은 skill과 validation/report 단계를 조합한 절차다.

예:
- diagnose_web_latency
- onboard_new_linux_server
- tune_siem_noise
- nightly_health_baseline_check
- monitor_siem_and_raise_incident

### Playbook의 역할
- step sequence를 정의한다.
- 실행 모드(one_shot / batch / continuous)를 명시한다.
- 실패 시 행동(retry, replan, approval request 등)을 정의한다.
- policy binding과 asset scope expectations를 가진다.

### Playbook이 가져야 하는 메타데이터
- id
- name
- version
- category
- execution_mode
- description
- input_schema_ref
- output_schema_ref
- dry_run_supported
- explain_supported
- default_risk_level
- required_asset_roles
- steps
- failure_policy
- policy_bindings
- enabled

### Playbook의 금지사항
- shell command를 직접 steps에 넣지 마라.
- skill 없이 command 나열로 절차를 구성하지 마라.
- 업무별 예외 로직을 core graph에 박아 넣지 마라.

---

## 6. Registry 파일 구조 원칙

Registry 관련 파일은 최소 다음 구조를 유지한다.

- `schemas/registry/tools/`
- `schemas/registry/skills/`
- `schemas/registry/playbooks/`
- `seed/tools/`
- `seed/skills/`
- `seed/playbooks/`
- `seed/policies/`

### 구조 원칙
- schema는 계약
- seed는 초기 탑재 데이터
- schemas와 seed의 naming은 일관되어야 한다
- input/output schema ref는 실제 존재하는 파일을 가리켜야 한다

---

## 7. Versioning 원칙

각 registry 객체는 version을 가져야 한다.

### 목적
- 변경 이력 추적
- playbook 호환성 유지
- 정책 바인딩 변경 추적
- 향후 dry-run / explain mode와의 정합성 확보

### M0 기준
M0에서는 단순 semantic version 문자열로 시작한다.  
version resolution logic은 M1 이후 구현 가능하되, version 필드는 이번 단계에서 반드시 고정한다.

---

## 8. Policy Binding 원칙

Registry 객체는 policy/approval와 느슨하게 결합해야 한다.

### Tool
- policy_tags 중심

### Skill
- policy_hint 중심

### Playbook
- policy_bindings 중심

즉, policy engine은 registry를 참고하되 registry 객체에 직접 business policy logic을 박아 넣지 않는다.

---

## 9. Validation / Evidence 연계 원칙

Registry는 validation과 evidence를 염두에 두고 정의한다.

### Tool
- output schema 보장

### Skill
- evidence expectation
- validation hint

### Playbook
- validation step
- failure policy
- report step

이 구조를 통해 OldClaw는 evidence-first / validation-gated completion 구조를 유지한다.

---

## 10. M0에서 포함하는 최소 seed 범위

### Tools
- run_command
- read_file
- write_file
- restart_service
- fetch_log
- query_metric

### Skills
- probe_linux_host
- collect_web_latency_facts
- check_tls_cert
- analyze_wazuh_alert_burst
- monitor_disk_growth
- summarize_incident_timeline

### Playbooks
- diagnose_web_latency
- onboard_new_linux_server
- tune_siem_noise
- nightly_health_baseline_check
- monitor_siem_and_raise_incident

---

## 11. 이번 M0에서 확정된 것과 다음 단계로 넘긴 것

### 이번 M0에서 확정
- Tool / Skill / Playbook 경계
- registry 파일 구조
- 최소 seed 범위
- version/policy/evidence 연계 원칙

### M1 이후 구현
- registry loader 실제 구현
- registry version resolver
- compatibility validator
- policy binding evaluator
- playbook composition execution engine

---

## 12. 임의 적용

이번 M0에서는 YAML seed + JSON schema 조합을 유지한다.  
이는 사람이 읽기 쉬운 seed와 기계 검증 가능한 schema를 동시에 만족시키기 위한 결정이다.

이 임의 적용은 구조 원칙을 깨지 않는 한, **M0 기준선 고정을 위한 구현 편의**다.
