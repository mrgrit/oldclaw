# NEXT-27

## 작업 이름
M2 코드 주입 3차 / report stage·evidence 최소 경로 구현

## 목적
M2 2차에서 만든 lifecycle 경로를 한 단계 확장하여,
`validate -> report` 전이와 최소 evidence 저장 경로를 실제 DB와 HTTP 라우터에 반영한다.

## 이번 단계의 구현 범위
- `packages/project_service`의 report stage finalize 구현
- minimal evidence insert 구현
- `apps/manager-api/src/main.py`에 `/projects/{id}/report/finalize`, `/projects/{id}/evidence/minimal` 추가
- smoke test 2종 추가
- M2 completion report 갱신

## 이번 단계의 성공 기준
- POST `/projects` 성공
- POST `/projects/{id}/plan` 성공
- POST `/projects/{id}/execute` 성공
- POST `/projects/{id}/validate` 성공
- POST `/projects/{id}/report/finalize` 성공
- POST `/projects/{id}/evidence/minimal` 성공
- report/evidence smoke 성공
- manager report HTTP smoke 성공
