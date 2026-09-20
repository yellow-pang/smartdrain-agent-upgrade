# SmartDrain Mac mini + OrbStack Migration Plan

> **실행 기준:** 이 문서의 Phase, Task, Gate를 source of truth로 사용한다. 특정 실행 framework나 서브에이전트는 필수가 아니며, 실제 작업에 도움이 될 때만 사용한다. 실행 편의를 이유로 불필요한 orchestration, 테스트, 문서를 추가하지 않는다.

**Goal:** 기존 SmartDrain 서비스 계약을 유지하면서 Apple Silicon Mac mini의 OrbStack에서 새 PostgreSQL을 포함한 전체 서비스를 재현하고, localhost 통합 검증 후 Cloudflare Tunnel을 안전하게 이전한다.

**Architecture:** 현재 `frontend → nginx → backend → ai-service → backend callback → PostgreSQL/WebSocket` 구조를 유지한다. 확인된 Docker 경로와 import 오류만 기존 파일에서 바로잡고, AI를 Linux/arm64 CPU에서 먼저 실추론한 뒤 전체 Compose, localhost, Cloudflare 순서로 Gate를 통과한다.

**Tech Stack:** Docker Compose, OrbStack Linux/arm64, PostgreSQL 16, FastAPI, Alembic, Python 3.12, Ultralytics/PyTorch, OpenCV, XGBoost, Next.js 16, Node.js 22, nginx, Cloudflare Tunnel.

**Spec:** [`docs/verification/18_mac-mini-orbstack-migration-analysis.md`](../verification/18_mac-mini-orbstack-migration-analysis.md)

## Global Constraints

- 기준 서비스 계약인 REST API, WebSocket payload, AI callback, DB schema를 변경하지 않는다.
- Python 3.12, Node.js 22, PostgreSQL 16과 현재 모델 파일 형식을 유지한다.
- `nvidia/cuda`, NVIDIA runtime, `platform: linux/amd64`, `.cuda()`를 새로 강제하지 않는다.
- 새 Dockerfile·Compose 파일, ARM 전용 코드 분기, 새 배포·테스트 framework를 추가하지 않는다.
- AI 이미지 최적화, dependency pinning, CI/CD, multi-arch는 Mac 이전 성공 조건과 분리한다.
- 실제 비밀값은 Git, 문서, 명령 출력, 로그에 기록하지 않는다.
- 기존 VM, 기존 PostgreSQL, 기존 image·volume, 기존 Cloudflare 경로는 Server Lifecycle Verification 통과 전까지 보존한다.
- 새 Mac 데이터베이스는 기존 VM 데이터와 분리된 새 Compose volume을 사용한다.
- 구현·외부 설정 변경은 이 Plan 승인 후 진행하며, Cloudflare 전환은 localhost Gate 통과 뒤 별도 승인 경계로 둔다.

## Review Focus

아래 실패 유형은 각 소유 Phase에서 한 번씩 검증한다. 같은 조건을 이름만 바꿔 다른 계층에서 반복하지 않는다.

1. `best.pt`가 없거나 비어 있거나 다른 모델인 경우: Phase 0의 크기·SHA256 기록과 Phase 2의 실제 모델 load가 소유한다.
2. Linux/arm64 native wheel 또는 연산이 호환되지 않는 경우: Phase 2의 architecture·import·CPU inference가 소유한다.
3. 컨테이너 안의 앱·Alembic·sample 경로가 서로 어긋나는 경우: Phase 1의 image layout·import 검증이 소유한다.
4. 빈 PostgreSQL에서 migration·seed·DB 연결이 재현되지 않는 경우: Phase 3의 새 volume bring-up이 소유한다.
5. health는 성공하지만 분석 callback·저장·WebSocket·화면 반영이 끊기는 경우: Phase 4의 localhost E2E가 소유한다.

---

## 1. 목적

기존 Windows 노트북의 Linux VM에 있던 SmartDrain 실행 환경을 Apple Silicon Mac mini + OrbStack으로 옮긴다. 성공 기준은 컨테이너가 단순히 `healthy`가 되는 것이 아니라 다음 흐름이 새 PostgreSQL에서 실제로 이어지는 것이다.

```text
Mac mini
  → OrbStack Linux/arm64
  → Docker Compose
      ├─ PostgreSQL 16
      ├─ backend
      ├─ ai-service
      ├─ frontend
      └─ nginx
  → http://127.0.0.1:8099 localhost E2E
  → Cloudflare Tunnel
  → 공개 HTTPS/WSS E2E
```

기존 VM은 비교 기준과 즉시 복귀 경로로 유지한다. 기존 DB 데이터·image·volume 전체를 Mac으로 복사하는 작업은 수행하지 않는다.

## 2. 기준 Analysis

### 기준 문서와 Git 기준

- 기준 문서: [`18_mac-mini-orbstack-migration-analysis.md`](../verification/18_mac-mini-orbstack-migration-analysis.md)
- Analysis 기준: `dev`, `5cd6c07dac1e6abd7845307a88e681f9ad1aa36f`
- Plan 작성 브랜치: `chore/macos-orbstack-migration`
- Plan 작성 시작 HEAD: `277e16727087bc0ccc1f4ae880a529063030d97b`

Analysis의 역할은 사전 분석과 사실 확인이다. 구현 순서, Gate, rollback, 완료 조건과 후속 최적화는 이 Plan이 담당한다.

### 이미 확인된 사실

- CUDA base image, NVIDIA runtime, GPU reservation, `linux/amd64` 강제, `.cuda()` 강제는 발견되지 않았다.
- 확정적인 ARM blocker는 발견되지 않았다.
- Linux/arm64 CPU에서 실제 `best.pt`와 XGBoost 추론 검증이 남아 있다.
- Backend Dockerfile의 Alembic COPY, 앱 배치·실행 경로, sample 경로가 현재 구조와 맞지 않는다.
- `backend/app/main.py`는 `realtime_simulator.router`를 등록하지만 해당 모듈을 import하지 않는다.
- AI runtime image는 `ai_service/`만 COPY하므로 기본 image source가 참조하는 `/app/mock_data/ai_image_samples`가 없다.
- Compose에는 PostgreSQL migration, 선택적 seed, nginx same-origin proxy, 외부 YOLO weight mount 구조가 이미 있다.
- 기본 Compose에서 host에 publish되는 서비스는 nginx뿐이며 `NGINX_HTTP_PORT`로 `127.0.0.1:8099`를 표현할 수 있다.

### 아직 실행 검증이 필요한 사실

- Mac에서 선택되는 Python·native dependency 조합과 image 크기.
- 동일 `best.pt`의 Linux/arm64 CPU load·inference.
- 새 PostgreSQL volume에 대한 Alembic migration과 seed.
- 전체 Compose startup과 재기동 재현성.
- localhost의 REST·WebSocket·image·AI callback·DB 저장·화면 반영.
- Cloudflare를 통한 HTTPS·WSS 접근과 domain-dependent 외부 설정.

### Analysis 수정 판단

Analysis에는 Plan 작성을 막는 사실 오류, 코드와의 모순, 중요 누락, 잘못된 ARM blocker 결론이 없다. **이번 Plan 작성에서는 Analysis를 수정하지 않는다.** 실행 결과가 기존 사실을 뒤집을 때만 구현 완료 기록에서 근거를 남기고 Analysis의 정정 필요성을 별도로 판단한다.

## 3. Scope

### In Scope

- 기존 VM의 배포 commit·AI dependency·모델 식별 정보를 읽기 전용으로 기록한다.
- 기존 VM 운영 `.env`를 Mac의 추적 제외 `.env`로 안전하게 복사하고, Mac 환경 차이가 있는 값만 조정한다.
- 기존 Backend Dockerfile의 COPY·실행 경로를 정상화한다.
- 기존 Backend router import 누락을 수정한다.
- Backend와 AI runtime image에 현재 코드가 기대하는 sample 경로를 제공한다.
- AI image를 Linux/arm64로 build하고 실제 YOLO·XGBoost CPU inference를 검증한다.
- 새 PostgreSQL volume으로 전체 Compose를 기동하고 migration·seed·DB 연결을 검증한다.
- `http://127.0.0.1:8099`에서 전체 사용자 흐름을 검증한다.
- localhost Gate 통과 후 Cloudflare Tunnel을 Mac nginx로 전환하고 공개 흐름을 검증한다.
- 구현 전에 Steps 문서를 실행 상태 기록으로 초기화하고, 정해진 checkpoint마다 실제 변경·검증·차이와 다음 작업을 갱신한다.

### Out of Scope

- 기존 PostgreSQL 데이터 이전.
- 기존 VM image·volume·Docker cache 복사 또는 삭제.
- DB schema·Alembic revision 변경.
- REST·WebSocket·AI callback 계약 변경.
- AI 알고리즘, YOLO weight, XGBoost model 변경.
- Python·Node·PostgreSQL major/minor runtime 업그레이드.
- ONNX, TensorRT, quantization, 새 inference framework.
- AI image 10GB 최적화, CPU-only dependency 재구성, requirements 전체 pinning.
- GHCR, GitHub Actions, multi-arch build, 자동 rollback.
- Jenkins 제거 또는 기존 Jenkins 변경.
- 모델 runtime download 구조.
- 기존 VM 종료·폐기.

### 승인 경계

1. 이 Plan 승인 후에만 Dockerfile·Compose 관련 구현과 로컬 실행을 시작한다.
2. Phase 5의 Cloudflare Tunnel 변경은 Gate C 통과 결과를 제시한 뒤 별도로 진행한다.
3. 기존 VM 종료·image/volume 삭제는 이 Plan 완료 후에도 별도 작업과 승인으로 남긴다.

## 4. 핵심 설계 원칙

### 최소 완결 변경

최소 변경은 코드 줄 수가 아니라 현재 서비스가 재기동 후에도 재현되는 가장 작은 완결된 변경을 뜻한다. 일회성 bind mount, 로컬 shell wrapper, 수동 container 내부 복사로 성공 처리하지 않는다.

### 서비스 계약 유지

- Frontend는 nginx의 same-origin `/api`와 `/ws`를 사용한다.
- Backend는 DB 저장·AI 요청·callback·WebSocket broadcast 책임을 유지한다.
- AI는 현재 image source, YOLO, XGBoost, callback 책임을 유지한다.
- 데이터 모델, migration, API payload, 상태 enum은 바꾸지 않는다.

### Migration과 Optimization 분리

현재 dependency가 크더라도 ARM에서 build·inference가 가능하고 Mac 저장공간을 즉시 고갈시키지 않으면 이전을 먼저 완료한다. image 최적화는 측정 결과를 근거로 후속 작업에서 다룬다.

### 테스트 중복 방지

```text
정적/config 검증       → 경로·import·Compose 해석 실패
AI ARM inference       → native dependency·모델·CPU 연산 실패
Compose integration    → DB migration·서비스 dependency·health 실패
localhost E2E          → 실제 API·callback·저장·WebSocket·화면 실패
Cloudflare E2E         → 공개 HTTPS/WSS·domain 설정 실패
```

하위 계층에서 이미 검증한 내용을 상위 계층에서 다시 단독 테스트하지 않는다. 상위 계층은 연결된 사용자 흐름을 검증한다.

### Additive-only 수정 방지

- 잘못된 Backend COPY 명령은 제거·교체한다.
- 누락된 import는 기존 import 목록에 추가한다.
- AI sample은 기존 Dockerfile의 runtime filesystem에 포함한다.
- Mac 전용 Dockerfile, migration Compose, wrapper script, test-only production branch는 만들지 않는다.

### 구현 대안과 선택

| 문제 | 대안 | 판단 |
| --- | --- | --- |
| Backend 경로 | 기존 Dockerfile 수정 / Mac 전용 Dockerfile 추가 | 기존 Dockerfile 수정 선택. 모든 architecture의 동일 결함을 제거한다. |
| Sample 공급 | image COPY / host bind mount / runtime download | 기존 Git 추적 sample을 image COPY하는 방식 선택. 재기동·다른 host에서 재현 가능하며 외부 저장소가 필요 없다. |
| ARM 대응 | native arm64 / 즉시 amd64 emulation | native arm64 우선. 실제 blocker가 확인될 때만 emulation을 진단 대안으로 검토한다. |
| 테스트 | 새 framework·다수 회귀 테스트 / 기존 test·smoke·E2E 재사용 | 기존 검증 재사용 선택. Docker packaging은 실제 image와 runtime으로 확인한다. |
| DB | 기존 데이터 복사 / 새 volume+migration+seed | 새 volume 선택. 이전 성공 조건에 데이터 이관을 추가하지 않는다. |

## 5. Phase 0 - Migration Preparation

**목적:** 코드를 바꾸기 전에 필수 비교 기준, 모델, 운영 환경값과 복귀 경로를 준비한다. 상세 image layer·cache 진단은 가능하면 기록하되 migration 진행 조건으로 사용하지 않는다.

### Task 0.1 — 기준 상태 기록

- [ ] 기존 VM에서 현재 운영 checkout의 commit을 읽기 전용으로 기록한다.
- [ ] 실제 실행 중인 Compose project와 컨테이너 image ID·architecture를 기록한다.
- [ ] 실행 중인 AI 컨테이너에서 주요 AI dependency 버전을 읽기 전용으로 기록하되 secret·환경변수는 출력하지 않는다.
- [ ] 가능하면 기존 VM의 `docker system df -v`, AI image `docker history --no-trunc`, shared·unique layer 정보를 기록한다. 이 자료를 얻지 못해도 migration을 중단하지 않는다.
- [ ] 기록된 commit이 Analysis 기준과 다르면 구현을 중단하지 않고 차이 파일을 먼저 확인한다. blocker 수정 대상이 해당 차이에서 이미 해결되었거나 변경되었다면 Plan을 갱신하고 승인을 다시 받는다.

기존 VM에서 사용할 명령의 형태는 다음과 같다. 실제 Compose project·container 이름은 `docker compose ps` 결과로 확정하고 placeholder를 그대로 실행하지 않는다.

```bash
cd /home/yp/apps/smart-drain
git rev-parse HEAD
docker compose ps
docker system df -v
docker history --no-trunc smartdrain-dev-ai-service:latest
docker exec <실행중인-ai-container> python -m pip freeze
```

### Task 0.2 — 모델 artifact 확인

- [ ] 기존 VM에서 실제 사용 중인 `best.pt`의 크기와 SHA256을 기록한다.
- [ ] 동일 파일을 Mac의 Git 외부 고정 경로에 복사한다.
- [ ] Mac 복사본의 크기와 SHA256이 기존 VM 기록과 일치하는지 확인한다.
- [ ] 저장소가 추적하는 `ai_service/model/sewer_xgboost_model.json`은 현재 Git 버전을 사용하고 별도 복사본을 만들지 않는다.
- [ ] 모델 파일 자체, hash 이외 메타데이터, 실제 경로에 포함된 사용자 정보는 Git 문서에 기록하지 않는다.

Linux와 macOS 확인 명령:

```bash
# 기존 Linux VM
stat -c '%s bytes' <기존-best.pt-절대경로>
sha256sum <기존-best.pt-절대경로>

# Mac
stat -f '%z bytes' <Mac-best.pt-절대경로>
shasum -a 256 <Mac-best.pt-절대경로>
```

### Task 0.3 — Mac 환경값과 격리된 DB 준비

- [ ] 기존 VM 운영 `.env`를 Mac의 Git 추적 제외 루트 `.env`로 안전하게 복사한다. `.env.example`을 근거로 운영 값을 추측하거나 새로 작성하지 않는다.
- [ ] `.env.example`과는 key 존재 여부만 비교하고 실제 값을 출력·문서화하지 않는다. 기존 운영 `.env`에 없는 신규 필수 key가 발견된 경우에만 별도로 보고한다.
- [ ] `COMPOSE_PROJECT_NAME=smartdrain-mac`처럼 기존 로컬 project와 충돌하지 않는 이름을 사용해 새 `postgres_data` volume namespace를 만든다.
- [ ] 복사한 값 중 `SMARTDRAIN_YOLO_MODEL_PATH`만 Mac의 실제 non-empty `best.pt` 절대경로로 조정한다.
- [ ] PostgreSQL 관련 값은 새 Mac DB 자격정보와 `db:5432` host가 서로 일치하도록 조정한다.
- [ ] `NGINX_HTTP_PORT=127.0.0.1:8099`로 설정한다.
- [ ] Frontend 관련 값은 기존 nginx same-origin `/api`, `/ws` 계약을 유지하도록 조정한다.
- [ ] Kakao 지도 공개 키와 localhost 허용 설정을 확인한다. secret 값은 기록하지 않는다.
- [ ] 기존 VM, 기존 DB, 기존 Cloudflare 설정은 변경하지 않는다.

환경 파일을 출력하지 않는 검증:

```bash
docker compose config --quiet
docker compose config --services
```

### Phase 0 종료 조건

- 기존 VM commit, 주요 AI dependency 버전, 기존 운영 환경 설정이 확인되어 있다.
- 동일 SHA256의 `best.pt`가 Mac에 있다.
- Compose config가 secret 출력 없이 성공한다.
- 새 Mac DB volume namespace와 `127.0.0.1:8099`가 준비되어 있다.
- 기존 VM과 Cloudflare 경로는 그대로 동작한다.

`docker system df -v`, image history, shared·unique layer 상세 자료는 이 종료 조건에 포함하지 않는다. 확보한 경우에만 Steps의 Measurements에 기록한다.

## 6. Phase 1 - Confirmed Runtime Blocker Fixes

**목적:** Analysis에서 확정된 일반 Docker/Application blocker만 기존 파일에서 제거한다.

### 예상 변경 파일과 변경 성격

| 파일 | 현재 문제 | 계획된 변경 | 성격 | 계약 영향 | ARM 전용 여부 |
| --- | --- | --- | --- | --- | --- |
| `backend/Dockerfile` | 존재하지 않는 루트 `alembic.ini` COPY, 앱이 `/app/backend/backend/app`에 배치됨 | `backend/alembic.ini`, `backend/alembic/`, `backend/app/`을 WORKDIR 기준의 `alembic.ini`, `alembic/`, `app/`에 배치하고 `mock_data/`는 `/app/mock_data/`에 배치 | 기존 잘못된 COPY 제거·교체 | 없음 | 아니오 |
| `backend/app/main.py` | `realtime_simulator.router`를 쓰지만 모듈 import 누락 | 기존 `app.routers` import 목록에 `realtime_simulator` 추가 | 기존 코드 수정 | 없음 | 아니오 |
| `ai_service/Dockerfile` | 기본 image source가 요구하는 sample이 runtime image에 없음 | Git 추적 `mock_data/ai_image_samples/`를 `/app/mock_data/ai_image_samples/`에 COPY하고 기존 appuser 소유권 처리에 포함 | 기존 파일에 COPY 추가 | 없음 | 아니오 |
| `docs/steps/step-03-mac-mini-orbstack-migration.md` | 구현·실측 기록 없음 | Phase별 실제 변경, 명령, 결과, 계획 차이와 남은 위험 기록 | 새 문서 추가 | 없음 | 아니오 |

예상하지 않는 변경:

- `docker-compose.yml`: 기존 build·model mount·port 변수로 충분하므로 수정하지 않는다.
- `.env.example`: 필요한 key가 이미 존재하므로 환경변수 구조를 바꾸지 않는다.
- Backend·AI application service: 알고리즘·callback·DB 로직을 바꾸지 않는다.
- 새 test 파일: 먼저 추가하지 않는다. 실제 기존 검증이 잡지 못하는 회귀가 확인될 때만 Plan 수정 후 검토한다.

### Task 1.1 — Backend image layout 정상화

- [ ] `backend/Dockerfile`의 잘못된 `COPY alembic.ini ./`, `COPY backend/ ./backend/`, `COPY mock_data/ ./mock_data/`를 제거한다.
- [ ] 기존 WORKDIR와 `PYTHONPATH=/app/backend`에 맞게 Alembic 설정·revision·app을 직접 배치한다.
- [ ] Backend가 참조하는 project root가 `/app`이 되도록 sample을 `/app/mock_data`에 배치한다.
- [ ] dependency install 순서는 유지해 requirements layer cache를 보존한다.
- [ ] 현재 불필요해 보이는 Backend OpenCV OS package 제거는 image 최적화로 분류해 하지 않는다.

### Task 1.2 — Router import 복구

- [ ] `backend/app/main.py`의 기존 router import에 `realtime_simulator`를 추가한다.
- [ ] router 등록 순서·path·handler를 변경하지 않는다.
- [ ] test-only import, fallback, 조건부 ARM 분기를 추가하지 않는다.

### Task 1.3 — AI runtime sample 공급

- [ ] `ai_service/Dockerfile`에서 기존 `ai_service/` COPY와 함께 필요한 sample 디렉터리를 image에 포함한다.
- [ ] `/app/ai_service/model/best.pt` 외부 read-only mount와 저장소의 XGBoost JSON 포함 방식을 유지한다.
- [ ] Compose의 일회성 sample bind mount나 runtime download로 우회하지 않는다.
- [ ] sample 포함으로 추가되는 layer 크기를 Phase 2에서 측정한다. image 최적화로 확장하지 않는다.

### Task 1.4 — Blocker 수정 검증

Backend image는 한 번 build하고 다음 검증에서 재사용한다.

```bash
docker compose config --quiet
docker compose build backend
docker compose run --rm --no-deps backend \
  python -c "from pathlib import Path; import app.main; assert Path('/app/backend/alembic.ini').is_file(); assert Path('/app/backend/alembic/versions').is_dir(); assert Path('/app/mock_data/ai_image_samples/drain_2.jpg').is_file()"
docker compose run --rm --no-deps backend alembic heads
```

성공 조건:

- build가 없는 source COPY 오류 없이 끝난다.
- `import app.main`이 `NameError` 없이 끝난다.
- 컨테이너 안의 앱·Alembic·sample 경로가 코드가 기대하는 위치와 일치한다.
- Alembic head가 현재 migration chain의 head로 해석된다.

실패 의미:

- 이 단계의 실패는 ARM 모델 문제가 아니라 Docker context, Python import, Alembic packaging 문제다.
- 수정 후 같은 명령만 반복한다. 전체 Compose나 Cloudflare로 우회하지 않는다.

## 7. Phase 2 - AI Linux/arm64 Verification

**목적:** 전체 시스템 전에 동일 모델의 Linux/arm64 CPU 추론 가능성을 판정한다.

### Task 2.1 — AI image 단일 build와 비용 기록

- [ ] 사용 가능한 Mac disk를 확인한다. 가능하면 build 전 `docker system df -v`도 기록한다.
- [ ] `DOCKER_DEFAULT_PLATFORM=linux/arm64`로 `ai-service` runtime image를 한 번 build한다.
- [ ] wall-clock build 시간과 cache hit 여부를 기록한다.
- [ ] image architecture는 반드시 확인하고, compressed/logical size와 shared·unique layer는 가능한 범위에서 기록한다.
- [ ] 같은 source·requirements 상태에서 이유 없이 `--no-cache` build를 반복하지 않는다.

```bash
docker system df -v
/usr/bin/time -p env DOCKER_DEFAULT_PLATFORM=linux/arm64 \
  docker compose build ai-service
docker compose images ai-service
```

Clean environment 재현성은 이번 host의 warm cache 결과만으로 확정하지 않는다. build log에서 requirements layer가 재사용되었는지 함께 기록하고, 후속 CI 도입 시 clean build를 별도 측정한다.

### Task 2.2 — Architecture·native import·실제 inference

아래 한 번의 진단 실행에서 architecture, native import, OpenCV decode, YOLO load·CPU inference, XGBoost load·inference를 확인한다. Phase 1 이후 sample은 image 안에 있어야 하므로 진단용 volume을 추가하지 않는다.

```bash
DOCKER_DEFAULT_PLATFORM=linux/arm64 \
docker compose run --rm --no-deps -T ai-service python - <<'PY'
import platform
from pathlib import Path

import cv2
import numpy as np
import torch
import torchvision
import xgboost

from ai_service.yolo.analyzer import YoloV3ImageAnalyzer
from ai_service.xgboost.model_predictor import TrainedXGBoostPredictor

assert platform.machine() == "aarch64", platform.machine()
sample_path = Path("/app/mock_data/ai_image_samples/drain_2.jpg")
assert sample_path.is_file() and sample_path.stat().st_size > 0

image_bytes = np.fromfile(str(sample_path), np.uint8)
decoded = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
assert decoded is not None

yolo = YoloV3ImageAnalyzer()
yolo_results = yolo.model.predict(decoded, device="cpu", verbose=False)
assert len(yolo_results) == 1

xgb = TrainedXGBoostPredictor()
features = [[0.2, 0.9, 30.0, 0.8]]
prediction = xgb.model.predict(features)
probabilities = xgb.model.predict_proba(features)
assert len(prediction) == 1 and len(probabilities) == 1

print("architecture:", platform.machine())
print("torch:", torch.__version__)
print("torchvision:", torchvision.__version__)
print("opencv:", cv2.__version__)
print("xgboost:", xgboost.__version__)
print("cuda_available:", torch.cuda.is_available())
print("YOLO CPU inference: OK")
print("XGBoost inference: OK")
PY
```

`cuda_available: False`는 Apple Silicon Linux container의 CPU 기준에서는 실패가 아니다. import error, illegal instruction, model deserialization 오류, decode 실패, CPU predict 실패를 blocker로 본다.

### Task 2.3 — 기존 AI 계약과 orchestration 검증

실제 추론과 역할이 다른 기존 검증만 한 번씩 재사용한다.

```bash
docker compose run --rm --no-deps ai-service \
  python -m pytest ai_service

/usr/bin/time -p docker compose run --rm --no-deps ai-service \
  python -m ai_service.scripts.smoke_analysis --drain-id 2
```

- pytest는 모델 adapter·validation·callback payload 등 기존 계약 회귀를 검사한다. 실제 weight 추론을 대신하지 않는다.
- 직접 inference는 native runtime 실패를 노출한다. `smoke_analysis`의 unknown fallback으로 가려지지 않게 먼저 실행한다.
- `smoke_analysis`는 image source → YOLO → XGBoost → callback payload 조합을 검사하되 실제 Backend callback은 보내지 않는다.

### Task 2.4 — 기존 VM과 결과 계약 비교

- [ ] 비교 가능한 코드 경로, 동일 SHA256 `best.pt`, 동일 sample, 동일 XGBoost artifact가 모두 확보된 경우에만 기존 VM과 Mac의 결과를 비교한다.
- [ ] bit-level score 동일성을 무조건 요구하지 않는다.
- [ ] 다음 계약을 비교한다: 필수 callback key, `request_id`·`job_id` 연결, `yolo_status` 허용 enum, obstruction/confidence 범위, XGBoost `risk_level`·`final_decision` enum, feature snapshot key, 예외 없는 완료.
- [ ] 비교 조건을 확보하지 못하면 비교 불가 이유를 Steps에 기록한다. 비교 불가만으로 Mac의 정상적인 ARM 실행을 실패로 판정하지 않는다.
- [ ] 의미 있는 status·classification 차이가 있으면 dependency·architecture 차이로 분류하고 Gate A를 닫는다. 허용 오차를 즉석에서 만들어 통과시키지 않는다.

### Gate A — AI ARM inference

다음이 모두 충족되어야 Phase 3으로 진행한다.

- image 내부 architecture가 `aarch64`다.
- native dependency import와 OpenCV decode가 성공한다.
- 동일 `best.pt`가 CPU에서 load·predict된다.
- XGBoost JSON이 load·predict된다.
- 기존 pytest와 `smoke_analysis`가 성공한다.
- 현재 SmartDrain이 사용하는 callback·status·result 계약이 유지된다.
- 비교 조건이 확보된 경우 기존 VM과의 결과 계약 비교가 성공한다. 조건을 확보하지 못한 경우 Steps에 이유가 기록되어 있다.
- image·cache가 Mac의 가용 저장공간을 위협하지 않는다. 위험 수준의 기준은 build 후 여유 공간과 추가 build 필요량을 측정해 판단하며 임의 GB를 사전 기준으로 두지 않는다.

실패 시 Phase 3으로 진행하지 않는다. 먼저 wheel 부재, 모델 serialization, native library, 실제 NVIDIA custom op 여부를 분류한다. amd64 emulation이나 dependency 변경이 필요하면 범위 변경으로 보고하고 Plan을 갱신한다.

## 8. Phase 3 - Full Compose Bring-up

**목적:** Gate A를 통과한 AI image를 재빌드하지 않고 새 PostgreSQL부터 nginx까지 기존 dependency 순서로 기동한다.

### Task 3.1 — 나머지 image build

- [ ] Phase 1에서 만든 Backend image의 cache 재사용 여부를 확인한다.
- [ ] Frontend production image를 build한다.
- [ ] AI는 Phase 2 image를 그대로 사용하고 이 단계에서 다시 build하지 않는다.

```bash
/usr/bin/time -p docker compose build backend frontend
```

Frontend build 실패는 ARM native frontend package, lockfile, build-time 공개 환경값으로 분류한다. runtime이나 package version을 즉시 올리지 않는다.

### Task 3.2 — 새 DB와 전체 dependency 기동

- [ ] project 이름이 Mac 전용인지 `docker compose config`로 확인한다.
- [ ] `docker compose up --detach`를 `--build` 없이 실행한다.
- [ ] Compose가 `db healthy → migrate exited 0 → backend healthy → ai-service → frontend → nginx` 조건을 충족하는지 확인한다.
- [ ] 실패 시 해당 서비스 log만 먼저 확인한다. image prune, volume 삭제, 전체 rebuild를 첫 대응으로 사용하지 않는다.

```bash
/usr/bin/time -p docker compose up --detach
docker compose ps --all
docker compose logs --tail=100 db migrate backend ai-service frontend nginx
```

### Task 3.3 — Migration·schema·DB 연결 검증

- [ ] `migrate`가 exit code 0인지 확인한다.
- [ ] `alembic_version`이 현재 head인지 확인한다.
- [ ] 핵심 5개 table인 `drains`, `sensor_data`, `yolo_results`, `xgboost_results`, `analysis_jobs`가 생성되었는지 확인한다.
- [ ] Backend health와 DB 기반 dashboard API가 빈 DB에서도 오류 없이 응답하는지 확인한다.
- [ ] localhost E2E용 데이터가 필요하므로 migration 검증 후 seed profile을 한 번 실행한다.
- [ ] seed 재실행은 idempotency를 별도로 재검증할 필요가 생긴 경우에만 수행한다.

```bash
docker compose exec -T db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select version_num from alembic_version"'
docker compose exec -T db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select tablename from pg_tables where schemaname = '\''public'\'' order by tablename"'
docker compose exec -T backend python -c \
  "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/api/dashboard/summary').status)"
docker compose --profile seed run --rm seed
```

### Task 3.4 — 재기동 재현성

- [ ] `docker compose restart` 후 health가 다시 수렴하는지 확인한다.
- [ ] PostgreSQL volume data와 seed 결과가 유지되는지 dashboard API로 확인한다.
- [ ] host에서 수동 복사한 container 내부 파일에 의존하지 않았음을 확인한다.

```bash
docker compose restart
docker compose ps --all
curl --fail --silent --show-error \
  http://127.0.0.1:8099/api/dashboard/summary
```

### Gate B — 새 PostgreSQL과 전체 Compose

- migration exit 0, 현재 Alembic head, 핵심 table 생성이 확인된다.
- Backend가 새 DB에 연결하고 seed 이후 데이터를 조회한다.
- AI·Frontend·nginx를 포함한 필수 장기 실행 서비스가 healthy다.
- restart 후 같은 상태로 복구된다.
- Gate A에서 만든 AI image가 추가 rebuild 없이 사용된다.

Gate B 실패 시 localhost 기능 검증으로 진행하지 않는다. migration, image, 환경값, health dependency 중 실패 계층을 먼저 분리한다.

## 9. Phase 4 - Localhost Integration Verification

**목적:** Cloudflare 변경 전에 `http://127.0.0.1:8099`에서 실제 사용자 흐름을 끝까지 확인한다.

### Task 4.1 — nginx·Frontend·REST·image

- [ ] 브라우저에서 대시보드와 시설 상세 화면을 연다.
- [ ] nginx를 통한 frontend HTML과 dashboard REST API가 응답하는지 확인한다.
- [ ] seed가 연결한 sample image URL이 nginx → Backend StaticFiles 경로로 non-empty 응답하는지 확인한다.
- [ ] 직접 Backend port가 host에 publish되지 않았는지 `docker compose ps`로 확인한다.

```bash
curl --fail --silent --show-error --output /dev/null \
  http://127.0.0.1:8099/
curl --fail --silent --show-error \
  http://127.0.0.1:8099/api/dashboard/summary
curl --fail --silent --show-error --output /dev/null \
  http://127.0.0.1:8099/api/mock-images/drain_2.jpg
docker compose ps
```

### Task 4.2 — WebSocket 연결 기준선

- [ ] 브라우저 개발자 도구의 Network에서 `ws://127.0.0.1:8099/ws/drains/status`가 연결되는지 확인한다.
- [ ] 페이지 초기 데이터와 연결 상태 UI가 오류 없이 표시되는지 확인한다.
- [ ] 별도 WebSocket package나 test client를 추가하지 않는다. Task 4.3의 실제 분석 이벤트로 연결을 함께 검증한다.

### Task 4.3 — 실제 분석·callback·저장·화면 반영 E2E

브라우저에서 DR-002 화면과 WebSocket frame을 관찰한 상태에서 다음 요청을 한 번 수행한다.

```bash
curl --fail --silent --show-error \
  -H 'Content-Type: application/json' \
  -d '{"drainId":"DR-002"}' \
  http://127.0.0.1:8099/api/analysis/async-run
```

- [ ] 응답의 `requestId`, `jobId`, 초기 `status`를 기록한다.
- [ ] AI log에서 동일 request/job의 분석 완료와 두 callback 전송 결과를 확인한다.
- [ ] DB의 해당 `analysis_jobs`가 `completed`이고 `yolo_result_id`가 연결됐는지 확인한다.
- [ ] `/api/drains/DR-002/analysis/history`에서 새 YOLO·XGBoost 결과가 조회되는지 확인한다.
- [ ] WebSocket에서 분석 결과 또는 drain 상태 이벤트가 수신되는지 확인한다.
- [ ] 새로고침 없이 Frontend의 해당 시설 상태·분석 정보가 반영되는지 확인한다.
- [ ] 화면 새로고침 후에도 DB 저장 결과가 유지되는지 확인한다.

request ID를 shell에 직접 넣을 때는 응답에서 확인한 실제 값으로 치환한다.

```bash
docker compose logs --tail=120 ai-service backend
docker compose exec -T db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select request_id, job_id, status, yolo_result_id from analysis_jobs order by id desc limit 1"'
curl --fail --silent --show-error \
  'http://127.0.0.1:8099/api/drains/DR-002/analysis/history?limit=1'
```

`healthy`, `/health`, dashboard GET만으로 Task 4.3을 대체하지 않는다. 이 단계는 Backend → AI → 두 callback → DB → WebSocket → Frontend 연결 전체가 소유한다.

### Gate C — Localhost E2E

- Frontend, REST, sample image가 nginx 단일 진입점으로 동작한다.
- WebSocket이 연결되고 실제 분석 이벤트를 전달한다.
- 실제 YOLO·XGBoost 추론이 callback으로 돌아와 DB에 저장된다.
- Frontend가 새로고침 없이 결과를 반영하고 새로고침 뒤에도 유지한다.
- Backend·DB·AI port는 host에 별도 공개되지 않는다.
- 실패·재시작 후에도 같은 절차로 재현된다.

Gate C 통과 전에는 Cloudflare 설정을 변경하지 않는다.

## 10. Phase 5 - Cloudflare Migration

**목적:** 검증된 localhost nginx를 공개 origin으로 연결하되 앱 계약을 바꾸지 않는다.

### Task 5.1 — 전환 전 안전 확인

- [ ] Gate C 결과와 실행 시각을 Steps 문서에 기록한다.
- [ ] 기존 VM Tunnel 이름·hostname·origin과 현재 정상 상태를 기록한다. credential은 기록하지 않는다.
- [ ] Mac cloudflared 설치·로그인·새 Tunnel 연결 방식을 Cloudflare 공식 절차로 준비한다.
- [ ] Mac Tunnel origin은 `http://localhost:8099`로 둔다.
- [ ] 기존 VM Tunnel과 route를 삭제하거나 중지하지 않는다.
- [ ] 실제 Cloudflare 변경 전에 사용자에게 대상 hostname과 복귀 origin을 제시한다.

### Task 5.2 — Tunnel 연결과 hostname 전환

- [ ] 가능하면 최종 hostname을 바꾸기 전에 별도 검증 hostname으로 Mac Tunnel → localhost 연결을 검사한다.
- [ ] 최종 hostname route를 Mac Tunnel로 전환한다.
- [ ] Cloudflare 때문에 Frontend API base, WebSocket path, nginx location을 재설계하지 않는다.
- [ ] 도메인이 기존과 달라질 때만 Kakao 지도 허용 도메인과 명시적 CORS origin을 갱신한다.
- [ ] cloudflared가 Mac host에서 실행되는 경우 `localhost:8099`를 사용한다. 컨테이너화는 이번 범위에 추가하지 않는다.

### Task 5.3 — 공개 E2E

- [ ] HTTPS Frontend와 REST API를 확인한다.
- [ ] 브라우저에서 WSS `/ws/drains/status` 연결을 확인한다.
- [ ] sample image와 Kakao 지도를 확인한다.
- [ ] 실제 분석 요청 한 건으로 callback·DB 저장·WebSocket·Frontend 반영을 확인한다.
- [ ] 외부 공개 응답에 Backend·AI·DB port가 노출되지 않는지 확인한다.

### Gate D — Cloudflare 공개 검증

- 공개 HTTPS, REST, WSS, image, 지도, 분석 E2E가 모두 성공한다.
- 기존 서비스 계약과 URL path가 유지된다.
- 장애 시 기존 VM origin으로 되돌릴 정보와 권한이 확보되어 있다.
- Gate D 통과 후에도 즉시 VM을 삭제하지 않는다. 관찰 기간과 종료는 별도 결정으로 남긴다.

### Task 5.4 — Server Lifecycle Verification

Gate D 통과 후 현재 OrbStack, Compose, cloudflared 설정이 제공하는 복구 방식을 먼저 확인한다. 자동 시작이 없다는 이유만으로 새 daemon, framework, wrapper를 즉시 추가하지 않는다. 기존 구조로 서버 운영 요구를 충족할 수 없을 때만 필요한 최소 설정과 영향을 제안하고, 자동 로그인처럼 보안에 영향을 주는 설정은 사용자 승인 없이 활성화하지 않는다.

- [ ] OrbStack 또는 container runtime 재시작 뒤 전체 Compose가 의도한 방식으로 복구되는지 확인한다.
- [ ] Mac 재부팅 뒤 OrbStack, Compose, cloudflared가 각각 어떤 조건에서 다시 시작되는지 실제 설정과 동작으로 확인한다.
- [ ] 재시작·재부팅 뒤 PostgreSQL named volume과 기존 검증 데이터가 유지되는지 확인한다.
- [ ] nginx의 `127.0.0.1:8099` 접근이 복구되는지 확인한다.
- [ ] cloudflared가 의도한 방식으로 Tunnel에 다시 연결되는지 확인한다.
- [ ] 공개 HTTPS와 WSS가 정상 복구되는지 확인한다.

### Server Lifecycle Verification — 운영 복구 검증

- runtime 재시작과 Mac 재부팅 뒤 서비스 복구 방식이 확인되어 있다.
- PostgreSQL volume, nginx localhost 진입점, cloudflared 연결이 유지 또는 재현된다.
- 공개 HTTPS·WSS가 복구된다.
- 필요한 수동 절차가 있다면 Steps에 정확히 기록되어 있으며, 서버 운영에 필수인 자동화 공백은 별도 승인 없이 우회하지 않는다.
- 이 검증을 통과한 뒤에만 migration 완료를 판단한다.

## 11. Verification Matrix

| 검증 | 목적 | 실행 시점 | 성공 조건 | 실패 시 의미 | 중복 여부 |
| --- | --- | --- | --- | --- | --- |
| `docker compose config --quiet` | 환경값 참조와 Compose 문법 | Phase 0·Phase 1 변경 후 | 출력 없이 exit 0 | config·환경 | 최초 준비와 설정 변경 후만 실행 |
| Backend image build·import·Alembic heads | 확정된 COPY·import blocker 제거 | Phase 1 | build, import, head 해석 성공 | 코드·Docker packaging | AI·E2E와 다른 계층 |
| ARM 직접 inference | native import와 실제 모델 CPU 연산 | Phase 2 | aarch64, decode, YOLO, XGBoost 성공 | ARM·dependency·모델 | health로 대체하지 않음 |
| 기존 AI pytest | adapter·validator·callback payload 회귀 | Phase 2 | 기존 suite 전체 통과 | 코드 계약 | 실제 inference와 목적 다름 |
| `smoke_analysis` | image source부터 callback payload 조합 | Phase 2 | exit 0, 결과 payload 생성 | 코드·data·모델 orchestration | 직접 inference 후 한 번만 실행 |
| VM↔Mac 계약 비교 | 비교 가능한 조건에서 architecture 변화가 서비스 계약을 깨지 않는지 확인 | Gate A 전, 조건 충족 시 | key·enum·범위·완료 의미 유지 또는 비교 불가 이유 기록 | ARM·dependency·모델·비교 조건 | bit-level 비교 아님, 비교 불가 자체는 Gate 실패 아님 |
| 새 DB migration·schema | 빈 DB 재현성 | Phase 3 | migrate 0, revision·table 확인 | DB·migration·환경 | E2E에서 schema 재검사 안 함 |
| Compose health·restart | dependency와 재기동 재현성 | Phase 3 | 필수 서비스 healthy, restart 후 회복 | config·runtime | localhost에서는 health 반복 안 함 |
| Localhost REST·image | nginx routing과 정적 제공 | Phase 4 | 127.0.0.1:8099 응답 | nginx·Backend·Frontend | Cloudflare에서는 공개 route만 재검증 |
| Localhost 분석 E2E | callback·DB·WS·화면 전체 흐름 | Phase 4 | 동일 job 완료·저장·실시간 반영 | 서비스 연결·data | 단일 요청으로 여러 연결 확인 |
| Cloudflare 공개 E2E | Tunnel·HTTPS·WSS·domain 설정 | Phase 5 | 공개 사용자 흐름 성공 | Tunnel·DNS·domain | 앱 내부 기능 재시험이 아니라 공개 경계 검증 |
| Server lifecycle | Mac 서버의 재시작·재부팅 후 복구 가능성 | Gate D 후 | DB volume·localhost·Tunnel·HTTPS/WSS 복구 | host·runtime·Compose·cloudflared 설정 | Gate B의 container restart보다 넓은 host lifecycle 검증 |

새 테스트를 추가하기 전 다음 질문에 모두 답한다.

1. 기존 pytest, smoke, health, E2E가 이 실패를 잡지 못하는가?
2. 실제 재발 가능성이 있는가?
3. production 구조나 공개 계약을 테스트 때문에 바꿔야 하는가?
4. 내부 COPY 문구가 아니라 사용자 관찰 동작을 검증하는가?

하나라도 부정적이면 새 테스트를 추가하지 않는다.

## 12. Phase Gates

```text
Phase 0 준비 완료
  → Phase 1 확정 blocker 수정
  → Gate A: AI Linux/arm64 실제 inference
  → Phase 3 전체 Compose + 새 DB
  → Gate B: migration·health·restart
  → Phase 4 localhost E2E
  → Gate C: REST·image·callback·DB·WS·UI
  → Phase 5 Cloudflare 전환
  → Gate D: 공개 HTTPS/WSS E2E
  → Server Lifecycle Verification: runtime·Mac 재시작 후 복구
  → 기존 VM 종료 여부 별도 검토
```

| Gate | 다음 단계 진입 조건 | 실패 시 중단 위치 |
| --- | --- | --- |
| Gate A | ARM64 실제 모델·계약 검증 성공 | 전체 Compose 기동 전 |
| Gate B | 새 DB migration·전체 서비스·restart 성공 | localhost E2E 전 |
| Gate C | localhost 전체 사용자 흐름 성공 | Cloudflare 변경 전 |
| Gate D | 공개 HTTPS/WSS 전체 흐름 성공 | Server Lifecycle Verification 전 |
| Server Lifecycle Verification | runtime·Mac 재시작 후 DB·localhost·Tunnel·공개 접근 복구 | migration 완료 판단과 기존 VM 종료 검토 전 |

실패한 Gate를 무시하고 다음 단계로 진행하지 않는다. 실패 원인이 Plan 범위 밖 dependency 변경, emulation, model 변환을 요구하면 해당 변경을 먼저 보고하고 별도 승인을 받는다.

## 13. Rollback / Safety

### 코드·Mac 실행

- 구현은 전용 branch에서 수행하며 기존 VM checkout을 변경하지 않는다.
- Mac Compose가 실패하면 컨테이너를 중지하되 PostgreSQL volume과 image를 삭제하지 않는다.
- `docker compose down -v`, `docker system prune`, image 강제 삭제를 사용하지 않는다.
- 실패한 코드 변경은 원인을 확인한 뒤 새 commit으로 수정하며 사용자 변경을 reset·restore하지 않는다.

### 데이터

- Mac은 새 PostgreSQL volume을 사용하므로 기존 VM DB를 변경하지 않는다.
- migration은 Mac DB에만 적용한다.
- seed도 Mac DB에만 적용한다.
- 기존 DB 복사·양방향 동기화·schema 변경을 하지 않는다.

### Cloudflare

- Gate C 전 기존 route를 바꾸지 않는다.
- 전환 전에 기존 VM origin과 복귀 절차를 기록한다.
- Gate D 실패 시 hostname route를 기존 VM Tunnel/origin으로 되돌린다.
- Server Lifecycle Verification 실패 시 기존 VM을 유지하고, 필요한 수동 복구 절차 또는 최소 설정 변경안을 먼저 보고한다.
- 자동 rollback 시스템은 만들지 않는다. 수동 route 복귀만 준비한다.
- 복귀 후 Mac 로그와 실패 증거를 보존하고, 원인 확인 전 VM을 종료하지 않는다.

## 14. Time / Space Cost

### 시간 비용

| 작업 | 계획 | 측정 항목 |
| --- | --- | --- |
| AI build | Phase 2에서 runtime image 한 번 build | cold/warm 여부, wall time, dependency layer cache |
| AI 검증 | 같은 image를 재사용하고 `--build`를 지정하지 않음 | model load, YOLO inference, smoke total time |
| Backend build | Phase 1에서 build, Phase 3에서 cache 재사용 | COPY 변경에 따른 invalidated layer |
| Frontend build | Phase 3에서 한 번 production build | wall time, native package 오류 |
| Compose startup | build와 분리해 `up --detach` | DB healthy, migration, 전체 healthy 도달 시간 |
| Cloudflare 검증 | Gate C 후 단일 공개 E2E | Tunnel 연결·DNS 반영 시간 |

정확한 시간은 추정하지 않고 `/usr/bin/time -p`와 timestamp로 실측한다. 소스나 requirements가 바뀌지 않았는데 동일 대형 AI image를 다시 build하지 않는다.

### 공간 비용

| 대상 | 처리 원칙 |
| --- | --- |
| AI runtime image | build 성공과 가용 공간을 우선 확인하고, 가능하면 build 전후 `docker system df -v`와 image size 기록 |
| Shared layer | 자료를 확보한 경우 service/test image를 단순 합산하지 않고 shared·unique를 구분 |
| Build cache | 이번 이전에서 자동 GC 정책을 만들지 않고 실제 증가량만 기록 |
| AI test image | 별도 test target image를 만들지 않고 현재 runtime image에서 기존 pytest 실행 |
| YOLO weight | image에 COPY하지 않고 기존 read-only bind mount 유지 |
| XGBoost weight | 현재 작은 Git artifact를 image에 유지 |
| PostgreSQL | Mac 전용 named volume 사용, 완료 전 삭제 금지 |
| Frontend artifact | standalone runner image만 유지하는 현재 구조 사용 |
| Sample image | AI image 추가 layer 크기를 측정하되 migration blocker와 최적화를 섞지 않음 |

가용 공간이 실제 build·volume 예상 증가를 감당하지 못할 때만 공간을 blocker로 승격한다. 이 경우 image 삭제로 즉시 대응하지 않고 측정 결과와 안전한 정리 대상을 먼저 보고한다.

## 15. Maintainability / Extensibility Review

### 유지보수성 판단

- Dockerfile의 filesystem layout이 Python import와 코드의 project root 계산에 맞아져 기존 구조가 더 명확해진다.
- sample은 Git 추적 source와 image runtime 경로가 직접 연결되어 수동 host mount 의존성이 줄어든다.
- API·DB·callback·WebSocket을 바꾸지 않아 기존 amd64와 향후 자동화가 같은 Dockerfile을 사용할 수 있다.
- Compose의 기존 환경변수·service dependency를 유지하므로 이후 GHCR·GitHub Actions가 현재 build 정의를 재사용할 수 있다.
- ARM 전용 분기를 만들지 않아 향후 multi-arch 도입을 막지 않는다.

### Plan self-review

| 번호 | 질문 | 검토 결과 |
| --- | --- | --- |
| 1 | Mac 이전과 image 최적화가 섞이지 않았는가? | 분리됨. 크기는 측정만 하고 최적화는 후속이다. |
| 2 | Python/Node upgrade가 끼어들지 않았는가? | 기존 버전을 유지한다. |
| 3 | ARM 때문에 서비스 로직을 바꾸는가? | 바꾸지 않는다. Docker packaging과 import만 수정한다. |
| 4 | 모델 동작 계약이 변경되는가? | 모델·feature·callback 계약을 유지한다. |
| 5 | 새 Dockerfile/Compose를 만드는가? | 만들지 않는다. 기존 파일만 수정한다. |
| 6 | 기존 오류를 두고 우회 코드만 추가하는가? | 잘못된 COPY를 제거·교체하고 누락 import를 직접 고친다. |
| 7 | 삭제해야 할 기존 코드가 남는가? | 잘못된 Backend COPY 세 줄을 교체 대상으로 명시했다. |
| 8 | 작은 patch 때문에 서비스 재현을 놓치는가? | 실제 inference, 새 DB, E2E, restart까지 완료 조건에 포함했다. |
| 9 | 같은 계약을 여러 테스트에서 반복하는가? | 검증 계층별 소유 실패를 분리했다. |
| 10 | TDD로 내부 구현을 고정하는가? | 새 unit test를 기본 계획에 넣지 않았다. |
| 11 | test-only production code가 생기는가? | 생기지 않는다. 기존 runtime·script를 사용한다. |
| 12 | 테스트를 위해 서비스 설계를 바꾸는가? | 바꾸지 않는다. 테스트가 기존 구조를 따른다. |
| 13 | AI rebuild가 반복되는가? | Phase 2 한 번 build 후 이후 명령에는 `--build`를 지정하지 않는다. |
| 14 | image/cache/model 공간을 고려했는가? | 가용 공간과 weight는 우선 확인하고 shared·unique·cache는 가능한 범위에서 기록한다. |
| 15 | 실행·model load 비용을 고려했는가? | build, startup, load, inference를 분리 실측한다. |
| 16 | 수정 후 구조가 명확해지는가? | Docker path와 code path가 일치한다. |
| 17 | 향후 Actions/GHCR을 방해하는가? | 공용 Dockerfile·Compose를 정상화해 재사용 가능하다. |
| 18 | 미래 요구를 미리 구현하는가? | 자동화·최적화·multi-arch는 명시적으로 보류했다. |
| 19 | 추가 대규모 Analysis가 필요한가? | 필요 없다. 실행 중 기존 사실이 뒤집힐 때만 최소 정정한다. |
| 20 | 이번 Plan으로 구현을 시작할 수 있는가? | 가능하다. Phase 0의 운영 자료와 환경 이전부터 순차 진행한다. |
| 21 | ARM blocker가 새로 확정되었는가? | 아니다. 실제 Linux/arm64 inference 검증이 남아 있다. |
| 22 | migration과 optimization이 분리되어 있는가? | 분리되어 있다. layer 상세 진단도 non-blocking이다. |
| 23 | 불필요한 테스트가 늘었는가? | 아니다. 기존 pytest·smoke와 계층별 통합 검증을 재사용한다. |
| 24 | 기존 코드 대신 우회 코드가 추가되는가? | 아니다. 확인된 잘못된 COPY·import를 기존 파일에서 직접 수정한다. |
| 25 | Mac mini 서버 lifecycle이 완료 조건에 포함되었는가? | Gate D 뒤 별도 운영 복구 검증과 완료 조건에 포함했다. |
| 26 | Steps만으로 context recovery가 가능한가? | source of truth, 상태, 다음 작업, 실행 이력, Gate, 변경, 측정, 이슈, 복구 절차를 유지한다. |

Self-review에서 범위 혼합, 테스트 중복, additive workaround는 발견되지 않았다. 구현 중 이 전제가 깨지면 임의 확장하지 않고 Plan을 먼저 수정한다.

## 16. Explicitly Deferred Work

다음은 `Post-Migration / Follow-up`으로 분리한다.

- AI image 약 10GB 원인 layer 실측 후 최적화.
- CPU-only PyTorch·XGBoost dependency 검토.
- Python requirements 전체 pinning과 lock 전략.
- Python·Node runtime 업그레이드.
- dependency build/runtime multi-stage 최적화.
- AI test image 보존·정리 정책.
- Docker build cache GC 정책.
- GHCR image registry.
- GitHub Actions build·test·deploy.
- multi-arch build와 manifest.
- 자동 rollback.
- Jenkins 제거와 관련 파일 정리.
- 모델 runtime download·registry.
- YOLO/XGBoost model format 변경.
- ONNX, TensorRT, quantization.

후속 작업은 migration 실측값을 입력으로 삼는다. 이번 구현 branch에 함께 넣지 않는다.

## 17. Implementation Order

아래 순서를 유지한다. 각 Task는 이전 Gate의 결과를 입력으로 사용하므로 병렬 실행하지 않는다.

1. **State checkpoint:** 구현 전에 `docs/steps/step-03-mac-mini-orbstack-migration.md`를 초기화하고 이후 checkpoint마다 갱신한다.
2. **Preparation checkpoint:** 기존 VM commit·주요 AI dependency, 모델 hash, 기존 운영 `.env`의 안전한 Mac 이전, 가용 공간을 준비한다. 상세 image layer 진단은 가능한 경우에만 기록한다.
3. **Backend packaging checkpoint:** `backend/Dockerfile` 경로와 `main.py` import를 수정하고 image import·Alembic을 검증한다.
4. **AI packaging checkpoint:** `ai_service/Dockerfile` sample COPY를 수정하고 ARM runtime image를 한 번 build한다.
5. **Gate A checkpoint:** 직접 inference, 기존 pytest와 smoke를 통과한다. VM 비교 조건이 있으면 계약을 비교하고, 없으면 이유를 Steps에 기록한다.
6. **Compose checkpoint:** Backend cache와 Frontend를 build하고 새 DB로 전체 Compose를 기동한다.
7. **Gate B checkpoint:** migration, schema, seed, health, restart를 통과한다.
8. **Gate C checkpoint:** localhost에서 실제 분석 한 건의 callback·DB·WebSocket·UI를 통과한다.
9. **Cloudflare approval checkpoint:** 대상 hostname과 VM 복귀 경로를 사용자에게 제시한다.
10. **Gate D checkpoint:** 승인 후 Tunnel route를 전환하고 공개 E2E를 통과한다.
11. **Server lifecycle checkpoint:** 현재 OrbStack·Compose·cloudflared 설정을 확인하고 runtime 재시작과 Mac 재부팅 뒤 복구를 검증한다.
12. **Observation checkpoint:** 기존 VM을 유지한 채 관찰하고, 종료·삭제는 별도 작업으로 결정한다.

권장 commit 경계는 blocker 수정, 실행 검증 기록, Cloudflare 결과 문서화를 서로 분리하는 것이다. 실제 `git add`·`git commit`은 사용자가 해당 구현 단계에서 명시적으로 요청한 경우에만 수행한다.

## 18. Completion Criteria

다음 항목을 모두 충족해야 Mac 이전을 완료로 판단한다.

- [ ] 기존 서비스 계약·모델·runtime version을 유지했다.
- [ ] 확인된 Docker COPY·import·sample blocker를 기존 파일에서 수정했다.
- [ ] Linux/arm64에서 실제 YOLO·XGBoost CPU inference가 성공했다.
- [ ] 새 PostgreSQL volume에 migration head와 schema가 생성되었다.
- [ ] seed 또는 동등한 신규 데이터로 Backend DB 흐름이 동작한다.
- [ ] 전체 Compose가 기동·restart 후 재현된다.
- [ ] `127.0.0.1:8099`에서 Frontend·REST·image·WebSocket·분석·callback·저장·화면 반영이 성공했다.
- [ ] localhost Gate 뒤 Cloudflare HTTPS·WSS 전체 흐름이 성공했다.
- [ ] runtime 재시작과 Mac 재부팅 뒤 PostgreSQL volume, nginx `127.0.0.1:8099`, cloudflared, 공개 HTTPS·WSS의 복구 방식이 검증되었다.
- [ ] 실패 시 기존 VM route로 복귀할 수 있다.
- [ ] 기존 VM·DB·image·volume은 별도 종료 승인 전까지 유지된다.
- [ ] 실제 build 시간, image/cache, startup, model load·inference 비용이 Steps 문서에 기록되었다.
- [ ] deferred optimization이 migration 변경에 섞이지 않았다.

### 최종 판단

```text
Analysis 추가 필요 여부: 없음. 실제 실행 결과가 기존 사실을 뒤집을 때만 최소 정정한다.
Plan 실행 가능 여부: 사용자 승인 후 Phase 0부터 순차 실행 가능.
확정 ARM blocker: 현재 없음.
남은 ARM 실검증: Linux/arm64 native import, OpenCV decode, best.pt load·YOLO CPU inference, XGBoost inference, 기존 test·smoke와 현재 callback/status/result 계약. 비교 조건이 확보되면 VM 결과 계약도 비교한다.
Mac 이전 필수 수정: Backend Docker COPY·실행 경로, realtime_simulator import, Backend·AI sample 공급, Mac 모델·DB·nginx·Frontend 환경값.
후속으로 미룬 최적화: AI image·CPU-only dependency·pinning·runtime upgrade·cache GC·CI/CD·multi-arch·자동 rollback·Jenkins 제거·모델 format 변경.
```

**추가 대규모 Analysis 없이 이 Plan에 따라 구현 및 실행 검증으로 진행한다.**

**Plan ready for implementation**
