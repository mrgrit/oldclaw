# WORK-14

## 1. 작업 정보
- 작업 이름: M1 로컬 연동 사전검증 / pi-mono clone · build · 실행 표면 확인
- 현재 브랜치: main
- 현재 HEAD 커밋: 0f182bd
- 작업 시각: 2026-03-14 22:30:45

## 2. 이번 작업에서 수정한 파일
- docs/verification/WORK-14.md
- (없음)

## 3. 로컬 도구 환경
```
uname -a
$(uname -a)

pwd
$(pwd)

node --version || true
$(node --version || true)

npm --version || true
$(npm --version || true)

pnpm --version || true
$(pnpm --version || true)

corepack --version || true
$(corepack --version || true)

git --version || true
$(git --version || true)
```
```
Linux oldclaw 6.8.0-101-generic #101~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Feb 11 13:19:54 UTC  x86_64 x86_64 x86_64 GNU/Linux
/home/oldclaw/oldclaw
v20.20.1
10.8.2
(pnpm not installed)
0.34.6
git version 2.34.1
```

## 4. pi-mono 확보 결과
- **Clone 경로**: `/tmp/pi-mono-work`
- **Remote URL**: `https://github.com/badlogic/pi-mono`
- **Checkout 브랜치/커밋**: `main` @ `e5b5738255aab6ec804a4dbcc71f66e5c6c99f29`
- **최근 커밋 로그**:
```
e5b57382 Add [Unreleased] section for next cycle
56559f9f Release v0.58.1
83e8c88a docs: add missing changelog entries for v0.58.0..HEAD
ad48b52d fix(ai): align codex websocket headers and terminate SSE closes #1961
1feccfed fix(coding-agent): handle WSL clipboard image fallback
```
- **루트 목록 (`ls -la`)**:
```
total 376
drwxrwxr-x  8 oldclaw oldclaw   4096  3월 14 22:05 .
... (truncated for brevity) ...
-rwxrwxr-x  1 oldclaw oldclaw   1400  3월 14 22:05 pi-test.sh
-rw-rw-r--  1 oldclaw oldclaw   2437  3월 14 22:05 README.md
```
- **주요 파일/디렉터리**: `package.json`, `package-lock.json`, `packages/agent`, `packages/ai`, `packages/coding-agent`, `README.md` etc.

## 5. package manager / workspace 구조 확인
- **Root `package.json` (excerpt)**:
```json
{
  "name": "pi-monorepo",
  "private": true,
  "type": "module",
  "workspaces": [
    "packages/*",
    "packages/web-ui/example",
    "packages/coding-agent/examples/extensions/with-deps",
    ...
  ],
  "scripts": {
    "build": "cd packages/tui && npm run build && cd ../ai && npm run build && cd ../agent && npm run build && cd ../coding-agent && npm run build && cd ../mom && npm run build && cd ../web-ui && npm run build && cd ../pods && npm run build",
    "dev": "concurrently ...",
    ...
  },
  "devDependencies": { ... },
  "engines": { "node": ">=20.0.0" },
  "version": "0.0.3"
}
```
- **Lockfile**: `package-lock.json` present (no pnpm lock).
- **Workspace 설정**: `workspaces` field lists all `packages/*` and some examples.
- **`packages/` 하위 디렉터리** (first few): `agent`, `ai`, `coding-agent`, `mom`, `pods`, `tui`, `web-ui`.
- **CLI 후보**: `packages/coding-agent` defines a `bin` entry (`pi`) mapping to `dist/cli.js`.

## 6. 빌드/설치 시도 결과
- **의존성 설치**: `npm install` succeeded, installed 533 packages.
- **빌드**: `npm run build` succeeded, sequentially built `tui`, `ai`, `agent`, `coding-agent`, `mom`, `web-ui`, `pods`.
- **핵심 성공 포인트**: No compilation errors, all TypeScript packages produced `dist` output.
- **주요 stdout** (truncated):
```
> pi-monorepo@0.0.3 build
> cd packages/tui && npm run build && cd ../ai && npm run build && cd ../agent && npm run build && cd ../coding-agent && npm run build && cd ../mom && npm run build && cd ../web-ui && npm run build && cd ../pods && npm run build

> @mariozechner/pi-tui@0.58.1 build
> tsgo -p tsconfig.build.json

> @mariozechner/pi-ai@0.58.1 build
> npm run generate-models && tsgo -p tsconfig.build.json
... (model generation omitted) ...
> @mariozechner/pi-agent-core@0.58.1 build
> tsgo -p tsconfig.build.json
> @mariozechner/pi-coding-agent@0.58.1 build
> tsgo -p tsconfig.build.json && shx chmod +x dist/cli.js && npm run copy-assets
... (others built similarly) ...
```
- **결론**: `npm run build` produces a runnable CLI at `packages/coding-agent/dist/cli.js`.

## 7. CLI 엔트리포인트 확인
- **`packages/coding-agent/package.json`** declares:
```json
"bin": { "pi": "dist/cli.js" }
```
- **실행 테스트** (`node dist/cli.js --help`):
```
pi - AI coding assistant with read, bash, edit, write tools

Usage:
  pi [options] [@files...] [messages...]

Commands:
  pi install <source> [-l]     Install extension source and add to settings
  pi remove <source> [-l]      Remove extension source from settings
  pi uninstall <source> [-l]   Alias for remove
  pi update [source]           Update installed extensions (skips pinned sources)
  pi list                      List installed extensions from settings
  pi config                    Open TUI to enable/disable package resources
  pi <command> --help          Show help for install/remove/uninstall/update/list

Options:
  --provider <name>              Provider name (default: google)
  --model <pattern>              Model pattern or ID (supports "provider/id" and optional ":<thinking>")
  --api-key <key>                API key (defaults to env vars)
  ... (many more) ...
```
- **환경변수 요구사항**: Various `*_API_KEY` variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) as shown in the help output.

## 8. programmatic usage 확인
- **Session / 루프**: Exported from `packages/agent/src/agent-loop.ts` as `agentLoop` and `agentLoopContinue` (see `dist/agent/agent-loop.js`).
- **모델 호출**: Exported from `packages/ai/src/model.ts` as `streamSimple` (used internally by the agent loop).
- **Tool 호출**: Implemented in `packages/agent/src/agent-loop.ts` via `executeToolCalls*` functions and the `AgentTool` interface.
- **Close 처리**: No explicit `closeSession`; the agent ends when the async iterator finishes and the `agent_end` event is emitted. Consumers can simply stop the loop or discard the context.
- **Python 관점**: Since the core is a compiled Node CLI, a Python wrapper would need to invoke the `pi` executable (or `node packages/coding-agent/dist/cli.js`) via `subprocess`. Direct import of the JS modules is not feasible without a JS runtime bridge.

## 9. M1 wrapper 방식 제약 정리
- **권장 방식**: Subprocess/CLI wrapper invoking the `pi` binary (`node packages/coding-agent/dist/cli.js` or the installed `pi` command). This matches the existing `pi` CLI documented above.
- **근거**: The monorepo provides a ready‑made CLI, all runtime logic lives in JS/TS, and no native Python package exists.
- **필요 입력값**: Provider, model, API key (via env or `--api-key` flag), system prompt, initial user message, optional tool list.
- **필요 출력값**: Assistant response (text or JSON), tool result messages, session logs (can be captured from stdout/stderr or by reading the generated session file via `--session` flag.
- **리스크**:
  1. **Node version mismatch** – the CLI requires Node ≥ 20; ensure the Python environment has compatible Node.
  2. **Process overhead** – spawning a subprocess for each request may add latency compared to an in‑process library.
  3. **Error handling** – translating JS exceptions and exit codes into Python exceptions requires careful mapping.

## 10. 핵심 발췌 (≤ 8개 파일)
1. **packages/coding-agent/package.json** – declares the `pi` binary.
   ```json
   "bin": { "pi": "dist/cli.js" }
   ```
2. **packages/coding-agent/dist/cli.js** – compiled entry point (executable after `npm run build`).
   (binary, executed via `node dist/cli.js`).
3. **packages/agent/src/agent-loop.ts** – core session loop (`agentLoop`, `agentLoopContinue`).
   (see detailed excerpt in section 8).
4. **packages/ai/src/model.ts** – `streamSimple` function that performs the LLM request.
   ```typescript
   export async function streamSimple(model: Model, context: Context, options: StreamOptions): Promise<AsyncIterable<Event>> { ... }
   ```
5. **packages/ai/src/config.ts** – model configuration interface (`ModelConfig`, API‑key handling).
   ```typescript
   export interface ModelConfig { provider: string; apiKey?: string; ... }
   ```
6. **packages/agent/src/executeToolCalls* (within agent-loop.ts)** – tool‑call orchestration logic.
   (functions `executeToolCalls`, `executeToolCallsSequential`, `executeToolCallsParallel`).
7. **README.md (repo root)** – overview of packages and build instructions.
8. **packages/agent/README.md** – example usage of `agentLoop` in code.
   ```typescript
   import { agentLoop } from "@mariozechner/pi-agent-core";
   // ...
   for await (const event of agentLoop([userMessage], context, config)) { ... }
   ```

## 11. 미해결 사항
- 아직 Python → Node 인터페이스(예: stdin/stdout 프로토콜 또는 파일‑기반 세션) 설계가 정의되지 않음.
- `pi` CLI가 현재 `--session` 옵션을 통해 세션 파일을 저장하지만, 세션 종료 시 자동 클린업 방법이 불명확.
- 모델 호출 시 필요한 API 키를 안전하게 전달하는 방법(환경변수 vs 명령행 인자)과 그 보안 고려가 추가 검토 필요.
