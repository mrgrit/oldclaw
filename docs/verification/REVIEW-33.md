# REVIEW-33

## 판정
미통과

## 이유
`WORK-33` 보고와 실제 코드가 안 맞는다.

### 확인된 문제
1. `packages/pi_adapter/runtime/__init__.py` 아직 `from .client import PiRuntime` 이다. 실제 `client.py`에는 `PiRuntime`가 없고 `PiRuntimeClient`, `PiRuntimeConfig`만 있다.
2. `packages/graph_runtime/__init__.py` 아직 `GraphRuntimeError`, `require_transition`이 없다. 그런데 `project_service`는 그걸 import해서 쓰려고 한다.
3. `apps/manager-api/src/main.py` 아직도 깨져 있다.
   * `PiAdapterError` import 시도
   * `plan_project_record`, `validate_project_record`, `link_asset_to_project`, `get_project_assets` 등 import 누락
   * `POST /projects/{project_id}/close` 없음
   * target route가 여전히 `/targets/{project_id}/targets/{target_id}` 구조
   * playbook router는 여전히 501
4. `tools/dev` 아직 없다.
   * `project_playbook_smoke.py`
   * `manager_projects_playbook_http_smoke.py`
   * `m3_integrated_smoke.py`
5. `README.md`, `docs/m3/oldclaw-m3-start-report.md` 문서는 target/playbook 상태를 충분히 반영하지 못한다.

## 결론
코드와 문서가 크게 불일치한다. 레포 정합성 복구가 필요하다.
