# Mac mini + OrbStack 이전 사전 분석

> 분석일: 2026-09-20
>
> 분석 기준: `dev`, HEAD `5cd6c07dac1e6abd7845307a88e681f9ad1aa36f`
>
> 문서화 브랜치: `chore/macos-orbstack-migration`
>
> 상태: 사전 분석 완료, 구현·실행 검증 전. 이 문서는 Implementation Plan이나 이전 완료 기록이 아니다.

## 분석 범위와 결론

기존 Windows 노트북의 Linux VM에서 운영하던 SmartDrain을 Apple Silicon Mac mini 16GB + OrbStack으로 이전할 수 있는지 검토했다. 현재 코드·Compose·기존 환경변수·새 PostgreSQL로 기능을 재현하는 것이 우선이며, DB 데이터 복사는 필수가 아니다.

**이전 가능성은 있으나 현재 HEAD 그대로 전체 `docker compose build/up`을 실행하면 정상 재현되지 않는다.** Backend의 Docker COPY·실행 경로 오류, router import 누락, 운영 AI 컨테이너의 샘플 이미지 공급 누락이 확인되었다. 이 문제들은 ARM 전용 문제가 아니다.

**CUDA base image나 NVIDIA runtime을 반드시 요구하는 구성은 발견되지 않았다.** AI의 Linux/arm64 CPU 추론은 별도로 검증해야 한다. 외부 `best.pt`와 미고정 Python dependency 조합은 아직 확인되지 않았다.

분석 중 코드 수정, build/up, migration 적용, 기존 VM 접근·변경, image/volume 삭제, Jenkins·Cloudflare 변경은 하지 않았다. 실제 `.env`는 존재만 확인했으며 내용·비밀값은 읽거나 출력하지 않았다. 이후 문서화 작업에서 브랜치 생성·체크아웃과 이 문서 및 문서 인덱스 작성만 수행했다.

근거의 성격은 다음처럼 구분한다.

- **저장소 확인**: 분석 기준 HEAD의 파일·설정으로 확인한 사실.
- **환경 확인**: 분석 시점의 로컬 Mac·OrbStack을 읽기 전용으로 확인한 결과.
- **사용자 제공**: 기존 VM 수치·운영 경로. 기존 서버에서 재측정하지 않았다.
- **외부 자료 확인**: 공식 image·wheel 지원 자료. 실제 설치 성공을 의미하지 않는다.
- **실검증 필요**: build, 모델 추론, DB 초기화, 공개 도메인 등 아직 실행하지 않은 항목.

## 1. 현재 저장소 구조

### 저장소와 로컬 환경

| 항목 | 분석 시점 결과 |
| --- | --- |
| 작업 경로 | `/Users/tro/dev/smartdrain-agent-upgrade` |
| Git 상태 | `git status --short --untracked-files=all` 출력 없음 |
| 브랜치·HEAD | `dev` / `5cd6c07dac1e6abd7845307a88e681f9ad1aa36f` |
| origin | `https://github.com/yellow-pang/smartdrain-agent-upgrade.git` |
| upstream | `https://github.com/star2871/smartdrain.git` |
| 호스트 | `Darwin arm64` |
| Docker context | `orbstack` |
| Docker CLI / Compose | `29.4.0` / `v5.1.2` |
| Docker 서버 | OrbStack, `aarch64`, CPU 10개 표시 |
| Docker에 보이는 메모리 | 8,393,289,728 bytes, 약 7.82GiB |
| 호스트 파일시스템 여유 | 약 163GiB. Docker 내부 저장공간 한도와 동일하다는 뜻은 아님 |

Mac의 물리 RAM 16GB 전체가 Docker에 표시되는 상태는 아니다. 위 값은 분석 시점 관측값이며 이후 실행 환경에서는 재확인한다.

```text
frontend/              Next.js 화면, API·WebSocket client
backend/
  app/                 FastAPI, DB 모델, callback, seed
  alembic/             migration 3개
  alembic.ini
ai_service/
  http/                HTTP API, callback 전송
  analysis/            분석 조합
  yolo/                YOLO + OpenCV
  xgboost/             위험도 추론
  image_source/        시설별 로컬 샘플 선택
  model/               XGBoost JSON
mock_data/             샘플·데모 이미지
mock_ai_server/        별도 mock 서버
nginx/                 운영·개발 proxy 설정
.jenkins/scripts/      검증·배포·seed·smoke script
jenkins/               Jenkins Dockerfile·Compose
docs/                  기준·검증·레거시 문서
.agents/               프로젝트 Skill
```

### 확인한 주요 파일

| 영역 | 근거 |
| --- | --- |
| 작업 지침 | [루트 AGENTS](../../AGENTS.md), [Frontend](../../frontend/AGENTS.md), [Backend](../../backend/AGENTS.md), [AI](../../ai_service/AGENTS.md) |
| 대표 문서 | [루트 README](../../README.md), [Frontend README](../../frontend/README.md), [Backend README](../../backend/README.md), [AI README](../../ai_service/README.md) |
| 앱 Compose | [기본 Compose](../../docker-compose.yml), [개발 override](../../docker-compose.dev.yml) |
| Dockerfile 전체 | [Frontend](../../frontend/Dockerfile), [Backend](../../backend/Dockerfile), [AI](../../ai_service/Dockerfile), [Jenkins](../../jenkins/Dockerfile) |
| 빌드 제외 | [.dockerignore](../../.dockerignore) |
| Jenkins | [Jenkinsfile](../../Jenkinsfile), [Jenkins Compose](../../jenkins/docker-compose.jenkins.yml), [shell script](../../.jenkins/scripts) |
| 환경변수 정의 | [루트 예시](../../.env.example), [Frontend 예시](../../frontend/.env.example), [Backend 예시](../../backend/.env.example), [AI 예시](../../ai_service/.env.example) |
| nginx | [운영](../../nginx/default.conf), [개발](../../nginx/default.dev.conf) |
| DB | [Alembic 설정](../../backend/alembic.ini), [migration](../../backend/alembic/versions), [seed](../../backend/app/seeds/seed_mock_data.py) |
| dependency | [AI requirements](../../ai_service/requirements.txt), [Backend requirements](../../backend/requirements.txt), [frontend package](../../frontend/package.json), [pnpm lock](../../frontend/pnpm-lock.yaml) |
| 배포 문서 | [운영 런북](17_배포_운영_런북.md), [개발·운영 가이드](../../frontend/docs/deployment/development-production-guide.md), [Jenkins workspace 가이드](../../frontend/docs/deployment/jenkins-custom-workspace-guide.md) |
| 모델 | [artifact 기준](../reference/15_AI_모델_아티팩트_관리_명세.md), [XGBoost JSON](../../ai_service/model/sewer_xgboost_model.json) |

`.github/workflows/` 파일은 없다. AI·Backend에는 `requirements.txt`만 있고 Python lockfile·`pyproject.toml`은 없다. Frontend에는 pnpm lock과 package-lock이 함께 있지만 Dockerfile은 pnpm을 사용한다.

루트 실제 `.env`는 존재한다. 확인한 기본 위치의 `backend/.env`, `ai_service/.env`, `frontend/.env.local`은 없었다. 외부 경로의 환경파일·모델은 확인하지 않았다.

### 문서와 구현의 불일치

- 루트 README는 `refactor/global-architecture`를 설명하지만 분석 시점 브랜치는 `dev`였다.
- README·구조 문서에 나오는 `ai-vision/`은 현재 없다.
- 오래된 Jenkins 문서는 `/home/yp/apps/apps/smart-drain`을 설명하지만 현재 설정은 `/home/yp/apps/smart-drain`이다.
- 문서의 AWS·Vercel·GitHub Actions 흐름은 현재 저장소의 실행 가능한 배포 구현으로 확인되지 않는다.
- AI runtime 문서는 `drain_5.jpg`가 없다고 설명하지만 현재 파일은 존재한다.

## 2. 현재 배포 흐름

현재 Jenkinsfile과 script로 복원한 흐름이다. 기존 VM이 이 HEAD로 운영되었다는 증거는 아니다.

```text
Jenkins 작업 실행
  → checkout scm
  → Secret File을 배포 경로의 .env로 복사
  → Docker socket·경로·Compose 사전 검사
  → Compose 설정 검사
  → frontend lint stage 빌드
  → AI test image 빌드·pytest
  → AI runtime 빌드·모델 파일 존재 및 크기 검사
  → docker compose up --detach --build --remove-orphans
  → nginx 강제 재생성·mount 확인
  → 선택적 seed
  → nginx 경유 frontend·dashboard API smoke
```

Compose의 기동 의존성은 다음과 같다.

```text
db healthy → migrate 성공 → backend healthy → ai-service 시작
frontend healthy + backend healthy → nginx 시작
```

- Git push → Jenkins 자동 실행 webhook/job 설정은 저장소에서 확인되지 않는다.
- `checkout scm`의 실제 저장소·브랜치는 Jenkins job 설정에 달려 있다.
- `DEPLOY_BRANCH=dev`는 선언되어 있지만 checkout 강제에 사용되지 않는다.
- 배포 script는 개발 override를 명시적으로 합치지 않는다. 기본 Compose에 `COMPOSE_NGINX_CONF_PATH=./nginx/default.dev.conf`를 적용한다.
- nginx는 AI health를 기다리지 않는다. 화면 접속 성공은 AI 정상의 증거가 아니다.
- Cloudflare 기동·갱신은 배포 script에 포함되지 않는다.

## 3. Jenkins가 담당하는 실제 역할

| 항목 | 현재 설정 |
| --- | --- |
| 대상 | SmartDrain frontend·backend·AI 검증 및 배포 |
| 실행 방식 | 호스트 `/var/run/docker.sock` 공유. 별도 DinD daemon 구성 아님 |
| Jenkins 데이터 | `smartdrain-jenkins-home:/var/jenkins_home` |
| Workspace | `/home/yp/apps/smart-drain`을 호스트·컨테이너에 같은 절대경로로 mount |
| 실행 사용자 | Compose에서 `root` 지정 |
| Jenkins port | `8082:8080`, `50001:50000` |
| Maven | 호출·캐시 구성 없음 |
| npm/pnpm | Docker build 안에서 pnpm 실행, 전용 호스트 cache mount 없음 |
| pip | `--no-cache-dir`, 전용 cache volume 없음 |
| Docker cache | socket이 연결된 호스트 Docker가 관리 |

근거: [validate.sh](../../.jenkins/scripts/validate.sh), [deploy.sh](../../.jenkins/scripts/deploy.sh), [smoke-test.sh](../../.jenkins/scripts/smoke-test.sh).

매 배포마다 AI build 명령을 호출한다. 다만 requirements layer가 유효하면 pip 설치 layer를 재사용하므로 매번 전체 dependency를 다시 다운로드한다고 단정할 수 없다.

`smartdrain-dev-ai-test`는 `--target test`로 만든 pytest용 이미지다. `docker run --rm`은 실행 컨테이너만 제거하고 이미지는 남긴다. 태그 교체 후 과거 이미지·cache가 남을 수 있으며, script에는 보존량 관리가 없다. 실제 누적은 Docker GC와 빌드 이력을 함께 확인해야 한다.

**Jenkins는 Mac의 수동 Compose 기능 재현에 필수가 아니다.** 앱이 Jenkins API나 Jenkins 데이터에 의존하는 구조는 발견되지 않았다. Jenkins 제거와 저장소 내 Jenkins 파일 삭제는 별개의 결정이다.

## 4. Frontend / Backend / AI / DB 책임 분리

| 구성 | 실행 방법 | 책임 |
| --- | --- | --- |
| Frontend | Node 22 Alpine, Next.js 16.2.6·React 19, `pnpm build`, standalone `server.js` | 화면·지도·REST·WebSocket |
| Backend | Python 3.12 slim, FastAPI, `uvicorn app.main:app` | DB, 분석 요청, callback 저장, WebSocket |
| AI | Python 3.12 slim, `uvicorn ai_service.http.app:app` | OpenCV·YOLO·XGBoost·callback |
| DB | PostgreSQL 16 | 시설·센서·결과·분석 job |
| nginx | nginx 1.28 Alpine | 단일 HTTP 진입점과 reverse proxy |

Frontend는 DB·AI를 직접 호출하지 않는다. Backend 내부에 `app/ai/` 코드가 남아 있지만 현재 비동기 분석은 별도 AI service로 요청한다.

Frontend의 `COMPOSE_FRONTEND_API_BASE_URL`은 [Next 설정](../../frontend/next.config.mjs)에서 공개 변수 `NEXT_PUBLIC_API_BASE_URL`로 변환된다. 빈 값이면 `/api/...`를 현재 origin에 요청하고 [WebSocket client](../../frontend/lib/websocket/drain-status-socket.ts)도 같은 origin의 ws/wss를 사용한다. production 공개 변수는 build에 반영되므로 변경 시 frontend 재빌드가 필요하다. Kakao 공개 키도 같은 방식이다.

Backend·AI 코드의 localhost 기본값은 Compose가 `db`, `backend`, `ai-service` 서비스 이름으로 대체한다. 조사한 실행 경로에서 기존 VM IP·공개 도메인을 반드시 요구하는 하드코딩은 발견되지 않았다. VM 절대경로 종속은 주로 Jenkins workspace와 외부 모델 입력값에 있다.

Frontend native dependency인 Next SWC·sharp·Tailwind oxide·lightningcss는 pnpm lock에 Linux ARM64 및 musl variant가 존재한다. Backend의 `psycopg[binary]`, `uvicorn[standard]` 등 native dependency도 실제 ARM import·기동 검증은 남는다.

## 5. AI 이미지가 큰 원인

사용자 제공 기존 VM 관측값:

- `smartdrain-dev-ai-service:latest`: Docker disk usage 약 10GB, content size 약 3.39GB.
- `smartdrain-dev-ai-test:latest`: 약 10GB 수준.
- Docker 전체 Image 약 34GB, Build Cache 약 8.7GB.
- nginx 약 12MB, PostgreSQL 약 52MB, AI 약 60MB, Backend 약 84MB, Frontend 약 100MB의 컨테이너 RAM 관측.

기존 VM의 image layer·설치 목록은 읽지 않았으므로 원인별 GB 수치를 확정할 수 없다.

| 요소 | 현재 Dockerfile·dependency 근거 | 용량 판단 |
| --- | --- | --- |
| Base | `python:3.12-slim` | CUDA base 아님. digest별 크기 실측 필요 |
| Ultralytics | 버전 미고정 | torch·torchvision 유입 경로 |
| PyTorch·CUDA 관련 패키지 | Ultralytics 전이 dependency | 대용량 원인의 우선 확인 대상. 실제 설치 버전·GB 실측 필요 |
| XGBoost | 일반 `xgboost`, 버전 미고정 | GPU 지원 binary·관련 dependency 확인 필요 |
| Scientific Python | numpy·pandas·scikit-learn | native package 누적, 설치 크기 실측 필요 |
| OpenCV·OS library | opencv-python, GL/X11/GLib/OpenMP 계열 | runtime binary·library 크기 실측 필요 |
| YOLO weight | `.dockerignore` 제외, 파일 bind mount | 현재 구조에서는 이미지 10GB 원인 아님 |
| XGBoost weight | JSON COPY | 351,715 bytes, 약 343KiB |
| AI 소스 전체 | `COPY ai_service/` | 분석 시점 로컬 파일 합계 약 0.50MB |
| pytest | 공통 requirements에 포함 | production에도 포함. GB급 주원인이라는 근거 없음 |
| apt cache | 같은 RUN에서 `/var/lib/apt/lists/*` 제거 | package list 누적 구조 아님 |
| pip cache | `--no-cache-dir` | pip download cache 누적 구조 아님 |
| compiler | gcc/build-essential 명시 설치 없음 | compiler 잔존이 주원인이라는 근거 없음 |

Ultralytics는 torch·torchvision을 기본 dependency로 가진다. 저장소는 TensorFlow·ONNX export extras를 요청하지 않으며, transformers·sentence-transformers도 선언하지 않는다. [Ultralytics 공식 정의](https://raw.githubusercontent.com/ultralytics/ultralytics/main/pyproject.toml)

**CPU 서버에서 실행한다고 pip가 CPU 전용 PyTorch를 설치하는 것은 아니다.** PyTorch 2.11 릴리스는 Linux x86_64·aarch64의 일반 PyPI 설치에 CUDA 13.0 wheel을 기본 제공한다고 설명한다. 현재 requirements는 이를 제한하지 않는다. 기존 이미지에 실제 어떤 버전이 설치되었는지는 별도 확인 대상이다. [PyTorch 공식 릴리스](https://github.com/pytorch/pytorch/releases/tag/v2.11.0)

```text
requirements → ultralytics → torch / torchvision → 배포판별 CUDA 관련 package
             → xgboost → 배포판별 GPU 지원 구성
             → OpenCV / scientific Python
```

AI Dockerfile은 `base → test`, `base → runtime` stage가 있으나 runtime은 base의 모든 dependency를 상속한다. 경량 runtime으로 dependency를 분리한 multi-stage 최적화는 아니다. test stage가 pytest를 다시 설치하지만 base requirements에 이미 pytest가 있다.

test와 runtime은 같은 base layer를 공유할 수 있다. **10GB + 10GB를 실제 점유 20GB로 합산하면 안 된다.** disk usage와 content size도 압축·전개·공유 layer 집계 차이를 확인해야 한다.

기존 VM에서 나중에 사용할 읽기 전용 진단 명령이며 이번에는 실행하지 않았다.

```bash
docker system df -v
docker history --no-trunc smartdrain-dev-ai-service:latest
docker image inspect smartdrain-dev-ai-service:latest \
  --format 'arch={{.Architecture}} size={{.Size}} layers={{json .RootFS.Layers}}'
docker image inspect smartdrain-dev-ai-test:latest \
  --format 'arch={{.Architecture}} size={{.Size}} layers={{json .RootFS.Layers}}'
```

## 6. Apple Silicon arm64 위험요소

대상은 macOS Python이 아니라 **Linux/arm64 컨테이너**다.

| 대상 | 공식 배포·저장소 확인 | 남는 검증 |
| --- | --- | --- |
| Python 3.12 slim, Node 22 Alpine | 공식 ARM64 image 지원 | 실제 tag 해석·build |
| PostgreSQL 16, nginx 1.28 Alpine | ARM64 배포 지원·artifact 확인 | 실제 manifest·pull·기동 |
| NumPy·pandas·scikit-learn | Python 3.12 Linux ARM64 wheel 존재 | 선택된 버전 조합 |
| OpenCV | Linux ARM64 wheel 존재 | import·native library·이미지 처리 |
| PyTorch | Linux ARM64 및 CPU wheel 배포 경로 존재 | torch/torchvision 조합·연산·모델 로드 |
| XGBoost | Linux aarch64 공식 지원 | 저장된 JSON 로드·추론 |
| psycopg binary | Python 3.12 Linux ARM64 wheel 존재 | DB 연결 |
| Frontend native package | lockfile에 ARM64 Linux·musl variant | Alpine에서 install·build |

지원 배포물이 있다는 사실은 미고정 requirements 전체가 현재 성공한다는 증명이 아니다. 최신 wheel의 GPU 지원 구성도 달라질 수 있다.

공식 근거:

- Image: [Python](https://raw.githubusercontent.com/docker-library/official-images/master/library/python), [Node](https://raw.githubusercontent.com/docker-library/official-images/master/library/node), [PostgreSQL](https://raw.githubusercontent.com/docker-library/official-images/master/library/postgres), [nginx ARM64 artifact](https://hub.docker.com/layers/arm64v8/nginx/1.28-alpine/images/sha256%3A891d82d494e8047b780f0eb9d65ab4d1551224fd3bdc9fb78028e1666f9d4ffb).
- Wheel: [NumPy](https://pypi.org/project/numpy/2.2.6/), [pandas](https://pypi.org/project/pandas/2.2.3/), [scikit-learn](https://pypi.org/project/scikit-learn/), [OpenCV](https://pypi.org/project/opencv-python/), [PyTorch CPU](https://download.pytorch.org/whl/cpu/torch/), [XGBoost](https://xgboost.readthedocs.io/en/stable/install.html), [psycopg binary](https://pypi.org/project/psycopg-binary/3.3.0/).

저장소에는 `FROM nvidia/cuda`, NVIDIA runtime, GPU device reservation, `platform: linux/amd64`, `.cuda()` 강제가 없다. [YOLO analyzer](../../ai_service/yolo/analyzer.py)는 `predict()`에 device를 지정하지 않고, [XGBoost predictor](../../ai_service/xgboost/model_predictor.py)는 일반 `XGBClassifier()`로 JSON을 로드한다.

따라서 NVIDIA 필수 blocker는 현재 확인되지 않았다. 다만 외부 `best.pt`의 custom layer·학습 버전은 미확인이고, 기존 VM의 실제 GPU 사용 여부도 확인하지 않았다.

MPS는 macOS용 backend이므로 Linux 컨테이너에서 Apple GPU를 그대로 사용한다고 가정하지 않는다. 이번 검증 기준은 CPU다. [PyTorch MPS](https://docs.pytorch.org/docs/main/notes/mps.html)

OrbStack의 Rosetta는 amd64 실행 대안이지만 NVIDIA GPU를 제공하지 않는다. ARM 실패가 확인되기 전 emulation을 기본 구성으로 도입할 이유는 없다. 성능 비용은 실측 필요다. [OrbStack 공식 설명](https://orbstack.dev/)

## 7. 현재 DB 초기화 재현성

```text
20260618_0001: drains / sensor_data / yolo_results / xgboost_results 생성
  → 20260619_0002: analysis_jobs 생성
  → 20260623_0003: analysis_jobs.trigger_type 추가
```

PostgreSQL은 `postgres_data` named volume을 사용한다. Compose의 `migrate`가 `alembic upgrade head`를 실행하고 Backend는 성공 후 시작한다. FastAPI startup에서 `create_all()`을 실행하는 구조는 아니다.

**새 DB 초기화 수단은 있지만 현재 Backend Dockerfile 오류 때문에 실제 재현은 막혀 있다.** migration chain은 정적으로 확인했고 새 DB에 적용하지 않았다.

Seed는 `seed` profile로 분리되어 기본 `up`에 포함되지 않는다. DR-001~DR-005 시설·센서·분석 예시를 생성한다. 기존 drain_code는 중복 생성하지 않지만, 기존 결과의 누락된 이미지 URL을 보완할 수 있다. Dashboard 집계는 빈 목록·0건을 처리한다. 빈 DB에는 분석 대상·센서가 없으므로 기존 데모 재현에는 seed 또는 별도 등록이 필요하다.

| DB 외 데이터 | 이전 판단 |
| --- | --- |
| YOLO `best.pt` | 별도 확보 필수. 저장소 기본 위치에 없음 |
| XGBoost JSON | Git 추적, 별도 VM 복사 불필요 |
| 기본·demo 이미지 | Git 추적, 컨테이너 공급 경로는 보완 필요 |
| scenarios 이미지 | 현재 good/caution/danger/unknown 디렉터리는 `.gitkeep`만 존재. VM 추가 이미지가 있었다면 확보 필요 |
| Preview 업로드 | AI가 임시 파일 생성 후 삭제. 영속 업로드 보관 구현 발견되지 않음 |
| Runtime cache | 영속 volume 선언 없음. VM 추가 파일은 미확인 |
| Vector index | 실행 코드·dependency에서 발견되지 않음 |

## 8. 네트워크 / Cloudflare 구조

사용자가 제공한 기존 publish는 `127.0.0.1:8099 → 80`이다. 현재 Compose는 다음처럼 변수화되어 있다.

```yaml
ports:
  - "${NGINX_HTTP_PORT:-80}:80"
```

같은 publish를 만드는 비밀값이 아닌 설정 예시는 다음과 같다. 실제 `.env` 값은 확인하지 않았다.

```dotenv
NGINX_HTTP_PORT=127.0.0.1:8099
```

기본값은 loopback 전용이 아니다. 기본 Compose에서 host publish는 nginx만 있고 frontend·backend·AI·DB는 없다. Dockerfile의 EXPOSE는 host publish와 다르다. 개발 override는 별도 `NGINX_DEV_HTTP_PORT`를 사용한다.

```text
/       → frontend:3000
/api/   → backend:8000
/ws/    → backend:8000 (WebSocket upgrade)
```

운영 nginx는 Swagger 경로를 404 처리하고 개발 nginx는 Backend로 proxy한다. Jenkins는 개발 nginx 설정을 선택한다.

실제 Tunnel ingress·cloudflared 서비스는 저장소에 없다. **Cloudflare가 기존 nginx만 바라보았는지는 저장소로 확정할 수 없다.** Mac 호스트에서 cloudflared를 실행하면 `http://localhost:8099` 구조를 유지할 수 있다. cloudflared를 컨테이너에서 실행하면 그 컨테이너의 localhost는 호스트가 아니므로 연결 주소를 별도로 확인한다.

same-origin API·WebSocket을 유지하면 Cloudflare 이전 때문에 앱 로직을 바꿀 이유는 없다. 도메인이 변경되면 Kakao 지도 허용 도메인 등 외부 설정도 확인한다. Cloudflare 설정은 변경하지 않았다.

## 9. Mac mini + OrbStack에서 그대로 사용할 수 있는 부분

- Frontend·Backend·AI·PostgreSQL·nginx 책임 경계.
- Python 3.12, Node 22, PostgreSQL 16 기준.
- Next.js standalone build, Compose 서비스 이름 기반 내부 통신.
- nginx same-origin REST·WebSocket 분기.
- Alembic chain, 선택적 seed, PostgreSQL named volume.
- YOLO 파일 하나의 read-only mount, XGBoost JSON의 image 포함.
- 현재 API·callback·WebSocket 계약과 분석 알고리즘.

GHCR·GitHub Actions·multi-arch CI·자동 rollback은 기능 재현의 전제조건이 아니다.

## 10. Mac 이전을 위해 반드시 수정해야 하는 부분

아래는 ARM 전용 대응이 아니라 현재 HEAD를 새 환경에서 실행하기 위한 결함 수정이다. 수정은 아직 적용하지 않았다.

| 문제 | 확인 근거 | 영향 |
| --- | --- | --- |
| 없는 Alembic 파일 COPY | Backend Dockerfile의 `COPY alembic.ini ./`; 실제 위치는 `backend/alembic.ini` | image build 실패 |
| Backend 앱 복사 위치 | WORKDIR `/app/backend`에서 `COPY backend/ ./backend/` | 실제 앱은 `/app/backend/backend/app`, PYTHONPATH는 `/app/backend`로 불일치 |
| Router import 누락 | `main.py` 마지막의 `realtime_simulator.router`, 해당 이름 import 없음 | 경로 복구 후에도 앱 import 시 NameError |
| Backend 샘플 복사 위치 | 현재 `/app/backend/mock_data`; 정상 앱 배치 `/app/backend/app` 기준 코드는 `/app/mock_data`를 참조 | 이미지 제공·seed URL·데모 이미지 문제 |
| AI 운영 샘플 공급 누락 | AI Dockerfile은 `ai_service/`만 COPY, 기본 Compose는 weight만 mount | `/app/mock_data/ai_image_samples` 부재 |

AI `/health`는 모델을 로드하지 않는다. 샘플 읽기 실패는 unknown 결과로 처리될 수 있다. 따라서 health 또는 HTTP 응답만으로 기능 재현을 판정하면 안 된다. 개발 override의 전체 저장소 mount는 일부 파일 누락을 가릴 수 있지만 기본 운영 Compose 문제를 해결하지 않는다.

최소 보완 범위는 기존 Backend Dockerfile의 COPY·실행 경로 정합성, 기존 router import, 기존 샘플 이미지의 컨테이너 전달이다. 새 서비스·새 계층·모델 변경을 요구하지 않는다.

환경 준비도 필요하다.

- 신뢰할 수 있는 기존 `best.pt` 확보, Mac의 유효한 `SMARTDRAIN_YOLO_MODEL_PATH`와 읽기 권한 확인.
- `POSTGRES_*`와 `COMPOSE_DATABASE_URL`의 계정·DB·비밀번호 일치. 새 DB host는 Compose의 `db:5432`인지 확인.
- nginx loopback 8099 입력 및 기존 Jenkins의 개발 nginx 선택을 재현할지 결정.
- Frontend API same-origin 입력과 Kakao 공개 키 준비.

기본 위치에 weight는 없지만 실제 `.env`의 외부 모델 경로를 읽지 않았으므로 Mac 전체에 모델이 없다고 단정하지 않는다.

## 11. Mac 이전과 별개의 이미지/배포 최적화 항목

### 현재 cache 구조

- AI·Backend는 requirements COPY → pip install → 소스 COPY 순서다.
- Frontend는 package·pnpm lock COPY → install → 소스 COPY 순서다.
- Frontend runner에는 standalone build 결과를 복사한다.
- `COPY . .`로 전체 저장소를 image에 넣는 Dockerfile은 없다. 앱 build context는 루트다.
- `.dockerignore`는 node_modules·.next·venv·Python cache 등을 제외한다.
- AI 소스 변경은 뒤쪽 COPY·chown·test stage를 무효화하지만 requirements layer까지 항상 무효화하지는 않는다.

### 후속 후보

| 항목 | 판단 기준 |
| --- | --- |
| PyTorch·XGBoost CPU 배포판 | 실제 설치 용량을 확인하고 모델 결과 호환성을 검증한 뒤 검토 |
| Python 버전 고정 | 기존 VM 설치 목록과 비교해 dependency 재현성을 확보 |
| pytest 분리 | production 불필요 dependency이나 GB급 주원인과 구분 |
| test image·cache 보존량 | shared/unique/reclaimable 수치와 GC 확인 후 결정 |
| build context 제외 | 모델 cache·runs·다른 위치의 weight가 포괄 제외되어 있지 않음 |
| 중첩 환경파일 | `**/.env*` 규칙이 없으므로 서비스 하위 secret까지 제외된다고 가정하지 않음 |
| pnpm 버전 | lockfile은 있으나 packageManager 버전 고정은 없음 |
| 모델 로딩 | YOLO·XGBoost 객체를 분석 호출마다 생성. 성능 개선은 별도 검토 |

`.gitignore`는 Docker build context 제외 규칙을 대신하지 않는다. 현재 기본 위치에 서비스별 실제 환경파일은 없지만 이후 추가 시 `.dockerignore` 범위를 확인한다. [Docker build context](https://docs.docker.com/build/concepts/context/)

### 과설계·유지보수성 검수

| 검수 질문 | 이번 판단 |
| --- | --- |
| 1. Mac 이전에 필요한가? | 확인된 실행 오류·파일·환경 연결만 필수 범위 |
| 2. 기존 파일로 해결 가능한가? | Dockerfile·Compose·기존 import 보완 범위, 새 계층 불필요 |
| 3. 서비스 로직 변경이 포함되는가? | 분석 알고리즘·API·callback 계약 변경 불필요 |
| 4. Runtime 업그레이드를 섞는가? | Python·Node 업그레이드 보류 |
| 5. 과도한 CI/CD·rollback인가? | 새 pipeline·registry·rollback 설계 보류 |
| 6. 테스트를 위한 테스트인가? | 시작 실패와 실제 추론 검출이 우선, 새 test framework 불필요 |
| 7. build/lint/test 중복인가? | AI Validate·Deploy의 반복 build 호출과 layer 재사용을 구분 |
| 8. 최적화가 AI 계약을 바꾸는가? | OpenCV 교체·export·양자화는 별도 결과 비교 필요 |
| 9. 런타임 모델 다운로드가 필요한가? | 불필요. 현재 외부 weight mount 유지 가능 |
| 10. amd64를 깨뜨릴 수 있는가? | 공용 설정에 ARM 전용 wheel·platform 강제 금지, 양쪽 호환 검토 |

### 시간·공간 비용

| 항목 | 확인 수준 |
| --- | --- |
| 기존 AI image·전체 image·cache 크기 | 사용자 제공값. 원인별 분해·공유분 제외는 실측 필요 |
| 기존 컨테이너 RAM | 사용자 제공값. 추론 peak인지 미확인 |
| 기존·Mac build 시간 | 실측 필요 |
| Mac AI image 크기 | 실측 필요. ARM에서도 CUDA package가 설치될 수 있어 축소 보장 불가 |
| 모델 로드·추론 시간 | 실측 필요 |
| build·추론 peak RAM | 실측 필요 |
| multi-arch 비용 | 플랫폼별 binary layer·빌드 작업 증가. 정확한 시간·공간은 실측 필요 |

AI health는 모델을 로드하지 않으므로 약 60MB RAM 관측만으로 실제 추론 메모리를 판단하지 않는다.

## 12. 제거 가능한 기존 VM/Jenkins 종속 요소

Mac 첫 기능 재현에서 사용하지 않아도 되는 요소이며 실제 삭제는 하지 않았다.

- Jenkins 컨테이너·home volume·bootstrap clone.
- `/home/yp/apps/smart-drain` workspace와 동일 절대경로 mount.
- Jenkins Docker socket 공유 및 Secret File 복사 단계.
- ai-test image의 상시 보존.
- 기존 VM image·build cache의 Mac 복사.
- 기존 PostgreSQL 데이터를 반드시 이전하는 절차.

모델 weight, schema 생성, 사용 중인 샘플·추가 시나리오 이미지, 환경변수, 분석·callback·WebSocket 검증은 유지해야 한다. Jenkins를 실행하지 않는 데 저장소의 Jenkins 파일 삭제는 필요하지 않다.

## 13. 실제 실행 전에 추가 확인해야 할 항목

1. 기존 VM 배포 commit과 분석 기준 HEAD 차이.
2. 기존 AI의 pip freeze, 특히 torch·torchvision·ultralytics·xgboost.
3. best.pt SHA256·크기·모델 호환성·읽기 권한.
4. Mac 환경값의 모델·DB·nginx·Frontend 정합성.
5. 기본 Compose와 Jenkins 개발 nginx 중 재현 대상.
6. ARM build·native import·실제 CPU 추론.
7. 새 DB migration·seed.
8. nginx 경유 이미지·REST·WebSocket·AI callback.
9. build·추론 RAM·시간·동시 요청 동작.

### 분석에서 실행한 검증

| 검증 | 결과·한계 |
| --- | --- |
| Git 상태·HEAD·remote | 분석 시작·종료에 변경 없음 |
| 파일·설정·script 읽기 | 현재 HEAD의 구조 확인, 실제 VM 상태는 아님 |
| Backend·AI Python AST parse | 구문 오류 없음. import·NameError·dependency 실행 검증 아님 |
| 기본 Compose `config --quiet` | `/dev/null` env-file로 성공. 실제 비밀값 검증 아님 |
| 개발 override 병합 `config --quiet` | 동일 조건 성공 |
| OrbStack 서버 정보 | aarch64·리소스 읽기 확인 |

분석 시 사용한 Compose 검사:

```bash
docker compose --env-file /dev/null -f docker-compose.yml config --quiet
docker compose --env-file /dev/null \
  -f docker-compose.yml -f docker-compose.dev.yml config --quiet
```

Compose 문법 성공은 Docker COPY·앱 시작·모델 추론 성공을 검증하지 않는다. 발견한 결함은 분석 기준 HEAD에 존재하던 문제다. build·up·migration·실제 추론·기존 VM 검사는 사용자 요청 범위에 따라 실행하지 않았다.

### 분류 요약

| 분류 | 대상 | 이유 |
| --- | --- | --- |
| 유지 | 서비스 분리·nginx same-origin·PostgreSQL 16·Alembic·모델 mount | 기능 재현의 기반 |
| 이전 필수 수정 | Backend COPY·실행 경로·router import | build·앱 시작 차단 |
| 이전 필수 수정 | Backend·AI 샘플 공급·Mac 경로·DB·port 입력 | 기능·접속 구조 재현 |
| 후속 최적화 | CPU dependency·버전 고정·pytest 분리·cache 관리 | 용량·재현성 개선이며 이전 판정과 구분 |
| 제거 후보 | Jenkins 실행 환경·VM 절대경로·test image 상시 보존 | 수동 Compose 실행 필수 요소 아님 |
| 실검증 필요 | ARM build·모델·DB·callback·WebSocket·peak RAM | 정적 분석으로 성공 보장 불가 |
| ARM blocker 가능성 | best.pt custom 연산·torch/torchvision/native 조합 | ARM 실추론 미실행 |
| ARM blocker 가능성 | 모델에 NVIDIA 필수 custom 연산이 있을 경우 | 저장소에서 발견되지 않았으나 weight 내부 미확인 |

### 최종 질문에 대한 답변

**1. 현재 코드 그대로 전체 `docker compose build/up`을 먼저 시도해도 되는가?**

전체 스택 재현 시도로는 권하지 않는다. Backend의 확정적인 build·시작 오류를 ARM 실패로 오판할 수 있다. AI만 분리한 ARM 검증은 모델·샘플을 준비한 후 가능하다.

**2. 실행 전에 반드시 수정해야 하는 최소 항목은 무엇인가?**

Backend Dockerfile의 Alembic·앱·샘플 경로, main.py의 realtime_simulator import, 운영 AI 샘플 공급, Mac 모델·DB·nginx 입력값이다. 서비스 책임 이동·모델 변경·runtime 업그레이드·새 CI/CD는 필요하지 않다.

**3. AI service가 Apple Silicon 이전의 blocker가 될 가능성이 있는가?**

남아 있지만 필수 CUDA blocker는 현재 확인되지 않았다. 실제 best.pt와 새 dependency 조합의 Linux/arm64 CPU 추론으로 판단해야 한다.

**4. 실제 blocker 여부를 확인하기 위한 최소 검증 명령은 무엇인가?**

다음은 사용자 검토 후 실행할 미실행 명령이다. image·build cache·임시 컨테이너를 생성하지만 `--no-deps`로 DB·migration은 실행하지 않는다. 프로젝트 루트에서 실행하고, 루트 `.env`의 `SMARTDRAIN_YOLO_MODEL_PATH`가 신뢰할 수 있는 실제 Mac 모델 파일을 가리켜야 한다. 실제 `.env` 전체를 출력하는 `docker compose config` 대신 `--quiet`를 사용한다.

```bash
docker compose config --quiet

DOCKER_DEFAULT_PLATFORM=linux/arm64 \
  docker compose build ai-service
```

현재 기본 Compose의 샘플 누락은 진단 명령의 일회성 read-only mount로 보완한다. 예외를 unknown으로 변환하는 앱 wrapper를 거치지 않는 직접 YOLO CPU 추론도 함께 검사한다.

```bash
DOCKER_DEFAULT_PLATFORM=linux/arm64 \
docker compose run --rm --no-deps -T \
  --volume "$PWD/mock_data/ai_image_samples:/app/mock_data/ai_image_samples:ro" \
  ai-service python - <<'PY'
import platform
import cv2
import numpy
import torch
import torchvision
import xgboost

from ai_service.yolo.analyzer import YoloV3ImageAnalyzer
from ai_service.xgboost.model_predictor import TrainedXGBoostPredictor

assert platform.machine() == "aarch64", platform.machine()
print("architecture:", platform.machine())
print("torch:", torch.__version__)
print("torchvision:", torchvision.__version__)
print("opencv:", cv2.__version__)
print("xgboost:", xgboost.__version__)
print("cuda available:", torch.cuda.is_available())

analyzer = YoloV3ImageAnalyzer()
_, processed = analyzer.preprocess_image(
    "/app/mock_data/ai_image_samples/drain_2.jpg"
)
assert processed is not None, "sample image decode failed"
results = analyzer.model.predict(processed, device="cpu", verbose=False)
assert len(results) == 1
print("YOLO CPU inference: OK")

predictor = TrainedXGBoostPredictor()
# 연산 가능성 확인용 입력. 기존 VM 결과 동등성 검증용 기준값은 아니다.
features = [[0.2, 0.9, 0.3, 0.8]]
print("XGBoost prediction:", predictor.model.predict(features).tolist())
print("XGBoost probabilities:",
      predictor.model.predict_proba(features).tolist())
PY
```

이어서 기존 분석 경로의 전처리·feature 변환·결과 조합을 검사한다. 이 script는 Backend callback을 보내지 않는다.

```bash
DOCKER_DEFAULT_PLATFORM=linux/arm64 \
docker compose run --rm --no-deps \
  --volume "$PWD/mock_data/ai_image_samples:/app/mock_data/ai_image_samples:ro" \
  ai-service \
  python -m ai_service.scripts.smoke_analysis --drain-id 2
```

통과하면 AI의 ARM CPU 실행 가능성을 확인할 수 있다. 기존 VM과 결과가 같은지는 동일 모델·샘플의 비교가 필요하며, 전체 기능은 DB·callback·WebSocket까지 별도로 확인해야 한다. 구현 계획은 이 분석의 사용자 검토 후 별도로 작성한다.
