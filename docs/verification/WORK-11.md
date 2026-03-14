# WORK-11

## 1. 작업 정보
- 작업 이름: M1 준비 현황 수집 + 검수 채널 고정
- 현재 브랜치: main
- 현재 HEAD 커밋: 7d29761b7bbfc66d46dafe9de52b58cd307de97e
- 작업 시각: 2026-03-14 20:41:29

## 2. 이번 작업에서 수정한 파일
- docs/verification/README.md
- docs/verification/WORK-11.md
- (없음)

## 3. 현재 브랜치 및 최근 커밋
```
main
?? apps/manager-api/src/__pycache__/
?? apps/master-service/src/__pycache__/
?? apps/scheduler-worker/src/__pycache__/
?? apps/subagent-runtime/src/__pycache__/
?? apps/watch-worker/src/__pycache__/
?? packages/a2a_protocol/__pycache__/
?? packages/approval_engine/__pycache__/
?? packages/asset_registry/__pycache__/
?? packages/core/__pycache__/
?? packages/evidence_service/__pycache__/
?? packages/experience_service/__pycache__/
?? packages/graph_runtime/__pycache__/
?? packages/history_service/__pycache__/
?? packages/pi_adapter/__pycache__/
?? packages/pi_adapter/contracts/__pycache__/
?? packages/pi_adapter/model_profiles/__pycache__/
?? packages/pi_adapter/runtime/__pycache__/
?? packages/pi_adapter/sessions/__pycache__/
?? packages/pi_adapter/tools/__pycache__/
?? packages/pi_adapter/translators/__pycache__/
?? packages/policy_engine/__pycache__/
?? packages/project_service/__pycache__/
?? packages/registry_service/__pycache__/
?? packages/reporting_service/__pycache__/
?? packages/retrieval_service/__pycache__/
?? packages/scheduler_service/__pycache__/
?? packages/shared/__pycache__/
?? packages/validation_service/__pycache__/
7d29761 M0 cleanup: replace specified files with exact provided content, pretty format other docs, update README and add completion report
3c5bd62 M0 final polish: inject core files, ensure readability, update master-service, README, completion report
```
```
packages/pi_adapter/contracts/__init__.py
packages/pi_adapter/contracts/__pycache__/__init__.cpython-310.pyc
packages/pi_adapter/__init__.py
packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/model_profiles/__pycache__/__init__.cpython-310.pyc
packages/pi_adapter/__pycache__/__init__.cpython-310.pyc
packages/pi_adapter/runtime/client.py
packages/pi_adapter/runtime/__init__.py
packages/pi_adapter/runtime/__pycache__/client.cpython-310.pyc
packages/pi_adapter/runtime/__pycache__/__init__.cpython-310.pyc
packages/pi_adapter/sessions/__init__.py
packages/pi_adapter/sessions/__pycache__/__init__.cpython-310.pyc
packages/pi_adapter/tools/__init__.py
packages/pi_adapter/tools/__pycache__/__init__.cpython-310.pyc
packages/pi_adapter/tools/__pycache__/tool_bridge.cpython-310.pyc
packages/pi_adapter/tools/tool_bridge.py
packages/pi_adapter/translators/__init__.py
packages/pi_adapter/translators/__pycache__/__init__.cpython-310.pyc
```
```
apps/manager-api/src/main.py
apps/master-service/src/main.py
apps/scheduler-worker/src/main.py
apps/subagent-runtime/src/main.py
apps/watch-worker/src/main.py
```
```
packages/pi_adapter/__init__.py
packages/pi_adapter/runtime/__init__.py
packages/pi_adapter/runtime/client.py
packages/pi_adapter/sessions/__init__.py
packages/pi_adapter/tools/__init__.py
packages/pi_adapter/tools/tool_bridge.py
packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/translators/__init__.py
packages/pi_adapter/contracts/__init__.py
```
```
packages/pi_adapter/runtime/client.py
packages/pi_adapter/runtime/__init__.py
packages/pi_adapter/tools/__init__.py
packages/pi_adapter/tools/tool_bridge.py
packages/pi_adapter/sessions/__init__.py
packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/translators/__init__.py
packages/pi_adapter/contracts/__init__.py
apps/manager-api/src/main.py
apps/master-service/src/main.py
apps/subagent-runtime/src/main.py
.env.example
README.md
```
```
grep -R "pi_adapter" -n apps packages || true
packages/pi_adapter/runtime/__init__.py:1:# packages/pi_adapter/runtime/__init__.py
packages/pi_adapter/model_profiles/__init__.py:1:# packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/tools/tool_bridge.py:1:# packages/pi_adapter/tools/tool_bridge.py
packages/pi_adapter/tools/__init__.py:1:# packages/pi_adapter/tools/__init__.py
packages/pi_adapter/translators/__init__.py:1:# packages/pi_adapter/translators/__init__.py
packages/pi_adapter/sessions/__init__.py:1:# packages/pi_adapter/sessions/__init__.py
packages/pi_adapter/__init__.py:1:# pi_adapter package placeholder
packages/pi_adapter/contracts/__init__.py:1:# packages/pi_adapter/contracts/__init__.py
```
```
grep -R "PiRuntimeClient" -n apps packages || true
packages/pi_adapter/runtime/client.py:12:class PiRuntimeClient:
```
```
grep -R "NotImplementedError" -n packages/pi_adapter apps || true
packages/pi_adapter/runtime/__init__.py:4:class RuntimeError(NotImplementedError):
packages/pi_adapter/runtime/client.py:26:        raise NotImplementedError(
packages/pi_adapter/runtime/client.py:32:        raise NotImplementedError(
packages/pi_adapter/runtime/client.py:38:        raise NotImplementedError(
packages/pi_adapter/tools/tool_bridge.py:5:In M0 they raise NotImplementedError.
packages/pi_adapter/tools/tool_bridge.py:12:        raise NotImplementedError("RunCommandTool execution not implemented in M0")
packages/pi_adapter/tools/__init__.py:13:        raise NotImplementedError("Tool execution not implemented for M0")
packages/pi_adapter/sessions/__init__.py:11:        raise NotImplementedError("PiSession not available in M0")
apps/watch-worker/src/main.py:16:    Returns a list of watch job dicts. Placeholder raises NotImplementedError in M0.
apps/watch-worker/src/main.py:18:    raise NotImplementedError("load_watch_jobs not implemented in M0 – DB integration pending")
apps/watch-worker/src/main.py:24:    raise NotImplementedError("process_watch_job not implemented in M0 – event handling pending")
apps/watch-worker/src/main.py:34:        except NotImplementedError:
apps/scheduler-worker/src/main.py:16:    Returns a list of schedule dicts. Placeholder raises NotImplementedError in M0.
apps/scheduler-worker/src/main.py:18:    raise NotImplementedError("load_schedules not implemented in M0 – DB integration pending")
apps/scheduler-worker/src/main.py:25:    raise NotImplementedError("process_schedule not implemented in M0 – job creation pending")
apps/scheduler-worker/src/main.py:35:        except NotImplementedError:
```
```
grep -R "FastAPI" -n apps || true
apps/watch-worker/src/main.py:5:from fastapi import FastAPI
apps/watch-worker/src/main.py:7:app = FastAPI(title="Watch Worker")
apps/manager-api/src/main.py:4:from fastapi import APIRouter, FastAPI, HTTPException, status
apps/manager-api/src/main.py:166:def create_app() -> FastAPI:
apps/manager-api/src/main.py:167:    app = FastAPI(
apps/scheduler-worker/src/main.py:5:from fastapi import FastAPI
apps/scheduler-worker/src/main.py:7:app = FastAPI(title="Scheduler Worker")
apps/subagent-runtime/src/main.py:4:from fastapi import APIRouter, FastAPI, HTTPException, status
apps/subagent-runtime/src/main.py:68:def create_app() -> FastAPI:
apps/subagent-runtime/src/main.py:69:    app = FastAPI(
apps/master-service/src/main.py:1:from fastapi import FastAPI, APIRouter, HTTPException, status
apps/master-service/src/main.py:60:def create_app() -> FastAPI:
```
```
grep -R "model_profile" -n . || true
packages/pi_adapter/runtime/client.py:7:    model_profile: str
packages/pi_adapter/model_profiles/__init__.py:1:# packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/model_profiles/__init__.py:3:# packages/pi_adapter/model_profiles/__init__.py
packages/pi_adapter/model_profiles/__init__.py:4:# packages/pi_adapter/model_profiles/__init__.py
```
```
   23 packages/pi_adapter/contracts/__init__.py
    8 packages/pi_adapter/contracts/__pycache__/__init__.cpython-310.pyc
   34 packages/pi_adapter/__init__.py
   14 packages/pi_adapter/model_profiles/__init__.py
    7 packages/pi_adapter/model_profiles/__pycache__/__init__.cpython-310.pyc
   15 packages/pi_adapter/__pycache__/__init__.cpython-310.pyc
   41 packages/pi_adapter/runtime/client.py
    5 packages/pi_adapter/runtime/__init__.py
   11 packages/pi_adapter/sessions/__init__.py
   13 packages/pi_adapter/tools/__init__.py
   14 packages/pi_adapter/tools/tool_bridge.py
   17 packages/pi_adapter/translators/__init__.py
   26 packages/pi_adapter/contracts/__init__.py
  251 total
```
```
  182 apps/manager-api/src/main.py
   30 apps/manager-api/src/__pycache__/main.cpython-310.pyc
   67 apps/master-service/src/main.py
   14 apps/master-service/src/__pycache__/main.cpython-310.pyc
   42 apps/scheduler-worker/src/main.py
   18 apps/scheduler-worker/src/__pycache__/main.cpython-310.pyc
   82 apps/subagent-runtime/src/main.py
   15 apps/subagent-runtime/src/__pycache__/main.cpython-310.pyc
   41 apps/watch-worker/src/main.py
   17 apps/watch-worker/src/__pycache__/main.cpython-310.pyc
  508 total
```
```
   3 .env.example
  24 README.md
  27 total
```
```
-rw-rw-r-- 1 oldclaw oldclaw 1.1K  3월 14 09:36 packages/pi_adapter/__init__.py
-rw-rw-r-- 1 oldclaw oldclaw 123  3월 14 20:07 packages/pi_adapter/runtime/__init__.py
-rw-rw-r-- 1 oldclaw oldclaw 1.4K  3월 14 20:07 packages/pi_adapter/runtime/client.py
-rw-rw-r-- 1 oldclaw oldclaw 364  3월 14 20:07 packages/pi_adapter/sessions/__init__.py
-rw-rw-r-- 1 oldclaw oldclaw 400  3월 14 20:07 packages/pi_adapter/tools/__init__.py
-rw-rw-r-- 1 oldclaw oldclaw 469  3월 14 20:07 packages/pi_adapter/tools/tool_bridge.py
-rw-rw-r-- 1 oldclaw oldclaw 472  3월 14 20:07 packages/pi_adapter/model_profiles/__init__.py
-rw-rw-r-- 1 oldclaw oldclaw 526  3월 14 20:07 packages/pi_adapter/contracts/__init__.py
-rw-rw-r-- 1 oldclaw oldclaw 570  3월 14 20:07 packages/pi_adapter/translators/__init__.py
```
```
Listing 'apps'...
Listing 'apps/manager-api'...
Listing 'apps/manager-api/src'...
Listing 'apps/master-service'...
Listing 'apps/master-service/src'...
Listing 'apps/scheduler-worker'...
Listing 'apps/scheduler-worker/src'...
Listing 'apps/subagent-runtime'...
Listing 'apps/subagent-runtime/src'...
Listing 'apps/watch-worker'...
Listing 'apps/watch-worker/src'...
Listing 'packages'...
Listing 'packages/a2a_protocol'...
Listing 'packages/approval_engine'...
Listing 'packages/asset_registry'...
Listing 'packages/core'...
Listing 'packages/evidence_service'...
Listing 'packages/experience_service'...
Listing 'packages/graph_runtime'...
Listing 'packages/history_service'...
Listing 'packages/pi_adapter'...
Listing 'packages/pi_adapter/contracts'...
Listing 'packages/pi_adapter/model_profiles'...
Listing 'packages/pi_adapter/runtime'...
Listing 'packages/pi_adapter/sessions'...
Listing 'packages/pi_adapter/tools'...
Listing 'packages/pi_adapter/translators'...
Listing 'packages/policy_engine'...
Listing 'packages/project_service'...
Listing 'packages/registry_service'...
Listing 'packages/reporting_service'...
Listing 'packages/retrieval_service'...
Listing 'packages/scheduler_service'...
Listing 'packages/shared'...
Listing 'packages/validation_service'...
```
## 10. M1 전에 내가 직접 작성해야 할 파일 후보
- packages/pi_adapter/runtime/client.py: 현재 스텁만 존재 – 실제 pi SDK 연동 구현 필요
- packages/pi_adapter/tools/tool_bridge.py: Tool 구현부는 NotImplementedError – 실제 Tool 로직 필요
- packages/pi_adapter/sessions/__init__.py: PiSession 스텁 – 세션 관리 구현 필요
- packages/pi_adapter/model_profiles/__init__.py: 프로파일 정의는 static – 동적 로드 로직 필요
- packages/pi_adapter/contracts/__init__.py: 계약 스키마 정의 – 검증 로직 필요
- apps/master-service/src/main.py: 리뷰/리플랜/에스컬레이션 엔드포인트 실제 로직 필요
- apps/scheduler-worker/src/main.py: 스케줄 로드/처리/루프 구현 필요
- apps/watch-worker/src/main.py: 워치 잡 로드/처리/루프 구현 필요
- apps/manager-api/src/main.py: 실제 엔드포인트 구현 필요
- docs/m0/oldclaw-m0-design-baseline.md 등: 설계 문서 보강 필요 (추후 M1 전 단계)

## 11. 미해결 사항
- 현재 모든 pi_adapter 관련 로직이 NotImplemented 상태이며, 실제 실행 로직이 부재
- 스케줄러와 워치 워커는 DB 연동이 미구현 상태
- FastAPI 엔드포인트는 스텁으로만 존재해 실제 서비스 동작 못 함
