# SmartDrain Mac mini + OrbStack Migration Steps

이 문서는 migration 구현 중 지속적으로 갱신하는 실행 상태 및 인수인계 기록이다. 판단 근거는 Analysis, 실행 순서와 Gate는 Plan을 참조하며 이 문서에 복제하지 않는다.

## 0. Source of Truth

- Analysis: [`docs/verification/18_mac-mini-orbstack-migration-analysis.md`](../verification/18_mac-mini-orbstack-migration-analysis.md)
- Plan: [`docs/plans/plan-03-mac-mini-orbstack-migration.md`](../plans/plan-03-mac-mini-orbstack-migration.md)
- 작업 branch: `chore/macos-orbstack-migration`
- 구현 시작 기준 HEAD: `5ce2b52067ad9f69587b3c4730b55d1bbec5e409`
- 현재 HEAD: `5ce2b52067ad9f69587b3c4730b55d1bbec5e409`
- 마지막 갱신 시각: `2026-09-20 12:32:09 KST`

## 1. Current State

- 현재 Phase: Phase 2 — AI Linux/arm64 Verification
- 현재 Task: Task 2.2 — 동일 `best.pt` load와 YOLO CPU inference
- 현재 Gate: Gate A — 부분 검증 후 대기
- 현재 상태: `BLOCKED`
- Phase 1의 확정 runtime blocker 수정과 검증은 완료했다. Gate A는 신뢰 가능한 `best.pt`가 Mac에 없어 완료할 수 없다.

## 2. Next Action

**기존 VM에서 사용 중인 신뢰 가능한 `best.pt`를 Mac의 `SMARTDRAIN_YOLO_MODEL_PATH` 대상에 배치하고, 기존 VM 파일과 Mac 복사본의 크기·SHA256 일치를 확인한다.**

## 3. Completed Tasks

### 구현 전 문서 준비

- 수행 내용: Plan의 실행 기준, 운영 `.env` 이전, non-blocking 용량 진단, 조건부 VM 비교, 서버 lifecycle 검증을 최종 보정하고 Steps를 초기화했다.
- 실제 변경 파일:
  - `docs/plans/plan-03-mac-mini-orbstack-migration.md`
  - `docs/steps/step-03-mac-mini-orbstack-migration.md`
- 실행 명령: Git branch·HEAD·working tree 확인과 문서 정적 검토만 수행했다.
- 결과: migration 구현 Task는 아직 시작하지 않았다.
- 성공 여부: 성공. 필수 구조, source 문서 경로, branch·HEAD, whitespace를 확인했다.

### Phase 0 — Migration Preparation (부분 완료)

- 수행 내용: Mac `.env` 추적 제외 여부와 key를 값 노출 없이 비교하고, OrbStack Docker architecture·용량과 Compose 해석을 확인했다. Mac 전용 project name과 nginx bind 값을 조정했다.
- 실제 변경 파일: `.env` (Git 추적 제외, 비밀값 미출력)
- 실행 명령: key-only 비교, `docker compose config --quiet`, `docker version`, `docker info`, `docker system df`, 모델 파일 존재·크기 검사.
- 결과: OrbStack server는 `arm64/linux`, Compose config는 유효하며 `COMPOSE_DATABASE_URL`은 `db:5432`, Frontend는 same-origin이다. `.env.example` 대비 누락 key 10개는 모두 Compose 기본값이 있는 선택 항목이다. 기존 VM 기준 정보와 동일 `best.pt`는 미확보다.
- 성공 여부: 부분 성공. 모델과 기존 VM 근거가 남아 있어 Phase 0 종료 조건은 미충족이다.

### Phase 1 — Confirmed Runtime Blocker Fixes

- 수행 내용: Backend image layout, router import, Backend·AI sample 공급 경로를 기존 파일에서 직접 수정했다.
- 실제 변경 파일: `backend/Dockerfile`, `backend/app/main.py`, `ai_service/Dockerfile`.
- 실행 명령: Compose config, Python compile, Backend image build, container import·path assertion, `alembic heads`.
- 결과: Backend ARM64 image가 빌드됐고 `app.main` import, Alembic·sample 경로, head `20260623_0003`이 확인됐다. 최초 로컬 compile은 macOS Python cache 쓰기 권한 때문에 실패했지만 cache를 `/tmp`로 지정한 재검증은 성공했다.
- 성공 여부: 성공.

### Phase 2 — AI Linux/arm64 Verification (부분 완료)

- 수행 내용: AI runtime image를 Linux/arm64로 한 번 빌드하고 모델 없이 가능한 native import, OpenCV decode, XGBoost load·inference, 기존 pytest를 실행했다.
- 실제 변경 파일: 없음. Phase 1에서 수정한 `ai_service/Dockerfile` image를 사용했다.
- 실행 명령: `DOCKER_DEFAULT_PLATFORM=linux/arm64 docker compose build ai-service`, 동일 image의 진단 Python, `python -m pytest ai_service`.
- 결과: image architecture `arm64`, OpenCV decode와 XGBoost inference 성공, 기존 pytest `115 passed`. `torch 2.14.0+cu130`은 CPU에서 import됐고 `torch.cuda.is_available()`은 false였다.
- 성공 여부: 부분 성공. 실제 YOLO weight load·CPU inference와 smoke flow는 모델 부재로 미실행이다.

## 4. Gate Results

### Gate A

- 상태: `BLOCKED`
- 근거: Linux/arm64 image build, native dependency import, OpenCV decode, XGBoost load·inference, 기존 pytest 115개는 성공했다.
- 남은 위험: 동일 `best.pt` load·YOLO CPU inference, 기존 smoke flow, 실제 callback/status/result 계약을 검증해야 한다. VM 비교 조건이 확보되면 결과 계약도 비교한다.

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
| `.env` | 수정 | Mac 전용 Compose namespace와 nginx `127.0.0.1:8099` 적용 | 없음, Git 추적 제외 |
| `backend/Dockerfile` | 수정 | 앱·Alembic·sample을 runtime 기대 경로에 배치 | 없음 |
| `backend/app/main.py` | 수정 | 등록된 `realtime_simulator.router` 모듈 import 복구 | 없음 |
| `ai_service/Dockerfile` | 수정 | 운영 image에 기존 sample image 공급 | 없음 |

## 6. Commands Already Executed

| 분류 | 명령/작업 | 결과 |
| --- | --- | --- |
| 상태 확인 | `git status --short --branch`, branch, HEAD 확인 | branch와 기준 HEAD 확인 |
| 문서 검증 | 필수 section·핵심 문구 검색, source 문서 존재 확인, whitespace 검사 | 통과 |
| Backend build | `/usr/bin/time -p docker compose build backend` | 성공, 31.53초 |
| Backend packaging | container import·path assertion, `alembic heads` | 성공, head `20260623_0003` |
| AI build | Linux/arm64 `docker compose build ai-service` | 성공, 506.78초. 같은 source로 재실행 금지 |
| AI 부분 검증 | native import, OpenCV decode, XGBoost load·inference, 기존 pytest | 성공, `115 passed` |
| YOLO·smoke | 미실행 | `best.pt` 부재 |
| DB migration | 미실행 | Gate A 전 |
| DB seed | 미실행 | Gate A 전 |
| E2E | 미실행 | Gate A 전 |
| Cloudflare 변경 | 미실행 | Gate C 이후 별도 승인 경계 유지 |

## 7. Measurements

- AI build 시간: 506.78초
- Backend build 시간: 31.53초
- Frontend build 시간: 미측정
- image/cache 증가량: 최초 images 7.911GB·build cache 6.384GB, Backend build 후 8.94GB·7.073GB, AI build 후 25.94GB·17.39GB
- AI image logical size: 3,666,967,615 bytes
- Backend image logical size: 173,240,414 bytes
- 모델 load 시간: YOLO 미측정, XGBoost 0.006초
- inference 시간: YOLO 미측정, XGBoost 0.002초
- AI native import 시간: 4.084초
- Compose startup 시간: 미측정
- build 후 host 가용 공간: 136GiB

추정값은 기록하지 않는다. 실제 측정 뒤 해당 항목만 갱신한다.

## 8. Decisions / Deviations

- Plan의 Phase, Task, Gate를 실행 source of truth로 사용한다. 특정 agent 실행 framework는 필수가 아니다.
- Steps는 완료 후 일회성 보고서가 아니라 구현 중 갱신하는 상태 문서로 사용한다.
- Phase 0의 상세 image layer·cache 진단은 non-blocking 자료다.
- VM과 Mac의 결과 비교는 동일한 코드 경로와 artifact가 확보된 경우에 수행한다. 비교 불가 이유는 기록하되 그 사실만으로 Gate A를 실패 처리하지 않는다.
- Phase 0의 외부 artifact가 미확보인 상태에서 이에 의존하지 않는 Phase 1 수정과 Phase 2 image build·부분 검증을 먼저 수행했다. Gate A 이후 단계로는 진행하지 않는다.
- unpinned dependency 해석 결과 PyTorch와 XGBoost가 CUDA 13 관련 package를 포함했다. 이번 migration에서 dependency를 바꾸지 않고 실제 크기·CPU 동작 근거로 기록했으며, 최적화는 deferred 범위로 유지한다.
- Backend `docker compose run --no-deps`가 `smartdrain-mac` network와 빈 `postgres_data` volume을 생성했다. migration·seed는 실행하지 않았고 volume은 삭제하지 않았다.
- 큰 범위 변경이 필요하면 구현하지 않고 이 문서의 blocker와 근거를 먼저 갱신해 보고한다.
- 사용자 승인 필요 여부: 현재 없음. 실제 Docker·Compose·Cloudflare 변경 단계에서는 루트 `AGENTS.md`와 Plan의 승인 경계를 따른다.
- Plan 수정 여부: 이번 최종 보정 반영 완료.

## 9. Open Issues / Blockers

- `.env`의 `SMARTDRAIN_YOLO_MODEL_PATH`가 가리키는 파일이 존재하지 않는다. 동일 운영 `best.pt`의 Mac 복사본과 hash 일치가 필요하다.
- 기존 VM 접속 대상이나 실행 결과가 현재 workspace에 없어 운영 commit, 주요 AI dependency 버전, 모델 원본 hash를 확인하지 못했다.
- Gate A는 실제 YOLO load·CPU inference와 smoke flow 완료 전까지 닫혀 있다.

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
