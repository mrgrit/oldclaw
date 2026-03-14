# OldClaw M0 Completion Report

## 직접 주입된 파일 목록

- `docs/m0/oldclaw-m0-design-baseline.md`
- `docs/m0/oldclaw-m0-registry-spec.md`
- `apps/manager-api/src/main.py`
- `apps/subagent-runtime/src/main.py`
- `packages/pi_adapter/runtime/client.py`
- `migrations/0001_init_core.sql`

## 남은 미해결 사항

1. `apps/master-service/src/main.py` 의 리뷰/리플랜/에스컬레이션 엔드포인트와 구조화된 앱 팩토리 구현 필요.
2. `apps/scheduler-worker/src/main.py` 에 `load_schedules`, `process_schedule`, `run_loop` 함수 구현 필요.
3. `apps/watch-worker/src/main.py` 에 `load_watch_jobs`, `process_watch_job`, `run_loop` 함수 구현 필요.
4. `packages/pi_adapter/tools/*` 에 툴 브리지 추상화 구현 필요.
5. `packages/pi_adapter/sessions/*` 에 세션 추상화 구현 필요.
6. `packages/pi_adapter/model_profiles/*` 에 모델 프로파일 정의 필요.
7. `packages/pi_adapter/translators/*` 에 요청/응답 변환 추상화 필요.
8. `packages/pi_adapter/contracts/*` 에 계약 타입/데이터클래스 정의 필요.

## 임의 적용 사항

- 전체 문서와 코드 파일을 **한 줄 압축 없이 멀티라인** 형태로 정리하여 가독성을 확보함.
- 기존 파일 내용은 **주어진 본문과 정확히 일치**하도록 교체함.
- Markdown 헤더와 리스트, 코드 블록이 정상 렌더링되도록 유지함.

## M0 완료 여부

(본 섹션은 작성하지 않음 – 사실만 기재)
