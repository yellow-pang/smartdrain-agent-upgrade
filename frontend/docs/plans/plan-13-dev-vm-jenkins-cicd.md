# 13 개발 VM 공용 Jenkins 기반 SmartDrain CI/CD 구성 계획

## 1. 작업 개요

| 항목           | 내용                                                                                                                                            |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 현재 브랜치    | `infra/dev-vm-jenkins-cicd`                                                                                                                     |
| 작업 규모      | 큰 작업 — Jenkins 컨테이너 설정, VM 배포 경로, Docker Compose 실행 및 Cloudflare 개발 도메인 연결이 포함된다.                                   |
| 최종 목표      | 기존 `health-center-jenkins`를 공용 CI 서버로 사용해 SmartDrain 개발 브랜치를 검증하고, VM의 `/apps/smart-drain`에 안전하게 재배포한다.         |
| 이번 계획 범위 | VM 디렉터리·권한·포트·도메인 분리, Jenkins pipeline, 환경변수/secret, 배포·롤백·검증 절차를 문서화하고 필요한 설정 파일의 작업 범위를 확정한다. |
| 비목표         | Jenkins 신규 설치/재생성, 운영 AWS 배포, RDS/ECS 전환, Kubernetes, 실제 운영 비밀값의 저장 또는 문서화                                          |

## 2. 현재 VM 확인 사항

VM에는 `/apps` 아래 여러 프로젝트가 있고, 기존 컨테이너는 VM 재시작 후에도 자동 기동하도록 구성되어 있다. Jenkins는 SmartDrain 전용이 아니라 `health-center` 프로젝트에서 실행 중인 공용 Jenkins 컨테이너다.

| 구분                 | 현재 확인된 값                                                            | SmartDrain 적용 원칙                                                                              |
| -------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Jenkins              | `health-center-jenkins`, host `8081 → container 8080`, agent `50000` 공개 | 기존 Jenkins를 재사용하고 SmartDrain 전용 Job/credential/folder만 추가한다.                       |
| 기존 웹 서비스       | `3000`, `3001`, `8080`, `8090`, `9090`, `3100` 등이 host에 이미 공개됨    | SmartDrain은 기존 host port를 사용하지 않는다.                                                    |
| 기존 DB              | host `5432`가 사용 중                                                     | SmartDrain PostgreSQL은 Compose 내부 네트워크에서만 사용하고 host port를 publish하지 않는다.      |
| SmartDrain 배포 경로 | `/apps/smart-drain` 예정                                                  | Git working tree, VM 전용 `.env`, Compose project를 이 경로와 `smartdrain-dev` 이름으로 분리한다. |
| 도메인               | 기존 프로젝트와 동일한 상위 도메인, Cloudflare 서브도메인 예정            | SmartDrain 전용 개발 서브도메인만 추가하고 다른 프로젝트의 origin/routing은 수정하지 않는다.      |

현재 포트 사용 현황상 SmartDrain Nginx에는 **host `8091`**을 우선 후보로 둔다. 외부에서 직접 접속할 필요가 없다면 `127.0.0.1:8091:80`만 bind하고, Cloudflare Tunnel 또는 VM의 공용 reverse proxy가 이 주소로 전달하도록 구성한다.

## 3. 목표 구조

```text
GitHub develop push
       │ webhook / Jenkins polling
       ▼
health-center-jenkins (기존 공용 Jenkins)
       │ Git credential, Docker CLI/socket, /apps/smart-drain mount
       ├─ 정적 검사 · 테스트 · Compose config 검증
       └─ /apps/smart-drain 기준 Docker Compose 재배포
                         │
                         ▼
              smartdrain-dev Compose project
       ┌──────────┬──────────┬────────────┬──────────┬─────────┐
       │ frontend │ backend  │ ai-service │ db       │ nginx   │
       └──────────┴──────────┴────────────┴──────────┴─────────┘
                                                  │ host 127.0.0.1:8091
Cloudflare 개발 서브도메인 ─ Cloudflare Tunnel 또는 공용 reverse proxy ─┘
```

Jenkins 자체의 Docker Compose 프로젝트와 SmartDrain Compose 프로젝트는 이름·volume·network가 달라야 한다. SmartDrain pipeline은 `docker compose -p smartdrain-dev`를 일관되게 사용한다.

## 4. 설계 결정

### 4.1 VM 파일과 권한 경계

| 위치                              | 책임                                                         | Git 추적            | 접근 원칙                                                                                   |
| --------------------------------- | ------------------------------------------------------------ | ------------------- | ------------------------------------------------------------------------------------------- |
| `/apps/smart-drain`               | SmartDrain 배포용 Git working tree 및 Compose 실행 기준 경로 | 소스만 추적         | Jenkins와 VM 관리자가 쓰기 가능해야 한다.                                                   |
| `/apps/smart-drain/.env`          | 개발 VM 전용 DB 비밀번호, 도메인, Compose 값                 | 제외                | Jenkins credential 또는 VM 관리자가 생성하며 콘솔에 출력하지 않는다.                        |
| `health-center` Jenkins 설정 경로 | 기존 Jenkins 컨테이너/volume 정의                            | 기존 프로젝트 기준  | SmartDrain 배포에 필요한 mount·Docker 권한만 최소 변경하고 기존 Job에는 영향을 주지 않는다. |
| Jenkins workspace                 | Jenkins가 checkout·검증에 사용하는 임시 작업 공간            | Jenkins volume 내부 | 배포 기준 경로로 사용하지 않고, 검증 산출물만 만든다.                                       |

Jenkins 컨테이너에는 `/apps/smart-drain`을 예를 들어 `/deploy/smart-drain`으로 bind mount한다. pipeline은 이 mount 경로에서만 배포 명령을 실행한다. Jenkins workspace와 배포 디렉터리를 분리하면 Jenkins의 임시 정리 작업이 실제 실행 중인 배포 소스를 지우는 일을 방지할 수 있다.

### 4.2 Jenkins 실행 권한

기존 Jenkins 이미지가 Docker CLI를 포함하는지, 그리고 Docker socket을 mount하여 host Docker daemon을 사용할 수 있는지 먼저 확인한다. SmartDrain은 별도 Docker daemon을 만들지 않고 VM의 기존 Docker daemon을 사용한다.

필수 확인 항목:

- Jenkins 컨테이너에 `docker`, `docker compose`, `git` 명령이 존재하는지
- `/var/run/docker.sock`이 Jenkins 컨테이너에 mount되어 있고 Jenkins 실행 사용자가 접근 가능한지
- `/apps/smart-drain`이 Jenkins 컨테이너에 read/write mount되는지
- Jenkins 컨테이너 내부 사용자 UID/GID와 `/apps/smart-drain` 소유권이 충돌하지 않는지

Docker socket 접근은 host Docker 관리자 권한과 동등하므로, SmartDrain Job은 프로젝트 관리 권한이 있는 사용자만 수정할 수 있게 제한한다. Jenkins plugin 또는 임의 pipeline 권한을 넓게 주지 않는다.

### 4.3 포트와 도메인

| 항목                                        | 권장값                                              | 이유                                                                 |
| ------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------- |
| Compose project                             | `smartdrain-dev`                                    | 다른 프로젝트의 container, network, volume 이름과 충돌하지 않는다.   |
| SmartDrain Nginx host port                  | `127.0.0.1:8091:80`                                 | 현재 공개 포트와 충돌하지 않고, origin을 VM 로컬로 제한한다.         |
| SmartDrain DB/backend/AI/frontend 직접 포트 | publish하지 않음                                    | Nginx 외 공격 표면을 만들지 않는다.                                  |
| Cloudflare hostname                         | `dev.<팀-도메인>` 또는 `smartdrain-dev.<팀-도메인>` | 서비스의 목적이 바로 드러나며 기존 프로젝트와 DNS record를 분리한다. |
| HTTPS/WebSocket                             | Cloudflare HTTPS + Nginx `/ws/` proxy               | 같은 origin REST/WebSocket 흐름을 유지한다.                          |

Cloudflare는 DNS만 사용하는 방식보다 **Cloudflare Tunnel**을 우선 검토한다. Tunnel을 사용하면 VM 공인 IP, 80/443 포트포워딩을 새로 열지 않고 hostname을 로컬 origin으로 연결할 수 있다. 기존 Cloudflare 연결 방식이 이미 있다면 그 방식을 우선 재사용하되 SmartDrain 전용 public hostname과 origin route만 추가한다.

### 4.4 환경변수와 Secret

VM의 `/apps/smart-drain/.env`는 `.env.example`을 기반으로 만들되 실제 값은 Git, Docker build context, Jenkins console log에 남기지 않는다.

```dotenv
COMPOSE_PROJECT_NAME=smartdrain-dev
NGINX_HTTP_PORT=127.0.0.1:8091

# 실제 값은 개발 VM에서만 설정한다.
POSTGRES_PASSWORD=<개발-VM-전용-랜덤-비밀번호>
COMPOSE_DATABASE_URL=postgresql+psycopg://smartdrain:<개발-VM-전용-랜덤-비밀번호>@db:5432/smartdrain_db
COMPOSE_CORS_ORIGINS=["https://<SmartDrain-개발-서브도메인>"]
COMPOSE_FRONTEND_API_BASE_URL=
```

`COMPOSE_FRONTEND_API_BASE_URL`은 빈 값으로 유지한다. 현재 frontend는 Nginx same-origin에서 `/api/*`와 `/ws/*`를 사용하도록 구성되어 있으므로, `/api`를 중복 설정하면 `/api/api/...` 경로가 될 수 있다. `NEXT_PUBLIC_*`에는 DB password, Jenkins/Git token, Cloudflare token을 넣지 않는다.

### 4.5 Jenkins pipeline 초안

| 순서 | 단계                | 통과 기준                                                              | 실패 시 처리                             |
| ---- | ------------------- | ---------------------------------------------------------------------- | ---------------------------------------- |
| 1    | Trigger/checkout    | 지정 브랜치의 commit SHA를 확보                                        | 기존 배포는 유지하고 Job 실패            |
| 2    | VM 배포 경로 동기화 | `/deploy/smart-drain`이 목표 commit 상태                               | `.env`를 덮어쓰지 않고 중단              |
| 3    | 사전 검증           | `.env` 존재, `docker compose config --quiet` 통과                      | secret 내용 없이 오류만 출력             |
| 4    | 코드 검증           | frontend lint/build, `python -m pytest ai_service` 통과                | 배포 전 중단                             |
| 5    | 배포                | `docker compose -p smartdrain-dev up -d --build --remove-orphans` 성공 | compose logs를 제한적으로 수집           |
| 6    | readiness           | migrate 성공, 장기 서비스 healthy/running                              | 이전 revision 롤백 절차 실행 여부를 판단 |
| 7    | smoke test          | `/`, `/api/dashboard/summary`, `/ws/drains/status` 확인                | Job 실패 및 배포 상태 기록               |

동시 배포는 금지한다. pipeline에는 `disableConcurrentBuilds()`를 적용하고, 배포 명령은 반드시 `-p smartdrain-dev`와 명시적인 작업 디렉터리를 사용한다. Jenkins가 실행 중인 다른 프로젝트에 `docker compose down`, `docker system prune`, 이름 없는 `docker stop` 같은 전역 명령을 실행해서는 안 된다.

초기 구현은 VM에서 source를 checkout하고 Docker image를 build하는 방식으로 시작한다. 이후 AWS 또는 registry를 도입할 때에는 검증된 commit SHA image를 publish하고 동일 tag를 배포·롤백 기준으로 전환한다.

### 4.6 배포와 롤백 원칙

- `docker compose down -v`는 PostgreSQL volume을 삭제하므로 pipeline에서 사용하지 않는다.
- 배포 전 현재 정상 동작 중인 Git commit SHA와 image ID를 기록한다.
- 새 revision의 smoke test가 실패하면 이전 정상 commit으로 checkout한 뒤 `docker compose -p smartdrain-dev up -d --build`로 복구하는 절차를 별도 스크립트로 명시한다.
- 자동 롤백은 migration이 되돌릴 수 있는지 확인하기 전에는 수행하지 않는다. migration이 포함된 배포는 실패 시 infra 담당자가 DB 영향과 로그를 확인한 뒤 수동 롤백한다.

## 5. 사용자 확인이 필요한 사항

아래 항목은 실제 Jenkins/Cloudflare 설정을 변경하기 전에 확정한다.

| 확인 항목                 | 권장안                                                                                             | 확인이 필요한 이유                                                   |
| ------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 배포 대상 브랜치          | `develop` push 시 개발 VM 자동 배포                                                                | feature 브랜치마다 VM 배포가 겹치지 않게 한다.                       |
| SmartDrain 개발 hostname  | `dev.<팀-도메인>` 또는 `smartdrain-dev.<팀-도메인>`                                                | 기존 두 프로젝트의 hostname과 충돌하지 않아야 한다.                  |
| Cloudflare 연결 방식      | 기존 Tunnel이 있으면 동일 Tunnel에 hostname 추가                                                   | DNS only/포트포워딩 여부에 따라 VM Nginx와 firewall 설정이 달라진다. |
| Jenkins Compose 수정 권한 | `health-center`의 Jenkins Compose에 SmartDrain deploy mount와 Docker socket 권한을 추가해도 되는지 | 다른 프로젝트 Jenkins의 재기동·권한에 영향을 줄 수 있다.             |
| Jenkins Git 인증 방식     | Jenkins Credential의 GitHub PAT 또는 Deploy Key                                                    | token의 저장 위치와 repository 권한 범위를 최소화해야 한다.          |
| SmartDrain host port      | `127.0.0.1:8091`                                                                                   | 실제 VM에서 이미 사용 중인지 마지막 확인이 필요하다.                 |
| 초기 DB 정책              | 빈 DB + migration, 필요 시 수동 seed                                                               | 개발 데모에 mock data가 필요한지에 따라 최초 배포 절차가 달라진다.   |
| FastAPI docs 공개         | 개발 hostname에서도 `/docs` 차단 유지 권장                                                         | 외부 개발 도메인에 API schema를 공개할지 결정해야 한다.              |

## 6. 예상 변경 파일

| 경로                                                 | 변경 목적                                 | 변경 전 승인                           |
| ---------------------------------------------------- | ----------------------------------------- | -------------------------------------- |
| `frontend/docs/plans/plan-13-dev-vm-jenkins-cicd.md` | 설계·확인 사항 기록                       | 완료                                   |
| `Jenkinsfile` 또는 `.jenkins/Jenkinsfile`            | SmartDrain CI/CD 선언                     | 필요                                   |
| `.jenkins/scripts/*`                                 | 배포/healthcheck/rollback 보조 스크립트   | 필요                                   |
| `.env.example`                                       | VM용 변수 설명 보강이 필요할 경우         | 필요                                   |
| `frontend/docs/deployment/*`                         | 확정된 VM/Jenkins 운영 가이드             | 필요                                   |
| 기존 `health-center` Jenkins Compose 파일            | `/apps/smart-drain` mount, Docker 권한 등 | **health-center 담당자 승인 필수**     |
| Cloudflare Tunnel/DNS 설정                           | SmartDrain 개발 hostname route            | **도메인/Cloudflare 관리자 승인 필수** |

## 7. 구현 및 검증 순서

1. 사용자 확인 사항을 확정하고, 기존 Jenkins 컨테이너의 mount·Docker socket·사용자 권한을 읽기 전용으로 점검한다.
2. `/apps/smart-drain`에 repository를 배치하고 VM 전용 `.env`를 생성한다. 파일 권한과 Git 제외 상태를 확인한다.
3. VM에서 `docker compose -p smartdrain-dev config --quiet`, build, 기동을 수동 검증한다.
4. SmartDrain 전용 Jenkins Folder/Job/Credential을 만들고 pipeline에 동시 실행 방지와 명시적 project name을 적용한다.
5. Jenkins가 Docker·Git·배포 mount에 접근 가능한지 최소 명령으로 검증한다.
6. Jenkins에서 검증·배포·smoke test를 수행하고, 정상/실패 로그와 실행 commit SHA를 기록한다.
7. Cloudflare 개발 hostname에서 HTTPS, REST API, WebSocket을 확인한다.
8. 실제 결과, 남은 위험, 롤백 절차를 `frontend/docs/steps/step-15-dev-vm-jenkins-cicd.md`에 기록한다.

## 8. 검증 기준

| 검증                                               | 기대 결과                                                                     |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| `docker compose -p smartdrain-dev config --quiet`  | Compose 문법과 VM 환경변수 치환이 유효                                        |
| `docker compose -p smartdrain-dev ps`              | SmartDrain 컨테이너가 다른 프로젝트와 별도 이름·network·volume으로 실행       |
| Jenkins 컨테이너 내부 Docker 확인                  | SmartDrain Compose만 제어 가능하며 기존 프로젝트를 변경하지 않음              |
| Jenkins pipeline                                   | lint, build, AI pytest, Compose build/deploy 성공                             |
| `curl http://127.0.0.1:8091/`                      | frontend HTTP 200                                                             |
| `curl http://127.0.0.1:8091/api/dashboard/summary` | backend API HTTP 200                                                          |
| WebSocket `/ws/drains/status`                      | Nginx Upgrade 후 연결 유지                                                    |
| Cloudflare hostname                                | HTTPS 화면, REST, WebSocket 정상 동작                                         |
| VM 재시작 후                                       | Jenkins와 SmartDrain의 restart 정책에 따라 서비스가 복구되고 healthcheck 통과 |

## 9. 리스크와 대응

| 리스크                                                            | 대응                                                                                                            |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| 공용 Jenkins가 다른 프로젝트 Compose를 잘못 제어                  | 모든 SmartDrain 명령에 `-p smartdrain-dev`와 `/deploy/smart-drain`을 명시하고 전역 Docker 정리 명령을 금지한다. |
| Jenkins 권한/UID 차이로 `/apps/smart-drain` 파일이 root 소유가 됨 | mount 전 UID/GID를 확인하고 Jenkins 실행 사용자와 배포 디렉터리 소유권을 맞춘다.                                |
| host port 충돌                                                    | `8091` 실제 점유 여부를 배포 직전에 확인하고, 필요 시 다른 미사용 loopback port로 확정한다.                     |
| Docker socket 노출                                                | SmartDrain Job 수정 권한과 Jenkins credential 접근을 최소화하고 audit log를 남긴다.                             |
| Cloudflare에서 WebSocket 실패                                     | Tunnel/origin 설정과 Cloudflare proxy 상태를 확인하고 `/ws/` 캐시 규칙을 두지 않는다.                           |
| 실패한 migration 뒤 자동 rollback                                 | DB schema 영향이 있으므로 자동 rollback을 보류하고 migration/DB 로그를 먼저 확인한다.                           |
| `.env` 또는 token이 log/image에 노출                              | `set +x`, Jenkins mask credential, `.dockerignore`, `.gitignore`를 유지하며 secret 값을 echo하지 않는다.        |

## 10. 다음 단계 승인 후 제안 커밋 메시지

```text
docs: 개발 VM 공용 Jenkins 기반 SmartDrain CI/CD 계획 추가
```

```text
- 기존 Jenkins와 SmartDrain 배포 경로의 책임을 분리한다.
- 포트, Compose 프로젝트명, Cloudflare 개발 도메인 설계를 기록한다.
- Jenkins pipeline, 검증, 롤백 및 사용자 확인 항목을 정의한다.
```
