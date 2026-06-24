# 20 개발 서버 Jenkins Host 경로 정렬 계획

## 1. 작업 개요

| 항목 | 내용 |
| --- | --- |
| 권장 브랜치 | `chore/dev-server-infra-path-alignment` |
| 작업 규모 | 큰 작업 — Jenkins pipeline, Jenkins container bind mount, Nginx mount 검증, 개발 VM 배포 기준 문서를 함께 변경한다. |
| 최종 목표 | Jenkins가 `dev` 브랜치를 실제 VM workspace에 checkout하고, Docker socket을 통한 Compose 실행과 Nginx 설정 bind mount도 같은 VM 경로를 기준으로 하게 한다. |
| 작업 범위 | `Jenkinsfile`, `jenkins/docker-compose.jenkins.yml`, `.jenkins` 점검 스크립트, `docker-compose.yml`의 Nginx mount 선언(필요 시), Jenkins·개발 VM 배포 문서, 잘못 생성된 경로의 안전한 정리 절차 |
| 비목표 | Jenkins Job/credential의 실제 수정, VM에서 명령 실행, 모델 파일 이동, 서비스 코드·Nginx 라우팅 규칙 변경 |

## 2. 확정하려는 개발 VM 경로

사용자가 제시한 경로는 앞의 `/`를 포함한 Linux 절대 경로로 해석한다.

| VM host 경로 | 역할 | Git 추적 |
| --- | --- | --- |
| `/home/yp/apps/opt/smartdrain` | 전용 Jenkins 컨테이너를 띄우기 위한 최소 bootstrap clone. Jenkins Compose/Dockerfile만 제공한다. | clone source |
| `/home/yp/apps/apps/smart-drain` | Jenkins Job이 `dev`를 checkout하고 Docker Compose로 실제 배포하는 workspace | Jenkins checkout source, `.env`는 Git 제외 |
| `/home/yp/apps/opt/smartdrain-data/models/best.pt` | Git·Docker image 밖에 보관하는 YOLO 모델 | Git 제외 host artifact |

XGBoost 모델 `ai_service/model/sewer_xgboost_model.json`은 저장소 추적 파일이며 Docker image에 계속 포함한다. 모델 디렉터리 전체를 mount하지 않고 `best.pt` 파일만 read-only mount한다.

## 3. 현재 구현과 실제 실행 흐름

현재 Job은 **Pipeline script from SCM**, Script Path `Jenkinsfile`로 등록되어 있다. 따라서 Jenkins가 Job의 SCM 설정으로 Pipeline 정의를 가져오며, Pipeline이 시작된 뒤 `checkout scm`이 Custom Workspace에 같은 SCM의 설정된 브랜치(의도는 `dev`)를 checkout한다. bootstrap clone은 Jenkins 컨테이너 이미지와 Compose를 시작하는 역할만 하며, 배포 source가 아니다.

```text
현재 VM bootstrap clone (문서 기준 /opt/smartdrain)
    └─ jenkins/docker-compose.jenkins.yml 실행
          └─ host /apps/smart-drain
               ⇅ bind mount
             Jenkins container /deploy/smart-drain
                 └─ checkout scm → .env Secret File 복사 → docker compose 실행
                                      │
                                      └─ Docker socket → VM host Docker daemon
```

현재 추적 파일에서 확인한 값은 다음과 같다.

| 위치 | 현재 값 | 영향 |
| --- | --- | --- |
| `Jenkinsfile` | Custom Workspace·`DEPLOY_DIR` = `/deploy/smart-drain` | Jenkins 컨테이너 내부 경로를 기준으로 스크립트와 Compose를 실행한다. |
| `jenkins/docker-compose.jenkins.yml` | `/apps/smart-drain:/deploy/smart-drain` | VM 실제 경로와 다르고, container와 host에서 workspace 절대 경로가 다르다. |
| `docker-compose.yml` | `./nginx/default.conf` bind mount | Compose 실행 위치 기준의 상대 source path를 Docker daemon에 전달한다. |
| `docker-compose.dev.yml` | `./:/app`, `./frontend:/app` bind mount | 개발 override를 Jenkins에서 사용하면 같은 문제가 source 전체에도 발생한다. |
| `.jenkins/scripts/*.sh` | `cd "$DEPLOY_DIR"` 후 Compose 실행 | Pipeline 경로를 바꾸면 추가 스크립트 수정 없이 같은 경로를 따라간다. |

## 4. 문제 원인

Jenkins 컨테이너는 Docker Engine을 자체 실행하지 않고 `/var/run/docker.sock`으로 **VM host Docker daemon**에 명령을 보낸다. 따라서 Docker Compose가 bind mount source를 해석할 때 다음 두 관점이 섞인다.

```text
Jenkins container의 현재 디렉터리: /deploy/smart-drain
Docker daemon이 실제 bind source를 찾는 위치: VM host filesystem

Compose 상대 bind source
  ./nginx/default.conf
      ↓ container 기준으로 절대화
  /deploy/smart-drain/nginx/default.conf
      ↓ host Docker daemon이 이 문자열을 해석
  VM host의 /deploy/smart-drain/nginx/default.conf
```

즉 현재 `host /apps/smart-drain → container /deploy/smart-drain`처럼 서로 다른 절대 경로를 사용하면, Docker daemon은 host에 존재하지 않는 `/deploy/...`를 source로 보게 된다. Docker가 누락된 bind source 디렉터리를 만들 수 있어 VM 루트에 `/deploy` 및 그 아래 `nginx`가 생긴 현상과 일치한다. Jenkins container 자체를 띄우는 Compose의 `/apps/smart-drain` source도 현재 실제 VM 경로가 아니므로 VM 루트에 `/apps`를 만들 수 있다.

Nginx 설정 파일의 내용(`nginx/default.conf`, `nginx/default.dev.conf`)은 이 문제의 원인이 아니다. 경로를 잘못 해석한 bind mount 대상이므로, 이번 작업은 **Nginx 설정 파일의 위치·mount·실행 검증·잘못 생성된 경로 정리까지** 포함한다. `/api`, `/ws`, frontend proxy 같은 Nginx 라우팅 규칙은 변경하지 않는다.

## 5. 권장 목표 구조

**Jenkins container와 VM host가 실제 배포 workspace를 완전히 같은 절대 경로로 보게 한다.** 이 방식은 Docker socket을 유지한 채 Compose의 build context와 상대 bind mount를 모두 한 기준으로 맞춘다.

```text
VM host
/home/yp/apps/opt/smartdrain
    └─ jenkins/docker-compose.jenkins.yml로 Jenkins 시작

/home/yp/apps/apps/smart-drain
        ⇅ 같은 절대 경로로 bind mount
Jenkins container
/home/yp/apps/apps/smart-drain
    └─ Jenkins Custom Workspace / DEPLOY_DIR
        └─ checkout scm (Job SCM의 dev)
        └─ Secret File → .env
        └─ docker compose -p smartdrain-dev up -d --build
              ├─ ./nginx/default.conf → host의 같은 workspace/nginx/default.conf
              └─ SMARTDRAIN_YOLO_MODEL_PATH → host model best.pt (read-only)
```

목표 값은 아래와 같다.

| 구성 | 목표 값 |
| --- | --- |
| Jenkins Compose workspace mount | `/home/yp/apps/apps/smart-drain:/home/yp/apps/apps/smart-drain` |
| Jenkinsfile `customWorkspace` | `/home/yp/apps/apps/smart-drain` |
| Jenkinsfile `DEPLOY_DIR` | `/home/yp/apps/apps/smart-drain` |
| Jenkins Secret File의 모델 값 | `SMARTDRAIN_YOLO_MODEL_PATH=/home/yp/apps/opt/smartdrain-data/models/best.pt` |
| Jenkins Job SCM branch specifier | `*/dev` |
| Jenkins Pipeline script path | `Jenkinsfile` |

이 방식에서는 `docker-compose.yml`의 `./nginx/default.conf`와 `docker-compose.dev.yml`의 상대 mount를 바꿀 필요가 없다. 로컬 개발자의 Compose 실행 방식도 그대로 유지된다.

### 5.1 Nginx 처리 기준

| 구분 | 개발 VM Jenkins 배포 | 로컬 개발 Compose |
| --- | --- | --- |
| 설정 source | `/home/yp/apps/apps/smart-drain/nginx/default.conf` | `<local-repo>/nginx/default.dev.conf` |
| 컨테이너 target | `/etc/nginx/conf.d/default.conf:ro` | `/etc/nginx/conf.d/default.conf:ro` |
| 선택 Compose 파일 | `docker-compose.yml` | `docker-compose.yml` + `docker-compose.dev.yml` |
| 기대 결과 | production 기준 Nginx가 workspace의 추적 설정을 read-only로 사용 | 개발용 `/docs` 노출·Hot Reload 기준 설정 사용 |

Nginx 설정은 반드시 repository workspace의 `nginx/`에만 둔다. VM 루트 `/deploy/nginx`, `/apps/.../nginx` 또는 bootstrap clone의 Nginx 파일을 배포 source로 사용하지 않는다. 구현에서는 기존 Compose 상대 mount를 유지하고 Jenkins host/container workspace를 동일 경로로 통일한다. `.jenkins/scripts/preflight.sh`는 설정 파일 존재를, `validate.sh`는 Compose 해석 source·target·read-only 값을, `deploy.sh`는 Docker daemon이 실제 연결한 mount를 검사한다.

## 6. 승인 후 구현 단계

1. `jenkins/docker-compose.jenkins.yml`의 workspace source·target mount를 `/home/yp/apps/apps/smart-drain`의 동일 경로로 바꾼다.
2. `Jenkinsfile`의 `customWorkspace`와 `DEPLOY_DIR`를 같은 절대 경로로 변경한다. `.jenkins/scripts`는 `DEPLOY_DIR` 환경변수를 사용하므로 경로 문자열을 중복 수정하지 않는다.
3. Nginx source를 `workspace/nginx/default.conf` 하나로 고정한다. `docker-compose.yml` mount 선언을 long syntax로 명시하거나 기존 short syntax를 유지하되, Jenkins Preflight/Validate에서 source 파일·Compose 해석 경로를 검사한다. 어느 방식을 선택했는지 문서에 기록한다.
4. Jenkins Custom Workspace·개발/운영 배포 가이드와 관련 최신 계획/완료 문서의 이전 `/opt`, `/apps`, `/deploy` 예시를 실제 VM 경로로 정정한다. 과거 작업 기록은 사실 보존이 필요하므로, 변경하지 않고 새 문서에서 “이전 구성”으로만 설명할지 범위를 먼저 정한다.
5. Jenkins Job에서 SCM Branch Specifier가 `*/dev`, Script Path가 `Jenkinsfile`, Secret File credential ID가 `smartdrain-dev-env-file`인지 VM 관리자가 확인한다.
6. VM에서 bootstrap clone과 빈 workspace를 준비하고 전용 Jenkins 컨테이너를 재생성한다. 최초 build가 Custom Workspace에 `dev`를 checkout하는지 확인한다.
7. Validate·Deploy·Smoke test를 실행해 Nginx source mount, 모델 mount, `smartdrain-dev` Compose project와 HTTP endpoint를 확인한다.
8. 새 구조의 Nginx 컨테이너가 `/home/yp/apps/apps/smart-drain/nginx/default.conf`만 mount한 것을 inspect로 확인한 뒤, root `/deploy`와 `/apps`의 소유자·내용·다른 컨테이너 사용 여부를 확인한다. SmartDrain이 만든 빈/고아 경로만 정리한다.

## 7. 사용자 확인이 필요한 사항

| 확인 항목 | 권장안 | 이유 |
| --- | --- | --- |
| 실제 Linux 절대 경로 | **세 경로 모두 `/home/yp/...`가 맞는지 확인** | 요청에는 앞 슬래시가 빠져 있어 문서에서는 Linux 절대 경로로 해석했다. 사용자명·디렉터리 하나라도 다르면 Docker bind mount가 다시 잘못된다. |
| host/container workspace 경로 | **동일한 `/home/yp/apps/apps/smart-drain` 사용** | Docker socket 환경에서 Compose 상대 bind source가 host에서도 같은 위치를 가리키게 하는 핵심 조건이다. |
| Jenkins 재생성 권한 | **경로 변경 후 전용 Jenkins 컨테이너를 재생성** | `docker-compose.jenkins.yml` volume 변경은 기존 container를 재생성해야 반영된다. Jenkins home named volume은 유지한다. |
| Job SCM 설정 | **Branch Specifier `*/dev`, Script Path `Jenkinsfile` 유지** | Pipeline script from SCM과 내부 `checkout scm`이 모두 같은 의도된 SCM/브랜치를 사용하게 한다. |
| VM `.env`의 Nginx 포트 | **현재 smoke test의 `8099`와 일치 여부 확인** | `smoke-test.sh`는 `127.0.0.1:8099`를 호출하지만 `.env.example`의 기본 `NGINX_HTTP_PORT`는 `80`이다. 실제 Secret File `.env`에서 `NGINX_HTTP_PORT=8099`인지 확인하거나, 포트 기준을 함께 정해야 한다. |
| `/home/yp` 권한 | **Jenkins container root와 host Docker daemon이 workspace·Nginx 파일을 읽고 쓸 수 있게 확인** | `/home/yp` 상위 디렉터리의 execute 권한 또는 workspace 소유권이 부족하면 checkout·bind mount가 실패한다. |
| 기존 root 디렉터리 정리 | **Nginx 전환 검증 후 SmartDrain 고아 경로만 함께 정리** | 사용자가 이번 범위에 Nginx 처리를 포함했다. 단, `/apps`, `/deploy` 안의 소유자·내용·container mount를 확인하고 다른 서비스가 없다는 확인 뒤에만 삭제한다. |
| 이전 문서 처리 | **활성 배포 가이드는 정정, step/PR 이력은 보존 권장** | 과거 결과 문서를 현재 사실처럼 덮어쓰지 않으면서 작업자가 최신 경로를 분명히 찾을 수 있다. |

## 8. 검증 계획

| 검증 | 기대 결과 |
| --- | --- |
| VM에서 `test -d /home/yp/apps/opt/smartdrain` | Jenkins bootstrap clone이 실제 경로에 있다. |
| VM에서 `test -d /home/yp/apps/apps/smart-drain` | Jenkins checkout 대상 workspace가 존재하고 쓰기 가능하다. |
| Jenkins container에서 `pwd` | Pipeline의 작업 경로가 `/home/yp/apps/apps/smart-drain`이다. |
| Jenkins container에서 `docker compose config` | nginx source가 `/home/yp/apps/apps/smart-drain/nginx/default.conf`, YOLO source가 `/home/yp/apps/opt/smartdrain-data/models/best.pt`로 해석된다. |
| Jenkins Preflight/Validate의 Nginx 검사 | `nginx/default.conf`가 workspace 안의 일반 파일이며, Compose가 해당 파일을 read-only target으로 mount한다고 확인한다. |
| Jenkins Validate 단계 | frontend lint build, AI test, 두 모델 파일 검사가 통과한다. |
| Jenkins Deploy 단계 | `smartdrain-dev` project가 의도한 컨테이너만 재기동한다. |
| Jenkins Smoke test | `.env`에서 확정한 Nginx host port의 `/`와 `/api/dashboard/summary`가 성공한다. |
| Nginx container inspect | host source가 `/home/yp/apps/apps/smart-drain/nginx/default.conf`, target이 `/etc/nginx/conf.d/default.conf`, read-only임을 확인한다. |
| VM 파일 정리 | 새 배포 뒤 root `/deploy` 또는 root `/apps` 아래에 Nginx source가 새로 생성되지 않고, 확인된 SmartDrain 고아 경로만 제거한다. |
| `git diff --check` | 인프라·문서 변경에 공백 오류가 없다. |

## 9. 리스크와 대응

| 리스크 | 대응 |
| --- | --- |
| `Pipeline script from SCM`의 Job branch와 `checkout scm` branch가 다름 | Job 설정에서 `*/dev`를 확인하고 첫 build console에서 checkout revision을 확인한다. Jenkinsfile의 `DEPLOY_BRANCH` 값은 현재 checkout을 강제하지 않으므로 설정 확인이 필요하다. |
| `/home/yp` 경로 권한으로 bind mount 실패 | 재생성 전에 `yp` 및 Jenkins/root가 workspace에 접근할 수 있는지 점검한다. 파일 소유권 정책은 VM 관리자와 합의한다. |
| 기존 `/apps`, `/deploy`를 너무 일찍 삭제 | Nginx container mount·Jenkins build·서비스 응답을 먼저 확인하고, 다른 Docker container 또는 사용자가 소유한 파일이 없는 SmartDrain 고아 경로만 정리한다. |
| Compose build context를 host 절대 경로로 억지 변경 | Jenkins container가 source를 tar로 읽어 build해야 하므로, host-only `--project-directory` 우회 대신 동일 경로 bind mount를 사용한다. |
| smoke test 포트 불일치 | 실제 Secret File `.env`의 `NGINX_HTTP_PORT`와 script의 호출 포트를 한 기준으로 맞춘다. |

## 10. 승인 후 제안 커밋 메시지

제목:

```text
chore: 개발 VM Jenkins 배포 경로를 실제 host 경로로 정렬
```

내용:

```text
- Jenkins Custom Workspace와 host bind mount를 동일한 절대 경로로 통일한다.
- Docker socket 환경에서 Compose 상대 bind mount가 VM 배포 source를 가리키도록 보정한다.
- Nginx 설정 파일의 host mount를 검증하고 잘못 생성된 고아 경로 정리 절차를 포함한다.
- Jenkins 배포 문서와 모델 artifact 경로를 개발 VM 기준으로 갱신한다.
```
