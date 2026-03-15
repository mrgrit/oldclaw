# WORK-27

## 1. 작업 정보
- 작업 이름: M2 코드 주입 3차 / report stage·evidence 최소 경로 구현
- 현재 브랜치: main
- 현재 HEAD 커밋: $(git rev-parse HEAD)
- 작업 시각: $(date -u +%Y-%m-%dT%H:%M:%SZ)

## 2. 이번 작업에서 수정한 파일
- docs/verification/REVIEW-26.md
- docs/verification/NEXT-27.md
- packages/project_service/__init__.py
- apps/manager-api/src/main.py
- docs/m2/oldclaw-m2-completion-report.md
- tools/dev/project_report_evidence_smoke.py
- tools/dev/manager_projects_report_http_smoke.py
- docs/verification/WORK-27.md

## 3. 실행한 명령 목록
- git checkout main
- git pull origin main
- mkdir -p docs/verification
- export DATABASE_URL='postgresql://oldclaw:oldclaw@127.0.0.1:5432/oldclaw'
- python3 -m pip install -r requirements.txt
- python3 -m compileall apps packages tools
- PYTHONPATH=. python3 tools/dev/project_report_evidence_smoke.py
- PYTHONPATH=. python3 tools/dev/manager_projects_report_http_smoke.py
- git status --short

## 4. pip install 결과
- stdout:
```
Defaulting to user installation because normal site-packages is not writeable
Requirement already satisfied: fastapi==0.116.1 in /home/oldclaw/.local/lib/python3.10/site-packages (from -r requirements.txt (line 1)) (0.116.1)
Requirement already satisfied: pydantic==2.11.7 in /home/oldclaw/.local/lib/python3.10/site-packages (from -r requirements.txt (line 2)) (2.11.7)
Requirement already satisfied: uvicorn==0.35.0 in /home/oldclaw/.local/lib/python3.10/site-packages (from -r requirements.txt (line 3)) (0.35.0)
Requirement already satisfied: requests==2.32.5 in /home/oldclaw/.local/lib/python3.10/site-packages (from -r requirements.txt (line 4)) (2.32.5)
Requirement already satisfied: psycopg2-binary==2.9.10 in /home/oldclaw/.local/lib/python3.10/site-packages (from -r requirements.txt (line 5)) (2.9.10)
Requirement already satisfied: httpx==0.28.1 in /home/oldclaw/.local/lib/python3.10/site-packages (from -r requirements.txt (line 6)) (0.28.1)
Requirement already satisfied: starlette<0.48.0,>=0.40.0 in /home/oldclaw/.local/lib/python3.10/site-packages (from fastapi==0.116.1->-r requirements.txt (line 1)) (0.47.3)
Requirement already satisfied: typing-extensions>=4.8.0 in /home/oldclaw/.local/lib/python3.10/site-packages (from fastapi==0.116.1->-r requirements.txt (line 1)) (4.15.0)
Requirement already satisfied: annotated-types>=0.6.0 in /home/oldclaw/.local/lib/python3.10/site-packages (from pydantic==2.11.7->-r requirements.txt (line 2)) (0.7.0)
Requirement already satisfied: pydantic-core==2.33.2 in /home/oldclaw/.local/lib/python3.10/site-packages (from pydantic==2.11.7->-r requirements.txt (line 2)) (2.33.2)
Requirement already satisfied: typing-inspection>=0.4.0 in /home/oldclaw/.local/lib/python3.10/site-packages (from pydantic==2.11.7->-r requirements.txt (line 2)) (0.4.2)
Requirement already satisfied: click>=7.0 in /usr/lib/python3/dist-packages (from uvicorn==0.35.0->-r requirements.txt (line 3)) (8.0.3)
Requirement already satisfied: h11>=0.8 in /home/oldclaw/.local/lib/python3.10/site-packages (from uvicorn==0.35.0->-r requirements.txt (line 3)) (0.16.0)
Requirement already satisfied: charset_normalizer<4,>=2 in /home/oldclaw/.local/lib/python3.10/site-packages (from requests==2.32.5->-r requirements.txt (line 4)) (3.4.5)
Requirement already satisfied: idna<4,>=2.5 in /usr/lib/python3/dist-packages (from requests==2.32.5->-r requirements.txt (line 4)) (3.3)
Requirement already satisfied: urllib3<3,>=1.21.1 in /usr/lib/python3/dist-packages (from requests==2.32.5->-r requirements.txt (line 4)) (1.26.5)
Requirement already satisfied: certifi>=2017.4.17 in /usr/lib/python3/dist-packages (from requests==2.32.5->-r requirements.txt (line 4)) (2020.6.20)
Requirement already satisfied: anyio in /home/oldclaw/.local/lib/python3.10/site-packages (from httpx==0.28.1->-r requirements.txt (line 6)) (4.12.1)
Requirement already satisfied: httpcore==1.* in /home/oldclaw/.local/lib/python3.10/site-packages (from httpx==0.28.1->-r requirements.txt (line 6)) (1.0.9)
Requirement already satisfied: exceptiongroup>=1.0.2 in /home/oldclaw/.local/lib/python3.10/site-packages (from anyio->httpx==0.28.1->-r requirements.txt (line 6)) (1.3.1)
```
- stderr: *(none)*
- exit code: 0

## 5. compileall 결과
- stdout: (listing output trimmed, compilation succeeded without errors)
- stderr: *(none)*
- exit code: 0

## 6. project_report_evidence_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/project_report_evidence_smoke.py`
- stdout:
```
PROJECT_ID: prj_0160ea0e1ccf
FINAL_STAGE: report
FINAL_REPORT_ID: rpt_429f875e36f3
EVIDENCE_ID: ev_c13df2dad3e0
EVIDENCE_EXIT_CODE: 0
```
- stderr: *(none)*
- exit code: 0

## 7. manager_projects_report_http_smoke 결과
- 명령: `PYTHONPATH=. python3 tools/dev/manager_projects_report_http_smoke.py`
- stdout:
```
HTTP_PROJECT_ID: prj_3e5a02cb1745
HTTP_FINAL_STAGE: report
HTTP_EVIDENCE_ID: ev_24987acdef5e
HTTP_REPORT_ID: rpt_5b5155441989
```
- stderr: *(none)*
- exit code: 0

## 8. 핵심 관찰점
- `/projects/{id}/report/finalize` 성공 여부: 성공
- `/projects/{id}/evidence/minimal` 성공 여부: 성공
- `validate -> report` 전이 성공 여부: 성공
- minimal evidence row 저장 성공 여부: 성공
- 아직 남은 한계 (5개 이내):
  1. Full graph/runtime 구현
  2. Asset / playbook 라우터 구현
  3. Approval / policy 엔진 연동
  4. CI 파이프라인 및 자동 테스트 확대
  5. 보고서 단계 전용 endpoint 추가 검토

## 9. 미해결 사항
- graph_runtime 전체 오케스트레이션 로직 구현 필요
- asset/playbook/evidence 라우터 세부 구현 계획 수립
- CI/CD 파이프라인에 전체 lifecycle 테스트 통합
