# SmartDrain GitHub Actions CI/CD 구현 계획

> 상태: **구현 전 계획 검토용**. 이 문서 작성으로 workflow, runner, GHCR, 운영 컨테이너 또는 GitHub 설정을 변경하지 않았다. Phase / Task / Gate를 실행 기준으로 사용하며 특정 실행 framework를 요구하지 않는다.

## 1. 목적과 완료 기준

Mac mini + OrbStack에서 수동으로 실행 중인 SmartDrain을 `dev → main` PR 병합 후 자동 검증·이미지 게시·배포하는 구조로 전환한다. 개발자가 운영 디렉터리에서 checkout하거나 AI 이미지를 다시 빌드하지 않아도, 병합된 commit의 세 애플리케이션 이미지가 현재 PostgreSQL 데이터와 모델을 사용해 실행되어야 한다.

```text
feature → dev PR: GitHub hosted CI
dev → main PR: GitHub hosted CI + 변경 검토
main 병합: 최종 SHA 검증 → Linux/arm64 이미지 build → GHCR digest 게시
  → 비공개 운영 저장소의 배포 workflow 호출
  → 배포 출처 확인 → Mac runner
  → 후보 이미지 실제 AI 추론 → 기존 DB migration → Compose 적용
  → http://127.0.0.1:8099 검증 → 성공 release 기록
```

자동배포 완료는 workflow가 초록색이 되는 것만으로 판단하지 않는다. 실제 실행 digest, 유지된 DB volume, AI 추론 결과, localhost API·이미지·WebSocket을 확인한다. Cloudflare Tunnel/DNS는 Health Center 공통 운영 세션이 관리하며 이 파이프라인에서 변경하지 않는다.

## 2. 기준과 현재 확인된 상태

### 2.1 조사 기준

- 조사일: 2026-09-27. 외부 설정은 구현 시작 시 변경 여부를 다시 확인한다.
- 저장소: `yellow-pang/smartdrain-agent-upgrade` — 공개 개인 Fork.
- 작업 branch: `chore/github-actions-cicd`, `dev`에서 생성.
- 기준 HEAD: `dc1c0601b69ae9e79ebde1852baf5f9a646cdb3a`.
- 조사 시 `origin/main`: `0b318e0e3e25f3940c12cab26bee911bf63cea53`.
- 시작 작업 트리: clean. 이번 계획 작성 범위는 이 문서와 Plans 목록이다.
- 이전 기록: [Mac 이전 Analysis](../verification/18_mac-mini-orbstack-migration-analysis.md), [Plan 03](plan-03-mac-mini-orbstack-migration.md), [실행 상태](../steps/step-03-mac-mini-orbstack-migration.md), [구현 기록](../steps/step-03-mac-mini-orbstack-migration-implementation-record.md).

이전 문서의 사전 분석·미완료 표시는 당시 상태다. 이번 판단에는 실제 Git, 컨테이너, GitHub 조회 결과를 우선한다. 과거 Analysis를 CI/CD 계획으로 확장하지 않는다.

### 2.2 현재 구현과 빈 부분

| 대상 | 확인된 사실 | 이번 계획에 미치는 영향 |
| --- | --- | --- |
| GitHub Actions | main/dev에 앱 workflow 없음. Dependency Graph 실행만 확인 | 앱 CI와 배포 workflow를 새로 작성해야 함 |
| GitHub 설정 | runner/environment/secret/variable/hook 없음, ruleset 없음, main/dev 미보호 | 파일 작성과 별도로 권한·보호 규칙·runner 초기 설정 필요 |
| Git 관계 | main 대비 dev만 64개, main만 1개 commit. merge-tree 검사 conflict 없음 | 첫 main 승격은 누적 변경 검토 필요. conflict 없음이 실행 성공을 뜻하지 않음 |
| 원격 선택 | origin은 개인 Fork, upstream은 원본 팀 저장소. 로컬 main은 upstream/main 추적 | 모든 PR/API는 개인 Fork를 명시. 로컬 main 추적 대상도 적용 전 확인 |
| Jenkins | Linux `/home/yp/apps/smart-drain`, project `smartdrain-dev`, dev nginx 설정에 종속 | Mac CD에서 기존 Jenkins deploy를 그대로 실행하지 않음 |
| Mac 실행 | project `smartdrain-mac`, db/backend/AI/frontend/nginx healthy, migrate 종료 0 | 새 DB를 만들지 않고 현재 Mac DB를 보존 |
| 공개 포트 | nginx `127.0.0.1:8099 → 80`, 나머지 서비스 내부 통신 | localhost origin과 네트워크 계약 유지 |
| 배포 파일 | 개발 checkout의 nginx 설정과 `ai_service/model/best.pt`를 bind | 개발 branch 전환과 runner 정리가 운영 파일을 바꾸지 않도록 경로 분리 |
| 다른 프로젝트 | Health Center, RWR 실행 중. RWR 전용 runner 존재 | 다른 runner 재등록·공용 prune·포트 변경 금지 |
| Cloudflare | Mac host daemon 존재. 조사 시 공개/임시 도메인 비인증 요청 403 | 공통 운영 세션에서 Access/route 상태 확인. 403만으로 앱 장애·공개 검증 완료 판정 금지 |

### 2.3 코드 근거

- `Jenkinsfile`, `.jenkins/scripts/{preflight,validate,deploy,smoke-test,seed}.sh`: socket·Linux 경로, 서버 build, AI test image, 선택적 seed, 제한된 HTTP smoke.
- `docker-compose.yml`: backend/migrate/seed 동일 이미지, AI/frontend build만 지정, migration 의존성, PostgreSQL named volume, nginx 설정·YOLO 모델 bind.
- `frontend/Dockerfile`, `frontend/package.json`, `frontend/next.config.mjs`: Node 22, pnpm frozen install, lint, Next production build, build-time 공개 환경값.
- `backend/Dockerfile`, `backend/requirements.txt`, `backend/alembic/`, `backend/app/routers/dashboard.py`: Python 3.12, Alembic, 실제 DB를 조회하는 summary API.
- `ai_service/Dockerfile`, `ai_service/requirements.txt`, 기존 pytest와 `ai_service/scripts/smoke_analysis.py`: 실제 모델과 mock 테스트의 구분.
- `ai_service/yolo/analyzer.py`, `ai_service/yolo/contract.py`, `ai_service/xgboost/model_predictor.py`: 추론 실패 sentinel과 정상적인 unknown 분류의 차이.

## 3. 범위와 제외 사항

**이번 구현의 범위**는 PR CI, main 이미지 게시, GHCR digest 배포, 기존 Compose 이미지 선택 확장, Mac 배포 경로·runner 준비, 배포 검증과 수동 복귀 절차다. 앱 API·WebSocket·callback·모델 알고리즘·DB schema는 변경하지 않는다.

다음은 별도 후속 작업이다.

- AI 이미지 용량 최적화, CPU-only PyTorch 재구성, requirements 전체 pinning.
- Python/Node/PostgreSQL upgrade, multi-arch, ONNX·TensorRT·모델 format 변경.
- 새 배포 framework, Mac 전용 Dockerfile/Compose, 자동 rollback 시스템.
- Jenkins/기존 VM 제거, image/volume 삭제, 공용 Docker cache GC.
- Cloudflare route/DNS/Access 변경, 다른 프로젝트 CI/CD 변경, Mac 자동 로그인 설정.

pnpm 실행 버전을 현재 정상 빌드 버전으로 명시하는 것은 빌드 재현성 범위다. 새 버전을 추측해 업그레이드하지 않으며 lockfile을 이유 없이 다시 생성하지 않는다.

## 4. 대안과 추천 구조

| 대안 | 이점 | 현재 환경에서의 비용·위험 | 판단 |
| --- | --- | --- | --- |
| Mac에서 Jenkins 재구축 | 기존 stage 일부 재사용 | VM 절대경로·socket·서버 build 구조 수정, 별도 Jenkins 운영 | 채택하지 않음 |
| 공개 repo에 Mac self-hosted runner 직접 연결 | 배포 경로가 짧음 | 공개 PR workflow가 운영 host를 공격할 수 있음. labels/environment만으로 격리 불가 | 채택하지 않음 |
| GitHub build + SSH 배포 | runner 없이 전달 가능 | 현재 SSH 전송 경로 미확인, 새 외부 접근·키·네트워크 운영 필요 | 이번 기본안에서 제외 |
| GitHub build + 비공개 운영 repo Mac runner | 외부 PR 실행과 운영 host 접근을 분리, Mac에서 rebuild 불필요 | 운영 repo 및 제한된 전달 권한 관리 필요 | **추천** |

비공개 운영 repo는 기능 확장을 위한 계층이 아니라 공개 repo의 임의 PR 코드와 운영 Docker 접근을 분리하기 위한 최소 경계다. 기존에 동일 책임의 비공개 운영 repo가 있다면 먼저 검토해 재사용하고, 없다면 `yellow-pang/mac-mini-deploy`를 제안한다. 아직 생성하지 않았다.

공식 문서도 공개 repo의 self-hosted runner 사용을 강하게 경계한다. 비공개 repo도 구성원·workflow를 제한해야 하며, 같은 Mac 사용자와 Docker daemon을 쓰는 한 다른 프로젝트까지 완전히 격리되는 것은 아니다. [GitHub runner 보안](https://docs.github.com/en/actions/reference/security/secure-use)

## 5. Trigger, 전달 계약과 권한

### 5.1 공개 SmartDrain 저장소

- `ci.yml`: `pull_request` 대상 dev/main 및 `workflow_call`. PR 코드 실행은 hosted runner에서만 수행한다. `pull_request_target`로 PR 코드를 실행하지 않는다.
- `release.yml`: `push` main에서 동일 CI 정의를 호출하고 성공하면 세 이미지를 Linux/arm64로 build/push한다. 구현 검증용 수동 실행은 **build-only**로 제한하며 운영 CD를 호출하지 않는다.
- 공개 repo variable `SMARTDRAIN_AUTO_DEPLOY_ENABLED`가 명시적으로 `true`인 경우에만 마지막 dispatch job을 실행한다. 미설정/false이면 게시까지만 성공 처리한다. 최초 전환 뒤 활성화하며 앱 환경변수로 전달하지 않는다.
- PR 검사와 main 검사는 서로 다른 merge 결과 SHA를 검증하므로 필요하다. 동일 SHA에서 별도 push CI와 release CI가 중복 실행되도록 구성하지 않는다.
- `sha-<전체 SHA>` tag는 조회 편의용이고 배포 입력은 `ghcr.io/yellow-pang/<package>@sha256:<digest>`다. `latest`로 운영 이미지를 선택하지 않는다.
- 세 build가 모두 성공한 후 source SHA, source run ID/attempt, 세 digest를 담은 release manifest JSON을 artifact로 남긴다. 모델·`.env`·로그 전체는 포함하지 않는다.
- dispatch secret은 공개 repo의 **main으로 제한한 release environment**에 둔다. PR CI에는 secrets와 package write를 주지 않는다. 이미지 게시 job만 `packages: write`, 나머지는 필요한 read 권한만 준다. 외부 action은 검토한 commit SHA로 고정한다.

### 5.2 비공개 운영 저장소와 Mac

비공개 repo의 기본 branch에 `deploy-smartdrain.yml`과 실제 배포 script를 둔다. 공개 repo가 전달하는 것은 source run ID/attempt와 SHA이며, command·임의 URL·host 경로를 입력받지 않는다.

1. 자동배포가 활성화되면 공개 release의 마지막 job에서 비공개 workflow의 고정 ref로 `workflow_dispatch`한다. 첫 적용은 같은 receiver를 수동 호출하며 아래 출처 검증을 그대로 적용한다.
2. 비공개 workflow의 hosted 검증 job이 고정 source repo, 허용한 release workflow, event=`push`, branch=`main`, SHA, run attempt, 최종 conclusion=`success`를 API로 확인한다.
3. dispatch 순간 source run이 아직 종료되지 않을 수 있다. 종료를 제한 시간 동안 기다린 뒤 검증하며 timeout/failure/cancelled는 Mac job으로 넘기지 않는다. 공개 job은 dispatch 접수와 수신 run 링크를 기록하고 끝나며, 비공개 배포 완료까지 기다려 순환 대기하지 않는다.
4. 확인한 run의 지정 artifact에서 manifest를 읽고 SHA/digest/package 이름을 검증한다. 전달된 digest·URL을 그대로 믿거나 `source`/`eval`하지 않는다.
5. source SHA가 배포 시점의 origin/main과 다르면 오래된 요청으로 건너뛰고 기록한다. 최신 main의 publish 실패가 이전 요청의 강제 배포로 이어지지 않는다.
6. Mac job은 신뢰된 비공개 repo의 script만 실행한다. 공개 main에서는 같은 SHA의 Compose/nginx 설정만 고정 경로로 가져온다. Compose의 privileged, socket, host mount, port 변경도 운영 권한 변경으로 검토한다.

dispatch 권한은 **운영 repo 하나의 Actions write**로 제한한 fine-grained token을 기본안으로 한다. receiver의 source artifact 조회에는 source repo의 Actions read 권한을 별도로 확인한다. `GITHUB_TOKEN`이 다른 repo 권한을 자동 상속한다고 가정하지 않는다. [Workflow dispatch API](https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event)

GHCR package는 우선 비공개로 두고 운영 repo에 package Actions read 접근을 부여한다. 가능하면 job의 단기 `GITHUB_TOKEN`으로 pull한다. token을 Compose `.env`에 합치지 않고 job용 Docker 인증 경로만 사용한다. [GHCR 인증·접근 권한](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

Mac runner는 해당 비공개 repo 전용으로 등록한다. PR job을 배정하지 않고 기본 branch/ref를 확인한다. macOS runner에서는 Docker CLI를 실행하며 Linux 전용 `services:`/container action을 사용하지 않는다. 비공개 repo의 environment 기능 이용 가능 여부는 계정 요금제에 따라 확인하되, environment를 host 격리 수단으로 간주하지 않는다.

공개 release 성공은 게시·전달 성공이며 운영 배포 성공과 구분한다. 공개 run summary에서 비공개 배포 run을 찾을 수 있게 하고, 최종 배포 결과는 receiver summary와 Mac의 성공 release 기록을 함께 확인한다.

### 5.3 동시 실행과 보호 규칙

- PR CI는 이전 실행 취소가 가능하다. 실제 CD는 고정 concurrency group과 `cancel-in-progress: false`를 사용한다. migration 중 새 push가 실행을 취소해서는 안 된다.
- Mac에서 배포 script의 중복 수동 실행도 막는 project 단위 lock을 사용한다. 표준 도구로 구현하며 macOS에 없는 GNU `flock` 등을 당연히 가정하지 않는다.
- 같은 성공 SHA/digest 재요청은 기록 후 no-op한다. 중단된 시도는 Alembic revision·컨테이너·직전 기록을 확인하고 재개 여부를 판단한다.
- main/dev에는 CI required check와 PR 경유 정책을 구성한다. 실제 check가 한번 생성된 후 이름을 등록한다. 개인 운영에서 불가능한 타인 승인 수를 강제하지 않는다.
- 평상시 main 병합 후 배포마다 추가 수동 승인을 요구하지 않는 것이 목표다. 최초 bootstrap과 장애 복구는 통제된 수동 단계로 구분한다.

## 6. 운영 경로와 환경값

제안 운영 root는 `/Users/tro/apps/smartdrain`이다. 아직 만들지 않았으며 기존 공통 운영 경로가 있으면 구현 전에 맞춘다.

```text
/Users/tro/apps/smartdrain/
  .env                    # 기존 운영값 안전 복사, 추적 제외
  model/best.pt           # 기존 모델 복사본, SHA256 일치
  releases/<SHA>-<run-id>-<attempt>/  # 검증된 manifest, Compose, nginx 설정
  state/                  # 현재/직전 성공 release, 실패 checkpoint
  backups/                # 필요 시 DB 백업, 제한된 접근
```

- 개발 checkout과 runner `_work`를 운영 bind 원본으로 사용하지 않는다. 개발 파일을 이동·삭제하지 않고 필요한 파일을 복사해 hash를 검증한다.
- `.env.example`로 실제 운영값을 재작성하지 않는다. 기존 `.env`를 복사하고 key 존재만 대조한다. 실제 secret은 출력·artifact·문서에 남기지 않는다.
- model과 nginx 설정은 **실제 release의 절대경로**를 전달한다. 이동하는 `current` symlink를 live bind 원본으로 삼지 않는다.
- release 디렉터리는 성공 후 덮어쓰지 않는다. 같은 SHA라도 재build한 run/attempt와 digest가 다르면 별도 release로 보존한다.
- `NGINX_HTTP_PORT=127.0.0.1:8099`, DB 내부 `db:5432`, frontend same-origin을 유지한다. frontend 공개 build-time 값은 hosted build로 안전하게 이전하고 서버 비밀값은 전송하지 않는다.
- Compose는 항상 `-p smartdrain-mac`, 명시한 `--env-file`과 `-f`를 사용한다. runner shell에 남은 동명 환경값이 override하지 않도록 정리·검증한다.
- 현재 DB container의 실제 volume 이름과 project label을 기록해 전후 대조한다. project 이름 변경, 새 volume 생성, seed 자동 실행은 하지 않는다.

## 7. 예상 변경 파일과 책임

| 위치 | 수정/추가 | 현재 문제 → 계획 변경 | 영향·선택 이유 |
| --- | --- | --- | --- |
| `.github/workflows/ci.yml` | 추가 | 앱 CI 없음 → 재사용 가능한 FE/BE/AI 검사 | 기존 workflow가 없어 추가 필요. 테스트 framework 추가 아님 |
| `.github/workflows/release.yml` | 추가 | main 자동 게시 없음 → CI 후 ARM build/push/manifest/dispatch | public build 책임만 보유 |
| `docker-compose.yml` | 수정 | build 중심 → 세 앱 image reference 선택 변수 추가 | 기존 build 유지. backend/migrate/seed 동일 digest |
| `.env.example` | 수정 | 배포 image 선택 설명 없음 → image 변수 key·기본값 설명 | 실제 secret 추가 없음 |
| `frontend/package.json`, 필요 시 `frontend/Dockerfile` | 조건부 수정 | pnpm 버전 비명시 → 현재 확인된 버전 사용 | runtime upgrade·lockfile 재생성 제외 |
| `ai_service/scripts/smoke_analysis.py` | 수정 | 실패 sentinel 출력 후 exit 0 가능 → 고정 sample 검증 모드 | production inference/API 변경 없이 기존 smoke 정상화 |
| 기존 AI 테스트 영역 | 최소 보완 | smoke 실패 판정 회귀 보호 | sentinel/정상 unknown 구분 등 빠진 계약만 검증 |
| 비공개 운영 repo `.github/workflows/deploy-smartdrain.yml` | 추가 또는 기존 수정 | 검증된 배포 요청 수신·Mac job | 이 repo 외부 변경. 초기 위치·권한 확인 필요 |
| 비공개 운영 repo `scripts/deploy-smartdrain.sh` | 추가 또는 기존 수정 | digest pull·migration·기동·read-only smoke·기록 | Linux Jenkins build script와 책임이 달라 별도 소유 |
| `docs/verification/17_배포_운영_런북.md`, 필요한 README | 수정 | Jenkins/수동 Compose와 새 운영 방식 구분 | 과거 기록을 현재 실행 방식처럼 안내하지 않음 |
| `docs/steps/step-04-github-actions-cicd.md` | 구현 시작 시 추가 | Phase/Gate·비싼 실행·실패 해결·다음 작업 기록 | 계획 내용 복사나 명령 전체 dump를 하지 않음 |

이미지 변수는 `SMARTDRAIN_BACKEND_IMAGE`, `SMARTDRAIN_AI_IMAGE`, `SMARTDRAIN_FRONTEND_IMAGE`를 제안한다. 로컬 값 미지정 시 기존 build/name 동작을 유지한다. CD에서는 세 값이 허용된 digest reference인지 선검증하여 로컬 기본값으로 조용히 fallback하지 않게 한다.

기존 `.jenkins/scripts/deploy.sh`는 `up --build`와 VM 경로를 전제로 한다. 새 CD에서 wrapper로 호출하거나 두 script가 같은 배포를 연속 수행하도록 하지 않는다. 기존 VM 상태 확인 전에는 Jenkins 코드를 제거하지 않고 레거시로 표시한다. 재사용할 수 있는 nginx mount 검사와 smoke 계약은 새 운영 절차에 옮기되 Jenkins validation 전체를 중복 실행하지 않는다.

## 8. Phase 0 — 경계 확정과 bootstrap 준비

### Task 0.1 — 기준과 변경 권한 확인

현재 Git/remote/main-dev 차이, GitHub 설정, 공통 운영 세션의 Cloudflare 현황을 확인한다. 비공개 운영 repo 위치·접근 권한, runner 이름·경로, 운영 root를 확정한다. 다른 세션의 변경과 충돌하지 않는다. 첫 main 승격에 포함되는 누적 변경은 별도 PR에서 읽을 수 있게 정리한다.

### Task 0.2 — 운영 보존 자료와 실행 상태

Steps를 생성해 기준 HEAD, 실제 project/volume, app image ID, DB revision, 모델·sample·XGBoost artifact hash와 주요 AI dependency 버전을 기록한다. 비밀값은 제외한다. 현재 local image에는 최초 전환 복귀용 보존 tag를 부여할 수 있도록 대상 ID를 먼저 확인한다. 현재 Compose/nginx도 보존한다.

최초 전환 전 DB backup을 만들고 격리된 임시 DB에 복구 가능함을 확인한다. 운영 DB를 복구 시험 대상으로 사용하지 않는다. 이후 schema 변경이 있는 release는 백업과 호환성 확인 없이는 적용하지 않는다.

### Task 0.3 — 설정 공급과 디스크 기준

운영 `.env`/모델을 §6 경로에 복사·검증하는 절차를 준비한다. host 여유 공간과 `docker system df -v`를 기록한다. 상세 history 분석은 필수 Gate가 아니다. 모델은 image/GHCR에 넣지 않는다.

**Gate 0:** 운영 경계·복귀 자료·설정 공급 방법이 확정됨. 이미지별 상세 layer 분석 부족은 Gate 실패가 아니다. 실제 적용은 사용자에게 승인된 범위에서 수행한다.

## 9. Phase 1 — PR CI와 배포 입력 정상화

### Task 1.1 — 기존 Compose 확장

§7의 세 image 변수를 기존 파일에 반영한다. backend/migrate/seed는 반드시 동일 reference를 사용한다. DB/nginx/ports/volume/healthcheck의 서비스 계약은 유지한다. 로컬 build와 CD digest 두 입력에 대해 비밀 없는 fixture로 `docker compose config --quiet` 및 선택된 image·mount·port만 확인한다. 전체 config 출력으로 secret을 노출하지 않는다.

### Task 1.2 — 기존 smoke의 엄격한 판정

기존 `smoke_analysis`는 `run_analysis_job` 결과 출력 후 0을 반환하므로 YOLO의 `unknown/-1/-1` 실패 sentinel을 배포 성공으로 오인할 수 있다. 고정 sample 검증 모드를 기존 CLI에 추가한다.

- `drain_2.jpg`와 기존 sensor 입력, 현재 승인 모델로 reference를 먼저 확인한다. model/sample/XGBoost hash와 분류 결과를 연결하고 새 출력에 맞춰 기대값을 자동 갱신하지 않는다.
- 기존 분석 함수를 **한 번** 호출하고 callback payload·식별자·status·수치 유효성·분류 계약을 확인한다. 기존 validator를 재사용한다.
- 고정 정상 sample의 YOLO 실패 sentinel, 파일 누락/skip, 예외, reference 분류 불일치는 nonzero다.
- XGBoost의 정상 `unknown` label을 일괄 실패 처리하지 않는다. 과거 기록의 `unknown/field_check`는 후보 근거이며 현재 artifact로 기준을 확인한다. 부동소수점 bit 일치를 요구하지 않는다.
- production fallback·algorithm·callback 전송을 바꾸지 않는다. 이 smoke는 실제 callback을 전송하지 않아 운영 DB를 쓰지 않는다.

### Task 1.3 — CI 구성

| Job | 실제 검사 | 제외할 중복 |
| --- | --- | --- |
| Frontend | Node 22, 확인된 pnpm, frozen install → lint → production build | 별도 tsc, 같은 Docker lint target 재실행 |
| Backend | Python 3.12, 기존 requirements, 임시 PG16 → Alembic upgrade head → Uvicorn → summary API | 별도 compile/import, 존재하지 않는 pytest 구성, seed |
| AI | Python 3.12, 기존 명세를 제약으로 경량 dependency 설치 → 기존 전체 AI pytest | 대형 ai-test build, PR에서 best.pt 요구 |

AI 최소 설치 후보는 `python -m pip install -c ai_service/requirements.txt pytest fastapi python-dotenv python-multipart`다. 새 dependency 명세를 만들지 않는다. **아직 이 조합을 clean runner에서 검증하지 않았다.** 전체 테스트의 import 실패가 있으면 실제로 필요한 기존 dependency만 보완하며 실패 테스트를 건너뛰지 않는다.

Frontend PR build에는 secret 없는 검사용 공개값을 사용한다. Backend summary는 HTTP 200, `success=true`, `error=null`, 빈 DB의 5개 count=0, `latestUpdatedAt=null`과 단일 Alembic head 일치를 확인한다. Uvicorn 기동/API polling이 앱 import·DB readiness 검증도 담당한다.

**Gate 1:** clean hosted 환경에서 CI 통과, Compose 두 모드 정합성, smoke의 false-success 차단 확인. 아직 배포하지 않는다.

## 10. Phase 2 — Linux/arm64 이미지 게시

### Task 2.1 — 단일 architecture build

Gate 1 통과 후 자동 dispatch가 비활성 상태임을 확인하고, 누적 변경을 검토한 최초 `dev → origin/main` PR을 병합하여 정상 push main release를 만든다. 이 시점에는 게시만 수행하며 현재 Mac 서비스는 교체하지 않는다. 수동 build-only 실행 결과를 main provenance 대신 사용하지 않는다.

hosted `ubuntu-24.04-arm`에서 기존 Dockerfile의 최종 운영 stage를 사용한다. AI는 `runtime`, frontend는 `runner`, backend는 이름 없는 최종 stage이므로 `--target runtime`을 일괄 적용하지 않는다. 세 service를 별도 job으로 build하여 AI와 다른 image의 disk peak를 한 runner에 합치지 않는다. QEMU·amd64·multi-arch는 도입하지 않는다.

표준 public ARM runner의 문서상 disk는 14GB이므로 기존 VM의 10GB AI image 표시만으로 성공·실패를 단정할 수 없다. 첫 AI build에서 dependency 설치, layer export와 cache를 포함한 peak를 실측한다. 공간 부족이면 그 결과를 blocker로 기록하고 더 큰 build runner 등 필요한 대안만 다시 결정한다. 운영 Mac에서 무조건 build하도록 조용히 fallback하지 않는다. [Hosted runner 사양](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)

### Task 2.2 — cache와 manifest

첫 build는 cache 없이도 성공해야 한다. 서비스·platform별 BuildKit registry cache를 분리하고 release job만 갱신한다. AI test target을 게시하지 않는다. 같은 runtime image를 별도 test 이름으로 다시 build하지 않는다. cache가 없어도 correctness가 유지되어야 하며 저장 비용은 기록한다. [Registry cache](https://docs.docker.com/build/cache/backends/registry/)

Frontend는 main 게시 시 운영 공개 build-time 값을 사용한다. PR의 검사용 build와 결과가 다를 수 있어 runtime build가 다시 필요한 것이며, 이를 불필요한 중복 lint/test와 구분한다. Backend image 하나를 API/migrate/seed가 공유한다.

digest별 Linux/arm64와 source revision을 확인하고 manifest를 게시한다. 세 이미지 중 하나라도 실패하면 CD를 호출하지 않는다. 같은 SHA를 재build하면 unpinned dependency 때문에 digest가 바뀔 수 있으므로 run attempt와 digest를 함께 식별한다.

**Gate 2:** clean ARM build, GHCR 게시·인증된 pull, 세 digest/manifest 대응 성공. Mac 운영 서비스는 아직 바꾸지 않는다.

## 11. Phase 3 — Mac 배포 경로와 runner 준비

Task 3.1에서 §5의 비공개 receiver·권한·Mac runner를 구성한다. Task 3.2에서 §6 운영 경로를 준비하고 secret/model 접근, OrbStack context, Compose CLI 지원 옵션과 실제 DB volume을 검증한다. 임시 runner workspace에서 운영 bind를 만들지 않는다.

Task 3.3은 적용 없는 사전 검증이다. 검증된 candidate digest를 pull하고 후보 AI runtime에 동일 모델을 read-only mount하여 엄격한 smoke를 한 번 실행한다. 이 실행이 native import·OpenCV decode·YOLO CPU 추론·XGBoost 추론을 포함한다. 이어 후보 nginx 설정을 실제 upstream 이름이 해석되는 network 조건에서 `nginx -t`로 확인한다. pull/실행 시간과 추가 공간을 기록한다.

잘못된 repo/SHA/run/digest, 실패 publish, 누락 model, YOLO sentinel, 동시 배포 요청은 운영 중인 컨테이너를 변경하기 전에 차단되는지 확인한다. 검증용 입력은 실제 운영 변경 없이 사용한다.

**Gate 3:** main의 검증된 이미지에만 Mac 접근을 허용하고, 현재 서비스 유지 상태에서 candidate AI가 통과함. source run 확인 실패·GHCR 권한 오류·model 불일치는 배포 중단 사유다.

## 12. Phase 4 — 최초 배포와 자동배포 활성화

### Task 4.1 — 한 번의 배포 시도 순서

다음 `compose`는 고정 project/Compose/env/운영 root를 지정한 Docker Compose 명령의 설명용 축약이다. 별도 wrapper framework를 만들라는 뜻이 아니다. 이미지가 이미 준비되었음을 확인한 뒤 실행한다.

1. 배포 lock 획득, 최신 main/성공 run 재확인, 현재 release·DB revision·volume 기록.
2. 세 후보 digest pull, candidate AI smoke와 nginx 검사. Phase 3과 같은 digest/설정/모델로 연속 적용한다면 이미 성공한 검사를 재실행하지 않고 근거를 재사용한다.
3. 기존 DB healthy·volume 일치 확인. 필요하면 `compose up --no-build --pull never --no-deps --no-recreate --wait db`로 기존 DB를 유지한다. 미리 확인한 volume이 없으면 빈 DB 생성으로 진행하지 않는다.
4. migration 차이가 있으면 호환성·백업 확인 후 필요한 유지보수 시간을 적용한다. schema 변경과 충돌할 앱 writer/scheduler를 계속 실행하지 않는다.
5. `compose up --no-build --pull never --no-deps --force-recreate --exit-code-from migrate migrate`를 실행하고 종료 0과 revision을 확인한다.
6. `compose up --no-build --pull never --no-deps --wait backend frontend`.
7. `compose up --no-build --pull never --no-deps --wait ai-service`.
8. `compose up --no-build --pull never --no-deps --force-recreate --wait nginx`.
9. nginx bind 원본·readonly·내용 hash, 실제 실행 digest, localhost smoke 확인 후 성공 release를 원자적으로 기록한다.

`--no-deps`로 backend 의존성의 migrate가 다시 실행되지 않게 한다. 정상 시도 한 번당 migration 명령 한 번이며, crash/retry를 포함한 전역 exactly-once 보장은 아니다. 중단 후 현재 revision과 종료 기록을 확인하지 않고 재실행하지 않는다. `docker compose run`에는 `--no-build` 옵션이 없으므로 위 `up` 형태를 기준으로 구현한다. [Compose up](https://docs.docker.com/reference/cli/docker/compose/up/), [Compose run](https://docs.docker.com/reference/cli/docker/compose/run/)

DB/nginx image를 매 release마다 최신 tag로 pull하지 않는다. 세 앱 digest만 pull하고 기존 infra image를 확인해 사용한다. infra image가 없거나 교체가 필요하면 명시적으로 준비한다. 일반 배포에는 `down`, `down -v`, `--remove-orphans`, seed, prune을 넣지 않는다.

nginx는 기존 resolver가 앱 IP 변경을 처리하지만 host bind 파일의 inode/경로 교체까지 해결하지 않으므로 재생성한다. 무중단 배포를 약속하지 않으며 이 과정의 짧은 중단 시간을 측정한다.

### Task 4.2 — 첫 전환과 자동 호출 활성화

bootstrap 중에는 공개 release의 `SMARTDRAIN_AUTO_DEPLOY_ENABLED`를 false/미설정으로 두고 dispatch job만 skip한다. 비공개 receiver workflow는 활성 상태로 준비한다. Phase 2에서 이미 성공한 push main run을 입력하여 receiver를 수동 호출하고, 동일한 출처 검증을 거쳐 통제된 첫 적용을 수행한다. 적용 직전 source SHA가 최신 main인지 다시 확인한다. 비활성 receiver에 dispatch해서 source run 자체를 실패시키거나 feature/dev artifact를 main artifact로 위장하지 않는다.

첫 인수 검증에서는 기존 사용자 흐름으로 분석 요청 → AI callback → DB 저장 → WebSocket → 화면 반영까지 한 번 확인한다. 운영 데이터가 추가되는 검증임을 기록하고 seed나 임의 삭제로 초기화하지 않는다. Cloudflare 공개 접근은 공통 운영 세션과 확인하고 route를 직접 바꾸지 않는다.

Gate 4 통과 후 공개 repo의 `SMARTDRAIN_AUTO_DEPLOY_ENABLED=true`로 자동 호출을 활성화하고 다음 실제 main 병합으로 자동 경로를 확인한다. 기본 branch는 현재 dev이므로 workflow dispatch 준비 시 각 repo의 workflow가 필요한 ref에 존재하는지도 확인한다. 기본 branch를 main으로 바꾸는 것은 이번 필수 조건이 아니다.

**Gate 4:** 첫 적용·현재 데이터 유지·localhost 전체 흐름·수동 복귀 가능성을 확인. **Gate 5:** 이후 main 병합이 수동 checkout/build 없이 동일 절차로 배포되고 배포 SHA/digest가 일치함.

## 13. 검증 Matrix와 운영 인수

| 검증 | 시점·목적 | 성공 조건 | 실패 의미·중복 방지 |
| --- | --- | --- | --- |
| Compose 정적 입력 | Phase 1, image/path/port 실수 | local build와 digest 선택 모두 의도한 서비스/volume | config 오류. Docker COPY unit test 등 추가하지 않음 |
| FE CI | PR/main, lint·타입·build 회귀 | 기존 lint/build 통과 | 코드/build 환경. 별도 tsc 생략 |
| BE CI | PR/main, 빈 DB 재현 | migration head+실제 summary API | 코드/schema/DB 환경. health와 import 반복 생략 |
| AI pytest | PR/main, 계약·fallback 회귀 | 기존 전체 테스트 수집·통과 | 코드/설치 문제. ARM 실추론을 대신하지 않음 |
| ARM image 게시 | Phase 2와 main release | 세 digest 및 architecture 확인 | Docker/native build/runner 용량 |
| 후보 AI smoke | 변경 digest 배포 전 | 고정 sample CPU 추론·payload/reference 통과 | model/native/runtime/계약. DB callback은 보내지 않음 |
| 출처·권한·lock | receiver 초기 검증 | 잘못된 입력 차단, 신뢰된 main만 적용 | 권한/동시성 설계. 운영 mutation 없는 실패 경로 사용 |
| migration·기동 | 배포 시 | 한 번의 migration 성공, volume 유지, readiness | DB/앱 시작 환경. 실패하면 다음 단계 중단 |
| localhost smoke | 매 배포 후 | 페이지·DB REST·실제 이미지·WS handshake | proxy/runtime 경로. 운영 분석을 매번 자동 생성하지 않음 |
| 전체 callback E2E | 최초 인수 및 API/callback·환경값/Compose 네트워크 연결 변경 시 | 분석→저장→WS→UI 실제 반영 | 서비스 통합 회귀. 후보 추론과 역할이 다름 |
| 공개 접근·lifecycle | 공통 운영 일정과 조율 | HTTPS/WSS 및 runtime/로그인 후 복구, runner online | Tunnel/host lifecycle. 공유 host 재부팅을 독자 실행하지 않음 |

매 배포 smoke가 실패하면 배포 성공을 기록하지 않는다. 현재 nginx health/Jenkins smoke만으로는 WS·실추론을 보장할 수 없다. 다만 운영 데이터 변경을 동반하는 E2E를 모든 배포에 자동 삽입하지 않는다.

OrbStack 재시작/로그인/재부팅 후 기존 restart policy, 영속 bind, PostgreSQL volume, localhost, runner와 cloudflared 복구를 확인한다. Mac runner 서비스가 로그인에 의존하는지 명시하고 자동 로그인은 켜지 않는다. 공통 lifecycle 검증 일정이 남으면 앱 자동배포와 서버 운영 인수 상태를 분리해 기록한다.

## 14. 실패 대응과 수동 복귀

- CI/build/publish/pull/사전 추론 실패: 운영 변경 없이 종료. 원인과 마지막 성공 release를 기록한다.
- migration 실패: 이후 기동 금지. 현재 DB revision과 실제 적용 범위를 확인한다. 자동 downgrade/백업 restore를 실행하지 않는다.
- 앱 교체 후 실패: 성공 포인터를 갱신하지 않는다. 직전 앱이 현재 schema와 호환되면 보존한 digest/Compose/nginx로 앱을 `--no-build --pull never --no-deps` 순서로 복구한다. 복귀 중 migration/seed를 자동 실행하지 않는다.
- schema 비호환: 앱만 되돌리지 않는다. 정방향 수정 또는 DB 복구 선택을 먼저 보고한다. 추후 destructive migration은 이 일반 자동배포 승인으로 포괄하지 않는다.
- 최초 GHCR 전환은 이전 digest가 없을 수 있으므로 Phase 0의 local image tag와 원래 config가 복귀 근거다. 이후 성공 release digest와 설정을 보존한다.
- 실패 시 로그는 필요한 서비스·구간만 수집하고 secret/DSN/token을 제거한다. `.env`, 전체 inspect/config, 무제한 로그를 공개 artifact로 올리지 않는다.

DB·volume·기존 VM 삭제와 자동 prune은 복구 수단이 아니다. Health/RWR 컨테이너와 공유 Tunnel을 건드리지 않는다.

## 15. 시간·공간 비용

| 항목 | 현재 근거 | 계획과 측정 지점 |
| --- | --- | --- |
| Mac Docker 전체 | 조사 시 image 약 28.01GB, build cache 약 18.73GB | 여러 프로젝트와 shared layer 포함. 합을 SmartDrain 고유 점유로 해석하지 않음 |
| 과거 VM AI | 사용자 관찰 image 약 10GB, content 약 3.39GB | 새 ARM image/registry 저장량으로 그대로 환산하지 않음 |
| OrbStack | 조사 시 Linux aarch64, 10CPU, 약 8.39GB 할당 RAM | Mac 16GB 전체를 Docker 가용 RAM으로 계산하지 않음 |
| YOLO | 현재 파일 크기 52,067,329 bytes | 운영 복사본 hash 일치, image에 중복 COPY하지 않음 |
| AI pip/build/export | 새 hosted 환경 수치 없음 | 첫 cold build 시간·최대 disk/RAM·cache 유무 실측 필요 |
| FE/BE build | 새 CI 환경 수치 없음 | 각 job 시간 기록. 같은 단계 lint/test 재실행 금지 |
| GHCR/cache | 아직 구성 없음 | compressed image/cache별 실제 저장량과 계정 정책 확인 |
| Mac pull/inference/startup | 새 배포 경로 수치 없음 | 다운로드, model load, inference, migration, 서비스 교체 시간 실측 필요 |
| DB backup/release 보존 | 현재 정책 미확정 | 첫 백업 크기·복구 시간 측정, 무제한 보관 자동화 금지 |

Mac에는 현재+후보+직전 이미지와 pull 중 임시 공간이 필요하다. shared/unique layer를 고려해 여유를 판단한다. 공간이 부족하면 적용 전 중단하며 다른 프로젝트 cache를 임의 삭제하지 않는다. cache 정리·보존 자동화는 별도 범위로 남긴다.

## 16. 승인 경계, 기록과 최종 검토

### 16.1 구현 전에 확정할 결정

| 결정 | 제안 | 실제 적용 경계 |
| --- | --- | --- |
| 배포 소유 repo | 비공개 운영 repo 재사용, 없으면 `yellow-pang/mac-mini-deploy` | 별도 repo·권한 변경이므로 위치와 사용자 권한 확인 |
| Mac 운영 위치 | `/Users/tro/apps/smartdrain`, project `smartdrain-mac` 유지 | 기존 env/model 안전 복사, runner 등록은 승인된 구현에서 진행 |
| GitHub 권한 | main 보호, release environment, 제한 token, GHCR 접근 | 비밀값 입력·보관과 설정 변경 범위 확정 |
| 첫 적용 | 보존 자료·backup·검증 후 main의 통제된 첫 배포 | 현재 컨테이너 교체/DB migration, E2E 데이터 추가 포함 |

현재 요청은 **브랜치 checkout과 계획 문서 작성까지**다. 구현 승인을 받으면 위 제안 범위를 구체적인 작업 기준으로 사용하며 이미 승인한 같은 내용을 반복 요청하지 않는다. 새 비용·권한 확대·schema/서비스 계약 변경이 필요할 때만 원인과 대안을 먼저 보고한다.

### 16.2 실행 기록과 복구

구현 시작 시 Steps에 Current Phase/Task/Gate, Next Action 하나, 실제 변경·명령 결과·측정·미해결 blocker를 기록한다. 특히 AI build, migration, 첫 배포, 실패 해결, 환경 변경, 세션 종료 시 갱신한다. context 복구 순서는 `AGENTS → 기준 Analysis/이전 기록 → 이 Plan → Steps → 실제 Git/운영 상태`다. 이미 완료한 build/migration/seed/배포를 기억만으로 반복하지 않는다.

### 16.3 Self-review

- Mac 이전과 CI/CD·이미지 최적화를 구분했는가: 예. 이전 실행 결과를 재사용하고 최적화/runtime upgrade는 제외했다.
- 기존 오류 대신 우회 코드를 쌓는가: 아니오. Compose와 smoke는 직접 수정한다. 새 workflow/운영 script는 현재 없는 실행 책임을 담당한다.
- AI 계약을 바꾸는가: 아니오. production fallback은 유지하고 배포용 reference smoke의 성공 판정만 보완한다.
- 테스트가 반복되는가: PR 계약, ARM 실제 runtime, 배포 후 연결, 최초 callback E2E의 실패 범위를 구분했다.
- 현재 데이터가 새 DB로 바뀔 수 있는가: project/volume 고정과 사전 비교를 필수로 두었다. migration 재실행과 seed를 분리했다.
- 운영 host 경계가 명확한가: 공개 PR은 hosted에서만 실행한다. private runner도 완전한 host 격리는 아니라는 제한을 명시했다.
- 시간/공간을 낙관했는가: 아니오. hosted AI cold build는 미검증이며 14GB disk 적합성을 Gate 2에서 측정한다.
- 외부 공개와 lifecycle을 누락했는가: 공통 운영 소유권을 유지하고 별도 인수 결과를 기록한다. CI/CD가 Tunnel 전환을 대행하지 않는다.

**최종 판단:** 추가 대규모 Mac 이전 Analysis는 필요하지 않다. 이 계획으로 CI/CD 구현을 시작할 수 있으나 현재는 미구현이다. 우선순위는 `경계 확정 → 기존 파일 최소 수정·PR CI → ARM 게시 실측 → 비공개 CD 준비 → 통제된 첫 배포 → main 자동배포·운영 인수`다. 첫 다음 작업은 **Task 0.1: 비공개 배포 repo와 Mac 운영 경로·권한 확정**이다.
