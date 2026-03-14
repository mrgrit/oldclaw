# docs/m0/oldclaw-m0-registry-spec.md

# Registry Specification (M0)

## 1. 개념 정의
- **Tool** – 저수준 시스템/SDK 호출. 반드시 **단일 원자 동작**만 수행한다. (예: `run_command`, `read_file`)
- **Skill** – 하나 이상의 Tool 조합 + 입력 검증 + 증거(evidence) 기대 정의. **비즈니스 로직**은 여기서 허용되지 않는다.
- **Playbook** – Skill 순차 실행, 흐름 제어(조건, 리트라이, 실패 정책), 정책 바인딩. **Tool** 직접 호출 금지.

## 2. 경계 및 금지사항
| 레이어 | 허용 행동 | 금지 행동 |
|--------|----------|-----------|
| **Tool** | 시스템 명령, 파일 I/O, 서비스 API 호출 | DB 쓰기, 비즈니스 의사결정, 복합 트랜잭션 |
| **Skill** | Tool 호출, 입력 검증, 증거 메타데이터 기록 | 직접 DB 조작, 외부 서비스와 직접 통신 (Tool을 통해서만) |
| **Playbook** | Skill 순서 정의, 조건/리트라이, 정책 바인딩 | Tool 직접 호출, 직렬화되지 않은 상태 유지 |

## 3. 메타데이터 필수 항목
- `id` : `<name>:<semver>` (예: `run_command:1.0`)
- `name`, `version`, `description`
- `input_schema_ref` / `output_schema_ref` – `schemas/registry/*` 경로
- **Tool** : `runtime_type`, `policy_tags`
- **Skill** : `required_tools` (list), `optional_tools` (list), `default_validation`, `evidence_expectations`
- **Playbook** : `required_asset_roles`, `execution_mode` (one_shot|batch|continuous), `failure_policy`, `policy_bindings`

## 4. 설계 결정 (M0 고정)
- Tool 은 **local** 혹은 **remote** (runtime_type) 으로 구분한다.
- Skill 은 **required_tools** 로 최소 의존성을 선언하고, `optional_tools` 로 유연성을 제공한다.
- Playbook 은 **execution_mode** 로 실행 형태를 지정하고, `failure_policy` 로 abort/continue 전략을 정의한다.

## 5. M1 로 넘기는 항목
- Tool 의 **policy_tags** 구체화 및 정책 엔진 연동
- Skill 의 **validation_hint** 상세 구현
- Playbook 의 **policy_bindings** 복합 정책 표현

---
*임의 적용*: 일부 필드(예: `policy_tags`) 는 현재 placeholder이며, M1 에서 구체화 예정.*
