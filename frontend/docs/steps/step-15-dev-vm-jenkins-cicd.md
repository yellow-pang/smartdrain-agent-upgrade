# 15 개발 VM 공용 Jenkins 기반 SmartDrain CI/CD 1차 구성 결과

## 1. 완료 요약

기존 `health-center-jenkins`를 공용 Jenkins로 재사용하기 위한 SmartDrain CI/CD 코드를 추가했다. SmartDrain은 `/apps/smart-drain`에서 별도 Compose project인 `smartdrain-dev`로 실행하며, Nginx origin은 `127.0.0.1:8099:80`을 사용한다.

이번 단계는 SmartDrain 저장소 내부의 pipeline·검증·배포 스크립트와 Docker CI target을 준비한 단계다. 기존 Jenkins 컨테이너 Compose와 Cloudflare Tunnel 설정은 다른 프로젝트/관리 콘솔의 소유 범위이므로 직접 수정하지 않았다.

## 2. 변경 파일과 역할

| 경로 | 변경 내용 |
| --- | --- |
| `/Jenkinsfile` | Jenkins SCM checkout, SSH source 동기화, 검증, Compose 배포, 선택 seed, smoke test와 실패 로그 수집을 선언한다. |
| `/.jenkins/scripts/preflight.sh` | Docker CLI/socket, Git, curl, 배포 mount와 VM `.env` 존재 여부를 확인한다. |
| `/.jenkins/scripts/sync-deployment-source.sh` | SSH private key로 `develop`을 clone/fetch하고 `/deploy/smart-drain`을 목표 revision으로 맞춘다. |
| `/.jenkins/scripts/validate.sh` | Compose config, frontend lint Docker target, AI pytest Docker target을 실행한다. |
| `/.jenkins/scripts/deploy.sh` | `smartdrain-dev` Compose project만 build·재기동한다. |
| `/.jenkins/scripts/seed.sh` | 첫 배포에서만 수동 실행하는 mock data seed 명령을 제공한다. |
| `/.jenkins/scripts/smoke-test.sh` | VM loopback의 frontend와 dashboard API를 확인한다. |
| `/.jenkins/scripts/collect-logs.sh` | 실패 시 nginx/backend/AI 서비스 로그 마지막 100줄을 수집한다. |
| `/frontend/Dockerfile` | `pnpm lint`를 실행하는 `lint` Docker target을 추가한다. |
| `/ai_service/Dockerfile` | production runtime과 분리된 `pytest`용 `test` Docker target을 추가한다. |
| `../plans/plan-13-dev-vm-jenkins-cicd.md` | 이 step 문서를 실제 적용 절차의 기준 문서로 연결한다. |

`.dockerignore`는 기존대로 `Jenkinsfile`과 `.jenkins/`를 application image build context에서 제외한다. pipeline 정의와 배포 스크립트가 runtime application image에 들어가지 않게 하는 의도다.

## 3. Jenkins 동작 흐름

```text
Jenkins Job의 Poll SCM
        ↓ develop 변경 감지
Jenkinsfile SCM checkout
        ↓
preflight: Docker/socket, /deploy/smart-drain, .env 확인
        ↓
SSH Deploy Key로 develop clone 또는 fetch/reset
        ↓
Compose config → frontend lint → AI pytest
        ↓
docker compose -p smartdrain-dev up -d --build --remove-orphans
        ↓
선택: SEED_MOCK_DATA=true일 때만 mock seed
        ↓
127.0.0.1:8099 frontend/API smoke test
```

Jenkinsfile에는 polling 주기를 고정하지 않았다. 기존 `health-center` Jenkinsfile도 polling trigger를 선언하지 않고 Jenkins Job 설정을 사용하는 구조이므로, SmartDrain Job의 **Build Triggers → Poll SCM**에 기존 Job과 같은 주기를 설정한다.

### 3.1 health-center 방식과 비교한 설계 이유

| 구분 | health-center 현재 방식 | SmartDrain 1차 구현 |
| --- | --- | --- |
| 배포 source | Jenkins workspace | VM `/apps/smart-drain` |
| Git 동기화 | `checkout scm` 한 번 | Jenkinsfile checkout 후 SSH clone/fetch/reset |
| `.env` | Jenkins Credential file 복사 | VM 배포 경로의 `.env` 유지 |
| Compose 실행 경로 | Jenkins workspace | `/deploy/smart-drain` mount |
| 장점 | 단순하고 기존에 검증됨 | VM에서 실제 revision과 설정을 직접 점검하기 쉬움 |
| 단점 | VM의 `/apps`에 배포 소스가 남지 않음 | Git 동기화가 두 번이라 설정과 권한 관리가 복잡함 |

SmartDrain 1차 구현이 health-center와 다르게 작성된 이유는 사용자가 `/apps/smart-drain`을 실제 배포 기준 폴더로 정했기 때문이다. Jenkins workspace만 쓰면 기존 방식에는 더 가깝지만, VM 관리자가 `/apps/smart-drain`에서 source, `.env`, Compose 로그와 Git revision을 직접 관리할 수 없다.

Jenkins Compose에 추가하는 `- /apps/smart-drain:/deploy/smart-drain` volume은 기존 `jenkins-home`, Docker socket, Maven/npm cache를 바꾸거나 대체하지 않는다. 단지 VM 배포 폴더를 Jenkins 컨테이너 내부에 보이게 한다.

운영 방식 통일을 우선한다면 다음 단계에서 Custom Workspace를 `/deploy/smart-drain`으로 지정하고 `checkout scm` 하나만 쓰는 혼합 방식으로 단순화할 수 있다. 이 경우 health-center처럼 Jenkins Credential의 secret file에서 `.env`를 checkout 뒤 복사하며, 별도 SSH clone/fetch 스크립트는 제거한다. 상세 비교는 `../deployment/jenkins-deployment-architecture-comparison.md`에 기록했다.

## 4. 개발 VM에서 해야 할 작업

### 4.1 SmartDrain 배포 경로 준비

VM에서 `/apps/smart-drain`을 만들고 Jenkins가 접근 가능하도록 한다. 최초 clone은 Jenkins pipeline이 수행할 수 있으므로 디렉터리는 비어 있어도 된다. 단, pipeline preflight가 VM `.env`를 먼저 요구하므로 예시 파일을 복사해 설정한다.

```bash
sudo mkdir -p /apps/smart-drain
cd /apps/smart-drain
sudo cp <SmartDrain-저장소-복사본>/.env.example .env
sudo chmod 600 .env
```

VM의 `.env`에는 다음 값을 사용한다. `<개발-VM-랜덤-비밀번호>`는 실제 랜덤 값으로 바꾸며 Git, Jenkins console, 스크린샷에 남기지 않는다.

```dotenv
COMPOSE_PROJECT_NAME=smartdrain-dev
NGINX_HTTP_PORT=127.0.0.1:8099
POSTGRES_USER=smartdrain
POSTGRES_PASSWORD=<개발-VM-랜덤-비밀번호>
POSTGRES_DB=smartdrain_db
COMPOSE_DATABASE_URL=postgresql+psycopg://smartdrain:<개발-VM-랜덤-비밀번호>@db:5432/smartdrain_db
COMPOSE_CORS_ORIGINS=["https://smartdrain-health.store"]
COMPOSE_FRONTEND_API_BASE_URL=
COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY=
```

`COMPOSE_FRONTEND_API_BASE_URL`은 빈 값으로 둔다. Nginx same-origin 환경에서 frontend API helper가 가진 `/api/*` 경로를 그대로 사용하기 때문이다.

### 4.2 기존 health-center Jenkins Compose 수정

기존 Jenkins 설정 파일은 다음 위치다.

```text
C:\Dev\health-center-smart-reservation\infra\jenkins\docker-compose.jenkins.yml
```

`jenkins` 서비스의 `volumes`에 아래 한 줄을 추가한다. `/var/run/docker.sock` mount는 이미 있으므로 유지한다.

```yaml
      - /apps/smart-drain:/deploy/smart-drain
```

Jenkins 컨테이너는 현재 Compose에서 `user: root`로 실행된다. Docker socket을 사용하기 위한 기존 설정이며, 이 상태에서 pipeline이 `/apps/smart-drain`에 생성하는 Git working tree 파일도 host에서는 root 소유가 될 수 있다. VM 관리자가 해당 경로를 관리하거나, 필요하면 배포 후 적절한 사용자에게 소유권을 넘긴다. Jenkins 실행 사용자를 임의로 바꾸면 Docker socket 권한이 깨질 수 있으므로 이번 단계에서는 변경하지 않는다.

Compose 파일을 바꾼 뒤 해당 디렉터리에서 Jenkins만 재생성한다. named volume `jenkins-home`은 유지되므로 Jenkins 설정과 Job은 보존된다. 실행 중인 Jenkins Job이 없는 시간에 수행한다.

```bash
cd /path/to/health-center-smart-reservation/infra/jenkins
docker compose -f docker-compose.jenkins.yml up -d --build
```

### 4.3 기존 Jenkins 이미지에 필요한 패키지

기존 Jenkins Dockerfile 위치는 다음과 같다.

```text
C:\Dev\health-center-smart-reservation\infra\jenkins\Dockerfile
```

현재 Dockerfile은 Docker CLI, Compose plugin, Node, Maven을 설치하지만 SmartDrain의 SSH Git 동기화에 필요한 `openssh-client`를 명시적으로 설치하지 않는다. `apt-get install` 목록에 `git openssh-client`를 추가한다.

```dockerfile
RUN apt-get update \
    && apt-get install -y ca-certificates curl gnupg maven git openssh-client \
    # 이하 기존 Docker/Node 설치 명령 유지
```

`git`은 Jenkins base image에 포함되어 있을 수 있지만, SmartDrain pipeline은 `git fetch`와 `ssh` 명령을 직접 실행하므로 두 도구를 image에 명시해 환경 차이를 없애는 것이 안전하다. 수정 후에는 4.2의 Compose 재생성 명령으로 image를 다시 build한다.

### 4.4 GitHub SSH Deploy Key와 Jenkins Credential 등록

1. GitHub SmartDrain repository의 **Settings → Deploy keys**에서 새 키를 추가한다. 배포는 clone/fetch만 하므로 `Allow write access`는 켜지 않는다.
2. Jenkins **Manage Jenkins → Credentials**에서 `SSH Username with private key` credential을 만든다.
3. Credential ID는 반드시 `smartdrain-github-deploy-key`로 지정한다. Jenkinsfile이 이 이름을 사용한다.
4. Username은 `git`, private key에는 Deploy Key의 개인 키를 등록한다.
5. Jenkins Job의 Pipeline SCM 설정도 동일한 SSH repository URL과 credential을 사용한다.

Deploy Key는 저장소 하나에만 읽기 권한을 주므로, 개인 계정 PAT나 개인 SSH key를 Jenkins에 저장하는 것보다 적합하다.

### 4.5 SmartDrain Jenkins Job 생성

Jenkins에서 Pipeline Job을 새로 만들고 다음을 설정한다.

| 항목 | 값 |
| --- | --- |
| Job 이름 | `smartdrain-develop-deploy` |
| Definition | Pipeline script from SCM |
| SCM | Git |
| Repository URL | `git@github.com:<owner>/<smartdrain-repository>.git` |
| Credentials | `smartdrain-github-deploy-key` |
| Branch Specifier | `*/develop` |
| Script Path | `Jenkinsfile` |
| Build Triggers | 기존 health-center Job과 동일한 주기로 `Poll SCM` 선택 |

첫 실행만 `GIT_REPOSITORY_SSH_URL` parameter에 위 SSH repository URL을 입력한다. `/apps/smart-drain/.git`이 생성된 뒤의 polling 배포에서는 빈 값으로 둔다.

`SEED_MOCK_DATA`는 기본값 `false`다. 첫 배포가 정상적으로 끝난 후 필요한 경우에만 `true`로 한 번 실행한다.

### 4.6 최초 배포와 seed 확인

첫 Job 실행 전에는 Jenkins mount 안에서 `.env`가 보이는지 확인한다. 이후 Job을 실행하고 frontend/API smoke test가 성공한 뒤 seed를 별도로 실행한다.

```bash
# VM에서 확인하는 경우
curl --fail http://127.0.0.1:8099/
curl --fail http://127.0.0.1:8099/api/dashboard/summary
```

seed는 `DR-001`~`DR-005`의 `drain_code`가 없을 때만 데이터를 추가한다. 동일 seed를 재실행하면 기존 행을 덮어쓰지 않고 건너뛴다. 일반 polling 배포에서는 실행되지 않는다.

데이터 전체 초기화가 필요한 특별한 경우에만 infra 담당자가 아래 명령을 수동 실행한다. Jenkinsfile에는 이 명령이 포함되어 있지 않다.

```bash
cd /apps/smart-drain
docker compose -p smartdrain-dev down -v
```

## 5. Cloudflare 적용 순서

1. 기존 Cloudflare Tunnel 또는 새 Tunnel에 public hostname `smartdrain-health.store`를 추가한다.
2. service 주소를 `http://127.0.0.1:8099`로 설정한다.
3. Access Application은 초기에는 만들지 않아 공개 상태로 둔다.
4. 팀원 합류 시 Zero Trust → Access → Applications에서 self-hosted application을 만들고, `smartdrain-health.store`에 이메일 또는 이메일 도메인 allow policy를 적용한다.
5. Access 적용 후 대시보드, `/api/dashboard/summary`, WebSocket `/ws/drains/status`를 다시 확인한다.

Cloudflare Tunnel은 VM 80/443 포트를 공개하지 않아도 되며, SmartDrain Docker Nginx는 loopback `8099`에서만 수신한다.

## 6. 검증 결과와 남은 리스크

| 항목 | 결과 |
| --- | --- |
| `git diff --check` | 통과 |
| Shell script 구문 검사 | 현재 Windows 작업 환경에 `sh`가 없어 실행하지 못했다. Jenkins는 Linux container에서 실행한다. |
| frontend lint Docker target | 로컬 Docker Desktop daemon이 실행 중이 아니어서 미검증 |
| AI pytest Docker target | 로컬 Docker Desktop daemon이 실행 중이 아니어서 미검증 |
| VM Jenkins/Cloudflare 적용 | 외부 VM 및 Cloudflare 관리 범위이므로 미실행 |

Docker Desktop daemon이 꺼진 상태에서 Docker API named pipe를 찾을 수 없어 build 검증은 실행되지 않았다. VM Jenkins 적용 후 첫 Job에서 lint와 pytest target을 반드시 확인한다.

## 7. 다음 작업

1. health-center Jenkins Compose에 SmartDrain deployment mount를 추가한다.
2. Jenkins를 재생성하고 SmartDrain deployment mount를 확인한다.
3. GitHub Deploy Key, Jenkins SCM Credential, `.env` Secret File Credential과 Job을 만든다.
4. Secret File Credential을 사용한 첫 배포와 선택 seed를 실행한다.
5. Cloudflare Tunnel hostname을 연결하고, 팀 합류 뒤 Zero Trust 이메일 제한을 추가한다.

## 8. 제안 커밋 메시지

```text
feat: 개발 VM Jenkins 기반 SmartDrain CI/CD 구성 추가
```

```text
- Custom Workspace와 Jenkins SCM checkout 기반 배포 파이프라인을 추가한다.
- Jenkins Secret File로 배포 환경변수를 checkout 직후 주입한다.
- Docker lint와 AI pytest 전용 CI target을 분리한다.
- VM, Jenkins, seed, Cloudflare Tunnel 적용 절차를 문서화한다.
```

## 9. 설계 변경: Custom Workspace 혼합 방식 적용

기존 1차 구현은 `/apps/smart-drain`을 실제 배포 source로 유지하기 위해 `checkout scm` 후 별도 SSH clone/fetch 스크립트를 실행했다. health-center 방식과 비교한 결과, Git 동기화가 두 번 발생하고 Deploy Key·최초 clone parameter·VM `.env` 관리가 추가되어 운영 복잡도가 높았다.

사용자 결정에 따라 Jenkinsfile을 아래 방식으로 변경했다.

```text
Jenkins Job SCM checkout
        ↓
Custom Workspace /deploy/smart-drain
        ↓
Jenkins Secret File credential을 .env로 복사
        ↓
Compose 검증 · build · 배포 · smoke test
```

| 항목 | 이전 1차 구현 | 현재 적용 방식 |
| --- | --- | --- |
| Jenkins agent workspace | 기본 Jenkins workspace | `/deploy/smart-drain` Custom Workspace |
| Git 동기화 | `checkout scm` + SSH clone/fetch | `checkout scm` 한 번 |
| `.env` | VM에 사전 생성·보존 | Secret File을 checkout 직후 매 배포 복사 |
| Git SSH credential | SCM credential + script용 별도 credential | Jenkins Job SCM credential 하나 |
| 제거된 입력 | `GIT_REPOSITORY_SSH_URL` 최초 clone parameter | 제거 |

`/deploy/smart-drain`은 Jenkins 컨테이너 내부 경로이고, host `/apps/smart-drain`을 mount해 사용한다. 따라서 기존 health-center의 checkout·Credential 기반 환경변수 관리 방식은 유지하면서 SmartDrain source를 VM `/apps/smart-drain`에서 직접 점검할 수 있다.

### 9.1 최종 VM/Jenkins 적용 사항

1. host `/apps/smart-drain`은 최초 Jenkins checkout 전 비어 있어야 한다. `.env`를 사전에 만들지 않는다.
2. `C:\Dev\health-center-smart-reservation\infra\jenkins\docker-compose.jenkins.yml`의 Jenkins volume에 다음 한 줄을 추가한다.

   ```yaml
   - /apps/smart-drain:/deploy/smart-drain
   ```

3. Jenkins Credential에 SmartDrain repository용 SSH credential과 아래 Secret File을 등록한다.

   ```text
   Credential ID: smartdrain-dev-env-file
   파일 내용: SmartDrain 개발 VM용 .env
   ```

4. SmartDrain Job은 `Pipeline script from SCM`, `*/develop`, `Jenkinsfile`로 만들고 기존 Job과 같은 Poll SCM 주기를 설정한다.

이번 방식에서는 Jenkins가 직접 `git fetch` 또는 `ssh` 명령을 실행하지 않는다. 따라서 기존 health-center Jenkins Dockerfile에 `git`이나 `openssh-client`를 추가할 필요가 없다. 외부 프로젝트에서 필요한 변경은 Jenkins Compose의 deployment mount 한 줄뿐이다.

Notion용 최종 정리 문서는 `../deployment/jenkins-custom-workspace-guide.md`에 기록했다.

## 10. 설계 변경: SmartDrain 전용 Jenkins 분리

health 프로젝트는 개인 저장소이고 SmartDrain은 팀 프로젝트이므로, Jenkins Job·Credential·plugin·log 관리 범위를 분리하기 위해 SmartDrain 전용 Jenkins 컨테이너를 추가했다. VM 자원이 충분하고 동일 인프라 담당자가 관리하는 조건에서는 공용 Jenkins의 접근 권한을 세밀하게 나누는 것보다 전용 Jenkins가 인수인계와 운영 경계를 더 명확하게 만든다.

| 항목 | health Jenkins | SmartDrain Jenkins |
| --- | --- | --- |
| container | `health-center-jenkins` | `smartdrain-jenkins` |
| UI host port | `8081` | `8082` |
| agent host port | `50000` | `50001` |
| Jenkins home | 기존 `jenkins-home` | `smartdrain-jenkins-home` |
| 저장소/팀 Credential | health 프로젝트 전용 | SmartDrain 팀 전용 |
| 배포 source | health Jenkins workspace | `/apps/smart-drain` Custom Workspace |

전용 Jenkins의 Compose와 Dockerfile은 SmartDrain 저장소의 `/jenkins/`에 추가했다. 현재 Jenkinsfile의 Custom Workspace, Secret File `.env`, Compose project `smartdrain-dev` 설정은 전용 Jenkins에서도 그대로 사용한다.

두 Jenkins는 같은 VM Docker socket을 사용한다. 따라서 Jenkins 설정과 Credential은 분리되지만, Docker daemon 권한은 공유한다. Docker 권한까지 완전히 분리하려면 별도 VM 또는 별도 Docker daemon/agent가 필요하다.

### 10.1 health Jenkins 변경 복구

전용 Jenkins 방식에서는 health-center 프로젝트에 SmartDrain mount나 SSH 패키지 추가가 필요 없다. 이전 방향으로 이미 health Jenkins Compose/Dockerfile을 수정했다면 SmartDrain을 위해 추가한 부분만 제거하고 health Jenkins를 재생성한다. `down -v`는 실행하지 않아야 기존 Jenkins home volume과 health Job/Credential이 보존된다.
