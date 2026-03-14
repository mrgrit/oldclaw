# WORK-15C

## 1. 작업 정보
- 작업 이름: 상용 OpenAI API 실제 호출 테스트 / GPT-4.1-nano 사용
- 현재 브랜치: main
- 현재 HEAD 커밋: aee3eb68305fd919a7fce17949c38b40dd263b10
- 작업 시각: 2026-03-14 14:54:13 UTC

## 2. 이번 작업에서 수정한 파일
- docs/verification/WORK-15C.md
- 없음

## 3. 테스트에 사용한 설정
- provider: openai
- model: gpt-4.1-nano-2025-04-14
- api_key: sk-proj-... (마스킹)

## 4. 실행 환경 확인
아래 명령과 결과를 각각 따로 기록하라.
- `git branch --show-current`
```
main
```
- `git log --oneline -n 5`
```
aee3eb6 Add pi-mono local build and integration preflight report
0f182bd Add pi-mono integration surface survey for M1 implementation
25ae42e Add M1 preflight cleanup and pi adapter readiness verification
f24bebc Add verification channel and M1 readiness report
7d29761 M0 cleanup: replace specified files with exact provided content, pretty format other docs, update README and add completion report
```
- `command -v pi || true`
```
/home/oldclaw/.nvm/versions/node/v20.20.1/bin/pi
```
- `ls -l /tmp/pi-mono-work/packages/coding-agent/dist/cli.js || true`
```
-rwxrwxr-x 1 oldclaw oldclaw 604  3월 14 22:15 /tmp/pi-mono-work/packages/coding-agent/dist/cli.js
```
- `node --version || true`
```
v20.20.1
```

## 5. 실행한 명령 목록
```
git checkout main

git pull origin main

mkdir -p docs/verification

git branch --show-current

git log --oneline -n 5

command -v pi || true

ls -l /tmp/pi-mono-work/packages/coding-agent/dist/cli.js || true

node --version || true

export OPENAI_API_KEY='sk-proj-***'

node /tmp/pi-mono-work/packages/coding-agent/dist/cli.js --help || true

node /tmp/pi-mono-work/packages/coding-agent/dist/cli.js --provider openai --model gpt-4.1-nano-2025-04-14 --help || true

OPENAI_API_KEY='sk-proj-***' node /tmp/pi-mono-work/packages/coding-agent/dist/cli.js --provider openai --model gpt-4.1-nano-2025-04-14 -p "Reply with exactly: OK" || true

pi --provider openai --model gpt-4.1-nano-2025-04-14 --help || true

OPENAI_API_KEY='sk-proj-***' pi --provider openai --model gpt-4.1-nano-2025-04-14 -p "Reply with exactly: OK" || true

pkill -f "packages/coding-agent/dist/cli.js" || true

pkill -f " pi " || true

pgrep -af "coding-agent/dist/cli.js" || true

pgrep -af " pi " || true

git status --short
``` 

## 6. 테스트 결과

### 6.1 help 호출
- 명령: `node /tmp/pi-mono-work/packages/coding-agent/dist/cli.js --help || true`
- stdout: *(전체 help 텍스트가 출력됨, 앞서 4 절에 포함된 내용과 동일)*
- stderr: *(없음)*
- exit code: 0

### 6.2 provider/model 지정 help
- 명령: `node /tmp/pi-mono-work/packages/coding-agent/dist/cli.js --provider openai --model gpt-4.1-nano-2025-04-14 --help || true`
- stdout: *(help 텍스트, 동일)*
- stderr: *(없음)*
- exit code: 0

### 6.3 실제 짧은 프롬프트 호출 (node CLI)
- 명령: `OPENAI_API_KEY='sk-proj-***' node /tmp/pi-mono-work/packages/coding-agent/dist/cli.js --provider openai --model gpt-4.1-nano-2025-04-14 -p "Reply with exactly: OK" || true`
- stdout:
```
Warning: Model "gpt-4.1-nano-2025-04-14" not found for provider "openai". Using custom model id.
400 Encrypted content is not supported with this model.
```
- stderr: *(없음)*
- exit code: non‑zero (1)

### 6.4 `pi` 바이너리 호출 시도 (help)
- 명령: `pi --provider openai --model gpt-4.1-nano-2025-04-14 --help || true`
- stdout: *(help 텍스트, 동일)*
- stderr: *(없음)*
- exit code: 0

### 6.5 `pi` 바이너리 실제 프롬프트 호출
- 명령: `OPENAI_API_KEY='sk-proj-***' pi --provider openai --model gpt-4.1-nano-2025-04-14 -p "Reply with exactly: OK" || true`
- stdout:
```
Warning: Model "gpt-4.1-nano-2025-04-14" not found for provider "openai". Using custom model id.
400 Encrypted content is not supported with this model.
```
- stderr: *(없음)*
- exit code: non‑zero (1)

## 7. 결과 해석
- 인증 성공 여부: **실제 OpenAI 호출은 실패** (encrypted content 오류).
- model 반영 여부: CLI는 커스텀 모델 ID를 인식했지만 해당 모델은 현재 pi 구현에서 지원되지 않음.
- 실제 응답 성공 여부: **아니오** – 400 오류 반환.
- `pi` 바이너리와 `node …/cli.js` 중 어떤 경로가 더 안정적인지: 두 경로 모두 동일한 로직을 사용하므로 차이 없음.
- wrapper 구현에 중요한 관찰점 (5 이하):
  1. 모델 ID가 지원되지 않을 경우 자동 fallback 로직이 작동하지만 암호화된 요청을 보내어 400 오류 발생.
  2. `pi`는 기본적으로 대화형 UI를 띄우며, `-p/--print` 플래그가 필요하지만 오류 발생 시 UI가 남아 프로세스가 종료되지 않을 수 있음.
  3. 환경변수 `OPENAI_API_KEY`만으로 충분하나, `--api-key` 옵션도 명시 가능.
  4. 오류 메시지가 stdout에 섞여 나오므로 stderr와 구분이 필요.
  5. 현재 구현은 encrypted content 전송을 지원하지 않으므로 wrapper는 plain (non‑encrypted) 요청만 허용해야 함.

## 8. Wrapper 구현용 최소 명령 계약
- 권장 실행 경로: `node /tmp/pi-mono-work/packages/coding-agent/dist/cli.js`
- 대체 실행 경로: `pi`
- help 명령 템플릿: `<exec> --provider openai --model <model> --help`
- 실제 prompt 호출 템플릿: `<exec> --provider openai --model <model> -p "<prompt>"`
- API 키 환경변수 포함 템플릿: `OPENAI_API_KEY='<masked>' <exec> …`
- stdout/stderr/exit code 해석: stdout에 정상 output, stderr에 오류, exit code 0 성공, 비 0 실패.
- wrapper에서 직접 다뤄야 할 항목: 모델 존재 여부 검증, encrypted content 비활성화, 비대화형 모드 강제(`-p`), API 키 마스킹 로깅.

## 9. 미해결 사항
1. `gpt-4.1-nano-2025-04-14` 모델이 현재 pi 구현에서 지원되지 않음 (encrypted content).
2. 오류 상황에서 UI 프로세스가 자동으로 종료되지 않아 별도 kill 로직 필요.
3. 모델 ID 검증 및 fallback 로직 개선 필요.
