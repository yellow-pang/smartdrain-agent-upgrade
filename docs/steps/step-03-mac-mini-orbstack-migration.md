# SmartDrain Mac mini + OrbStack Migration Steps

이 문서는 migration 구현 중 지속적으로 갱신하는 실행 상태 및 인수인계 기록이다. 판단 근거는 Analysis, 실행 순서와 Gate는 Plan을 참조하며 이 문서에 복제하지 않는다.

## 0. Source of Truth

- Analysis: [`docs/verification/18_mac-mini-orbstack-migration-analysis.md`](../verification/18_mac-mini-orbstack-migration-analysis.md)
- Plan: [`docs/plans/plan-03-mac-mini-orbstack-migration.md`](../plans/plan-03-mac-mini-orbstack-migration.md)
- 작업 branch: `chore/macos-orbstack-migration`
- 구현 시작 기준 HEAD: `5ce2b52067ad9f69587b3c4730b55d1bbec5e409`
- 현재 HEAD: `4e69a3118b0607674ce3391df330deafc7a9b74d`
- 마지막 갱신 시각: `2026-09-20 15:47:04 KST`

## 1. Current State

- 현재 Phase: Phase 4 완료 후 공동 운영 인계
- 현재 Task: SmartDrain localhost 변경·검증 기록 commit 준비
- 현재 Gate: Gate C — `PASSED`
- 현재 상태: `READY_TO_COMMIT`
- localhost Gate는 통과했다. 공개 hostname은 아직 기존 환경의 데이터를 반환하며, Cloudflare 변경은 Health Center 공통 운영 세션이 전담한다.

## 2. Next Action

**Nginx 수정, 실행 상태 문서와 별도 구현 기록을 검토한 뒤 하나의 SmartDrain localhost checkpoint로 commit한다. 이 세션에서는 Tunnel·DNS·재부팅을 변경하지 않는다.**

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

### Phase 2 — AI Linux/arm64 Verification

- 수행 내용: AI runtime image를 Linux/arm64로 한 번 빌드하고 모델 없이 가능한 native import, OpenCV decode, XGBoost load·inference, 기존 pytest를 실행했다.
- 실제 변경 파일: 없음. Phase 1에서 수정한 `ai_service/Dockerfile` image를 사용했다.
- 실행 명령: `DOCKER_DEFAULT_PLATFORM=linux/arm64 docker compose build ai-service`, 동일 image의 진단 Python, `python -m pytest ai_service`.
- 결과: image architecture `arm64`, OpenCV decode, XGBoost inference, 기존 pytest `115 passed`, 실제 `best.pt` load·YOLO CPU inference, `smoke_analysis`가 성공했다. `torch 2.14.0+cu130`은 CPU에서 동작했고 `torch.cuda.is_available()`은 false였다.
- 성공 여부: 성공. 기존 VM의 실행 결과와 commit이 없어 VM↔Mac 직접 비교는 수행하지 못했으며 이 비교 불가 이유를 기록했다.

### Phase 3 — Full Compose Bring-up

- 수행 내용: Backend cache를 재사용해 Frontend production image를 build하고, 새 PostgreSQL volume에서 전체 Compose, migration, schema, 빈 DB API, seed와 전체 restart를 검증했다.
- 실제 변경 파일: 없음.
- 실행 명령: `docker compose build backend frontend`, `docker compose up --detach`, DB revision·table query, Backend API, seed profile, `docker compose restart`, localhost API와 서비스 경계 진단.
- 결과: Frontend build, 전체 기동, migration head `20260623_0003`, 핵심 5개 table, 빈 DB API, seed 5건, 전체 service health와 DB volume 유지는 성공했다. 최초 전체 restart 뒤 nginx가 이전 Backend IP를 유지해 502를 반환했다. Docker resolver와 동적 upstream을 적용한 뒤 동일 전체 restart에서 별도 nginx 재시작 없이 Frontend·API가 복구됐다.
- 성공 여부: 성공. Gate B 통과.

### Phase 4 — Localhost Integration Verification

- 수행 내용: nginx 공개 포트에서 Frontend·REST·sample image를 확인하고, WebSocket 연결 상태에서 실제 분석 요청을 보내 AI callback, DB 저장과 화면 반영을 검증했다.
- 실제 변경 파일: 없음.
- 실행 명령: localhost `curl`, Node 내장 WebSocket+`fetch`, DB job query, 분석 history 조회, Backend·AI log 확인, Safari 화면 확인.
- 결과: Frontend와 REST가 200, sample image가 `image/jpeg` 649,529 bytes로 응답했다. `DR-002` 요청은 `processing`으로 수락됐고 `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED`, `DRAIN_STATUS_UPDATED`가 모두 도착했다. job `REQ_20260920061959014272_2`는 `completed`이고 `yolo_result_id=6`, error 없음으로 저장됐다. 최신 history의 YOLO·XGBoost 결과 연결과 Safari의 최신 시각·막힘 정도 22%·양호 상태·`실시간 연결됨` 표시를 확인했다.
- 성공 여부: 성공. Gate C 통과.

### Phase 5 — Cloudflare Migration (준비 완료)

- 수행 내용: Mac의 `cloudflared` 설치·프로세스·LaunchDaemon과 Cloudflare Tunnel 상태를 비밀값 없이 읽고, 공개 hostname이 현재 어느 환경을 반환하는지 확인했다.
- 실제 변경 파일: 없음. Cloudflare 설정도 변경하지 않았다.
- 실행 명령: `cloudflared --version`, Homebrew service·LaunchDaemon 메타데이터·프로세스 확인, Cloudflare dashboard 읽기, 공개 HTTPS REST·image 요청.
- 결과: `cloudflared 2026.9.1`과 system LaunchDaemon이 설치되어 실행 중이다. `RunAtLoad=true`, 실패 종료 시 재시작이며 token file 방식이다. Dashboard의 `mac-mini-prod` Tunnel은 Healthy였다. 그러나 `https://smartdrain.healthq.store/api/dashboard/summary`의 최신 데이터 시각은 `2026-06-30`으로 Mac localhost의 `2026-09-20`과 달라, 공개 hostname은 아직 Mac의 현재 DB를 바라보지 않는 것으로 확인됐다. 공개 sample image는 200이었다.
- 성공 여부: 준비 성공. Cloudflare route 변경은 Health Center 공통 운영 세션에 인계한다.

## 4. Gate Results

### Gate A

- 상태: `PASSED`
- 근거: Linux/arm64 image build, native dependency import, OpenCV decode, 동일 `best.pt` load, YOLO CPU inference, XGBoost load·inference, 기존 pytest 115개, `smoke_analysis`가 성공했다. callback key와 processing/good/unknown/field_check 결과 계약이 유지됐다.
- 남은 위험: 기존 VM의 비교 가능한 code revision과 실행 결과가 없어 VM↔Mac 직접 비교는 수행하지 못했다. 실제 status·classification 차이는 확인되지 않았다.

### Gate B

- 상태: `PASSED`
- 근거: 새 DB migration, schema, seed, 장기 서비스 health와 DB data 유지가 성공했다. Nginx 동적 upstream 수정 후 전체 restart에서도 migrate exit 0, 다섯 장기 서비스 healthy, Frontend·API 200과 seed 5건 유지가 확인됐다.
- 남은 위험: Mac host·OrbStack 자체 재시작과 공개 Tunnel 복구는 후속 Server Lifecycle Verification에서 확인한다.

### Gate C

- 상태: `PASSED`
- 근거: `127.0.0.1:8099`에서 Frontend, REST, image, WebSocket, 실제 YOLO/XGBoost inference와 callback, job 완료·결과 저장, Frontend 최신 결과 반영이 하나의 흐름으로 성공했다.
- 남은 위험: Cloudflare HTTPS/WSS 경계와 domain-dependent 설정은 Gate D에서 확인한다.

### Gate D

- 상태: `NOT_STARTED`
- 근거: Cloudflare 설정 미변경, 공개 E2E 미실행.
- 남은 위험: HTTPS, WSS, domain-dependent 설정과 기존 공개 route 복귀 경로를 검증해야 한다. 현재 공개 API가 Mac과 다른 데이터를 반환하므로 전환은 아직 완료되지 않았다.

### Server Lifecycle Verification

- 상태: `NOT_STARTED`
- 근거: OrbStack/runtime 재시작과 Mac 재부팅 검증 미실행.
- 남은 위험: PostgreSQL volume, nginx `127.0.0.1:8099`, cloudflared, 공개 HTTPS/WSS의 실제 복구 방식을 확인해야 한다.

## 5. Actual Changes

| 파일 | 수정/삭제/추가 | 실제 변경 이유 | Plan과 차이 |
| --- | --- | --- | --- |
| `docs/plans/plan-03-mac-mini-orbstack-migration.md` | 수정 | 승인 전 최종 보정 사항 반영 | 없음 |
| `docs/steps/step-03-mac-mini-orbstack-migration.md` | 추가 | 구현 상태, 다음 작업, Gate와 실행 이력을 세션 간 인계 | Plan 실행 전에 초기화하도록 시점 명확화 |
| `docs/steps/step-03-mac-mini-orbstack-migration-implementation-record.md` | 추가 | 이전 배경, 선택 이유, 문제 해결과 검증 결과를 장기 기록 | 실행 상태 문서와 역할을 분리해 추가 |
| `docs/steps/README.md` | 수정 | 실행 상태 문서와 별도 구현 기록의 역할 안내 | 없음 |
| `.env` | 수정 | Mac 전용 Compose namespace와 nginx `127.0.0.1:8099` 적용 | 없음, Git 추적 제외 |
| `backend/Dockerfile` | 수정 | 앱·Alembic·sample을 runtime 기대 경로에 배치 | 없음 |
| `backend/app/main.py` | 수정 | 등록된 `realtime_simulator.router` 모듈 import 복구 | 없음 |
| `ai_service/Dockerfile` | 수정 | 운영 image에 기존 sample image 공급 | 없음 |
| `ai_service/model/best.pt` | 추가 | Windows 노트북의 운영 YOLO 모델로 ARM inference 검증 | Git 추적 제외, 사용자가 직접 복사 |
| `nginx/default.conf` | 수정 | container IP 변경 뒤 Backend·Frontend upstream을 Docker DNS로 재해석 | Plan 밖 변경, 재기동 502 원인 확인 후 사용자 승인으로 추가 |

## 6. Commands Already Executed

| 분류 | 명령/작업 | 결과 |
| --- | --- | --- |
| 상태 확인 | `git status --short --branch`, branch, HEAD 확인 | branch와 기준 HEAD 확인 |
| 문서 검증 | 필수 section·핵심 문구 검색, source 문서 존재 확인, whitespace 검사 | 통과 |
| Backend build | `/usr/bin/time -p docker compose build backend` | 성공, 31.53초 |
| Backend packaging | container import·path assertion, `alembic heads` | 성공, head `20260623_0003` |
| AI build | Linux/arm64 `docker compose build ai-service` | 성공, 506.78초. 같은 source로 재실행 금지 |
| AI 부분 검증 | native import, OpenCV decode, XGBoost load·inference, 기존 pytest | 성공, `115 passed` |
| YOLO CPU inference | 동일 image에 `best.pt` read-only mount 후 load·predict | 성공 |
| AI smoke | `python -m ai_service.scripts.smoke_analysis --drain-id 2` | 성공, callback payload 생성 |
| Frontend build | `docker compose build backend frontend` | 성공, Backend 전 layer cache hit |
| 전체 Compose | `docker compose up --detach` | 성공, 32.85초 |
| DB migration | 신규 DB `alembic upgrade head` | 성공, `20260623_0003` |
| DB seed | seed profile 1회 | 성공, 5건 생성, 1.98초 |
| Compose restart 최초 | 전체 서비스 restart와 localhost API | service health·DB 유지 성공, nginx stale upstream IP로 API 502 |
| Nginx 경계 진단 | Backend 직접, nginx→Backend/Frontend 직접 요청, nginx 단독 restart | 앱 경로는 200, nginx 단독 restart 후 proxy 200로 원인 확정 |
| Nginx 수정 회귀 | `nginx -t`, 전체 Compose restart, Frontend·API 재확인 | 성공, 별도 nginx restart 없이 복구 |
| localhost 기본 경계 | Frontend, dashboard REST, 분석 history, sample image | 성공, HTTP 200 및 JPEG 제공 |
| localhost E2E | WebSocket 연결 후 `DR-002` 실제 분석 요청, DB·history·log 확인 | 성공, 3종 이벤트와 callback 2종, job 완료·결과 연결 확인 |
| Frontend 확인 | Safari에서 대시보드 접근과 최신 결과·실시간 상태 확인 | 성공, 최신 DR-002 결과와 `실시간 연결됨` 표시 |
| Cloudflare 사전 확인 | 설치·LaunchDaemon·Tunnel health와 공개 HTTPS 응답 확인 | Mac Tunnel Healthy, 공개 hostname은 기존 환경 데이터 반환 |
| Cloudflare 변경 | 미실행 | 공통 운영 세션이 임시 `mac-smartdrain.healthq.store → http://localhost:8099`부터 검증 |

## 7. Measurements

- AI build 시간: 506.78초
- Backend build 시간: 31.53초
- Frontend 포함 build 시간: 40.68초
- image/cache 증가량: 최초 images 7.911GB·build cache 6.384GB, Backend build 후 8.94GB·7.073GB, AI build 후 25.94GB·17.39GB
- AI image logical size: 3,666,967,615 bytes
- Backend image logical size: 173,240,414 bytes
- 모델 artifact: 52,067,329 bytes, SHA256 `d43cef94671907771f30b3316f2728e82af352db2cf4094644e92f6ffbaf16e2`
- 모델 load 시간: YOLO 0.268초, XGBoost 0.006초
- inference 시간: YOLO CPU 2.334초, XGBoost 0.002초
- AI native import 시간: 4.084초
- Compose startup 시간: 32.85초
- Compose restart 명령 시간: 최초 0.56초·수정 후 0.74초, 수정 후 health와 proxy 복구 성공
- localhost 실제 분석 수락부터 최종 결과 저장까지: 약 7.4초
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
- Phase 3에서 새 Mac DB에 migration과 seed를 실행했다. seed profile의 dependency로 migrate가 한 번 더 실행됐으나 동일 head에서 종료됐고 schema 변경은 없었다.
- 전체 restart가 nginx의 stale upstream IP 문제를 드러냈다. 사용자 승인 후 `nginx/default.conf`에 Docker resolver `127.0.0.11`과 `resolve` upstream을 적용했다. API path·WebSocket path·service 책임은 변경하지 않았다.
- Phase 4 최초 localhost 요청은 도구 sandbox 안에서 `curl: (7)`로 실패했다. 같은 시점에 OrbStack은 `127.0.0.1:8099`를 listen하고 있었고 nginx 내부의 Frontend·Backend 요청은 200이었다. Docker 및 localhost 접근 권한을 허용한 실행에서는 host Frontend·dashboard API가 200을 반환했으므로, 이는 서비스 장애가 아니라 실행 도구의 localhost 네트워크 격리로 판정했다. 이후 host E2E 명령은 같은 권한 경계에서 실행한다.
- UI 자동 검증용 in-app browser는 제공되지 않아 기존 Safari에 새 탭을 열어 확인했다. 기존 Cloudflare 탭은 변경하지 않았고 로컬 SmartDrain 탭에서만 대시보드 렌더링과 WebSocket 연결 상태를 읽었다.
- Mac에는 별도 Homebrew user service가 아니라 root 소유 system LaunchDaemon으로 `cloudflared`가 구성되어 있다. 실행 인자의 실제 token file 경로와 값은 출력하지 않았다. 현재 방식이 이미 `RunAtLoad`와 실패 재시작을 제공하므로 새 daemon이나 wrapper를 추가하지 않는다.
- Cloudflare dashboard에서 `mac-mini-prod` Tunnel이 Healthy임을 읽기 전용으로 확인했다. 공개 API의 데이터 시각이 Mac localhost와 달라 route 전환이 필요하다는 근거를 확보했으며, 변경 전에 승인을 받는 Plan 경계를 유지한다.
- RWR 작업 기록의 공동 운영 기준을 반영해 Cloudflare 변경 소유권을 Health Center 공통 운영 세션으로 일원화했다. SmartDrain은 `127.0.0.1:8099` origin과 앱 검증을 담당하고 별도 Tunnel·connector·service를 만들지 않는다.
- RWR 기록은 Mac에 user service나 `~/.cloudflared` 설정이 없다고 설명했지만, SmartDrain 실측에서는 root system LaunchDaemon과 실행 중인 `cloudflared`, Healthy인 `mac-mini-prod`가 확인됐다. 새 공통 Tunnel을 생성하기 전에 이 기존 구성을 먼저 확인해야 한다.
- 큰 범위 변경이 필요하면 구현하지 않고 이 문서의 blocker와 근거를 먼저 갱신해 보고한다.
- 사용자 승인 필요 여부: 현재 SmartDrain 파일 변경에는 없음. Cloudflare route 변경과 공동 재부팅은 Health Center 공통 운영 세션에서 별도 승인·조율한다.
- Plan 수정 여부: 이번 최종 보정 반영 완료.

## 9. Open Issues / Blockers

- 기존 VM 접속 대상이나 실행 결과가 현재 workspace에 없어 운영 commit, 주요 AI dependency 버전, 모델 원본 hash와 Mac 결과를 직접 비교하지 못했다.
- 사용자가 기존 Windows 노트북에서 복사한 모델이라고 확인했으며 Mac artifact의 크기·SHA256은 기록했다. 원본 hash가 추후 제공되면 일치 여부를 추가 확인한다.
- Cloudflare route 변경은 Health Center 공통 운영 세션의 작업이다. SmartDrain 검증 origin은 `http://localhost:8099`이며 임시 `mac-smartdrain.healthq.store` 검증 후 운영 hostname을 개별 전환한다.
- system LaunchDaemon과 `mac-mini-prod`가 이미 존재하므로 공통 운영 세션에서 중복 Tunnel·connector·service를 생성하지 않도록 실제 연결 관계를 먼저 확인해야 한다.

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
