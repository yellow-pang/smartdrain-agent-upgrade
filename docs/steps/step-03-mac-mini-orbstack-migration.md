# SmartDrain Mac mini + OrbStack Migration Steps

이 문서는 migration 구현 중 지속적으로 갱신하는 실행 상태 및 인수인계 기록이다. 판단 근거는 Analysis, 실행 순서와 Gate는 Plan을 참조하며 이 문서에 복제하지 않는다.

## 0. Source of Truth

- Analysis: [`docs/verification/18_mac-mini-orbstack-migration-analysis.md`](../verification/18_mac-mini-orbstack-migration-analysis.md)
- Plan: [`docs/plans/plan-03-mac-mini-orbstack-migration.md`](../plans/plan-03-mac-mini-orbstack-migration.md)
- 작업 branch: `chore/macos-orbstack-migration`
- 구현 시작 기준 HEAD: `277e16727087bc0ccc1f4ae880a529063030d97b` (예정 기준, 구현 미시작)
- 현재 HEAD: `277e16727087bc0ccc1f4ae880a529063030d97b`
- 마지막 갱신 시각: `2026-09-20 12:12:26 KST`

## 1. Current State

- 현재 Phase: Phase 0 — Migration Preparation
- 현재 Task: Task 0.1 — 기준 상태 기록
- 현재 Gate: Gate A — 미평가
- 현재 상태: `NOT_STARTED`
- 구현 코드는 아직 수정하지 않았다. 수정된 Plan과 이 초기 상태 문서의 확정 후 Phase 0부터 시작한다.

## 2. Next Action

Plan과 Steps 확정 후 **Task 0.1의 첫 작업으로 기존 VM 운영 checkout에서 `git rev-parse HEAD`를 읽기 전용으로 확인한다.**

## 3. Completed Tasks

### 구현 전 문서 준비

- 수행 내용: Plan의 실행 기준, 운영 `.env` 이전, non-blocking 용량 진단, 조건부 VM 비교, 서버 lifecycle 검증을 최종 보정하고 Steps를 초기화했다.
- 실제 변경 파일:
  - `docs/plans/plan-03-mac-mini-orbstack-migration.md`
  - `docs/steps/step-03-mac-mini-orbstack-migration.md`
- 실행 명령: Git branch·HEAD·working tree 확인과 문서 정적 검토만 수행했다.
- 결과: migration 구현 Task는 아직 시작하지 않았다.
- 성공 여부: 성공. 필수 구조, source 문서 경로, branch·HEAD, whitespace를 확인했다.

## 4. Gate Results

### Gate A

- 상태: `NOT_STARTED`
- 근거: Linux/arm64 AI build 및 실제 inference 미실행.
- 남은 위험: native dependency, OpenCV decode, YOLO CPU inference, XGBoost inference, callback/status/result 계약을 실제로 검증해야 한다.

### Gate B

- 상태: `NOT_STARTED`
- 근거: 새 PostgreSQL migration 및 전체 Compose 미실행.
- 남은 위험: 빈 DB migration, seed, service health, container restart 복구를 실제로 검증해야 한다.

### Gate C

- 상태: `NOT_STARTED`
- 근거: `127.0.0.1:8099` localhost E2E 미실행.
- 남은 위험: REST, image, WebSocket, AI callback, DB 저장, Frontend 반영을 실제 사용자 흐름으로 검증해야 한다.

### Gate D

- 상태: `NOT_STARTED`
- 근거: Cloudflare 설정 미변경, 공개 E2E 미실행.
- 남은 위험: HTTPS, WSS, domain-dependent 설정과 VM origin 복귀 경로를 검증해야 한다.

### Server Lifecycle Verification

- 상태: `NOT_STARTED`
- 근거: OrbStack/runtime 재시작과 Mac 재부팅 검증 미실행.
- 남은 위험: PostgreSQL volume, nginx `127.0.0.1:8099`, cloudflared, 공개 HTTPS/WSS의 실제 복구 방식을 확인해야 한다.

## 5. Actual Changes

| 파일 | 수정/삭제/추가 | 실제 변경 이유 | Plan과 차이 |
| --- | --- | --- | --- |
| `docs/plans/plan-03-mac-mini-orbstack-migration.md` | 수정 | 승인 전 최종 보정 사항 반영 | 없음 |
| `docs/steps/step-03-mac-mini-orbstack-migration.md` | 추가 | 구현 상태, 다음 작업, Gate와 실행 이력을 세션 간 인계 | Plan 실행 전에 초기화하도록 시점 명확화 |

## 6. Commands Already Executed

| 분류 | 명령/작업 | 결과 |
| --- | --- | --- |
| 상태 확인 | `git status --short --branch`, branch, HEAD 확인 | branch와 기준 HEAD 확인 |
| 문서 검증 | 필수 section·핵심 문구 검색, source 문서 존재 확인, whitespace 검사 | 통과 |
| AI build | 미실행 | 구현 시작 전 |
| DB migration | 미실행 | 구현 시작 전 |
| DB seed | 미실행 | 구현 시작 전 |
| E2E | 미실행 | 구현 시작 전 |
| Cloudflare 변경 | 미실행 | Gate C 이후 별도 승인 경계 유지 |

## 7. Measurements

- AI build 시간: 미측정
- Backend build 시간: 미측정
- Frontend build 시간: 미측정
- image/cache 증가량: 미측정
- 모델 load 시간: 미측정
- inference 시간: 미측정
- Compose startup 시간: 미측정

추정값은 기록하지 않는다. 실제 측정 뒤 해당 항목만 갱신한다.

## 8. Decisions / Deviations

- Plan의 Phase, Task, Gate를 실행 source of truth로 사용한다. 특정 agent 실행 framework는 필수가 아니다.
- Steps는 완료 후 일회성 보고서가 아니라 구현 중 갱신하는 상태 문서로 사용한다.
- Phase 0의 상세 image layer·cache 진단은 non-blocking 자료다.
- VM과 Mac의 결과 비교는 동일한 코드 경로와 artifact가 확보된 경우에 수행한다. 비교 불가 이유는 기록하되 그 사실만으로 Gate A를 실패 처리하지 않는다.
- 현재 Plan과 다른 구현 결정은 없다. 큰 범위 변경이 필요하면 구현하지 않고 이 문서의 blocker와 근거를 먼저 갱신해 보고한다.
- 사용자 승인 필요 여부: 현재 없음. 실제 Docker·Compose·Cloudflare 변경 단계에서는 루트 `AGENTS.md`와 Plan의 승인 경계를 따른다.
- Plan 수정 여부: 이번 최종 보정 반영 완료.

## 9. Open Issues / Blockers

- 현재 blocker 없음.
- 구현 시작 전 Plan과 Steps의 사용자 검토·확정을 기다린다.

## 10. Deferred Work

- AI image 최적화
- CPU-only dependency 재구성 및 전체 dependency pinning
- Python·Node runtime 업그레이드
- test image 정리와 Docker cache GC 정책
- GitHub Actions와 GHCR
- multi-arch build
- 자동 rollback
- Jenkins 제거
- 모델 runtime download와 format 변경
- ONNX, TensorRT, quantization

이 항목들은 migration 실행 중 편의를 이유로 현재 범위에 포함하지 않는다.

## 11. Context Recovery Procedure

새 세션 또는 context 압축 후 다음 순서로 복구한다.

1. 루트 `AGENTS.md`를 확인한다.
2. Analysis를 확인한다.
3. Plan을 확인한다.
4. 이 Steps 문서를 확인한다.
5. `git status --short --untracked-files=all`을 실행한다.
6. 현재 branch와 HEAD를 확인한다.
7. Steps의 Current State와 실제 Git 상태를 비교한다.
8. 불일치가 없다면 `Next Action`부터 계속 진행한다.

### 갱신 규칙

다음 시점에는 Current State, Next Action과 관련 결과를 갱신한다.

- Phase 변경
- Gate 통과 또는 실패
- Plan과 다른 구현 발생
- 새로운 blocker 발견
- 비싼 build 완료
- DB migration 또는 seed 실행
- Cloudflare 변경
- 세션 종료 전

명령 하나마다 로그를 복제하지 않는다. Steps에서 완료된 작업은 특별한 이유 없이 처음부터 반복하지 않으며, 대형 AI image rebuild, migration·seed 재실행, Cloudflare route 변경, Docker prune, volume 삭제는 현재 상태와 필요 이유를 먼저 확인한다.
