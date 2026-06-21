# SmartDrain Jenkins Custom Workspace 적용 메모

> Notion에 그대로 붙여넣기 위한 최종 적용 방식 정리입니다.

## 적용 결론

SmartDrain은 Jenkins의 Custom Workspace를 `/deploy/smart-drain`으로 사용한다. 이 경로는 Jenkins 컨테이너에서 보이는 경로이며, VM host의 `/apps/smart-drain`과 bind mount로 연결된다.

```text
VM /apps/smart-drain
        ⇅ bind mount
Jenkins /deploy/smart-drain (Custom Workspace)
        ↓
checkout scm
        ↓
Jenkins Secret File → .env 복사
        ↓
docker compose -p smartdrain-dev up -d --build
```

## 기존 health-center 방식과의 관계

| 항목 | health-center | SmartDrain 최종 방식 |
| --- | --- | --- |
| Git checkout | `checkout scm` | `checkout scm` |
| SSH 인증 | Jenkins Job SCM Credential | Jenkins Job SCM Credential |
| `.env` | Jenkins Secret File 복사 | Jenkins Secret File 복사 |
| 실행 폴더 | Jenkins 기본 workspace | `/deploy/smart-drain` Custom Workspace |
| Compose | workspace에서 실행 | Custom Workspace에서 실행 |

즉, Git과 Secret 관리 흐름은 health-center와 같다. SmartDrain은 사용자가 원하는 `/apps/smart-drain` 경로를 유지하기 위해 workspace 위치만 Custom Workspace로 바꾼다.

## Jenkinsfile의 핵심

```groovy
agent {
    node {
        customWorkspace '/deploy/smart-drain'
    }
}
```

`checkout scm` 직후 아래 Credential의 파일을 `.env`로 복사한다.

```text
Credential type: Secret file
Credential ID: smartdrain-dev-env-file
Destination: /deploy/smart-drain/.env
```

따라서 `.env`는 Git에 저장되지 않으며, Git checkout이나 workspace 정리로 사라져도 매 배포마다 다시 생성된다.

## 전용 Jenkins 구성

SmartDrain은 `health-center-jenkins`를 재사용하지 않고 전용 Jenkins 컨테이너를 사용한다. Jenkins 설정, Job, Credential, log, plugin 관리 범위는 SmartDrain 팀으로 분리된다.

| 항목 | SmartDrain 전용 값 |
| --- | --- |
| Compose 파일 | `/jenkins/docker-compose.jenkins.yml` |
| Dockerfile | `/jenkins/Dockerfile` |
| container name | `smartdrain-jenkins` |
| Jenkins UI | VM host `8082` → container `8080` |
| Agent port | VM host `50001` → container `50000` |
| Jenkins home volume | `smartdrain-jenkins-home` |
| 배포 source mount | `/apps/smart-drain:/deploy/smart-drain` |

VM에서 SmartDrain 저장소를 `/apps/smart-drain`에 최초 clone한 뒤 다음 명령으로 전용 Jenkins를 시작한다.

```bash
cd /apps/smart-drain/jenkins
docker compose -f docker-compose.jenkins.yml up -d --build
```

Jenkins container는 Docker socket을 사용하므로 같은 VM의 Docker daemon에 접근한다. 따라서 Jenkins UI·Credential은 분리되지만 Docker daemon 자체의 권한은 health 프로젝트와 완전히 격리되지 않는다. 완전한 격리가 필요하면 별도 VM 또는 별도 Docker daemon/agent가 필요하다.

## VM과 Jenkins에서 필요한 설정

1. VM에 빈 `/apps/smart-drain` 디렉터리를 만든다.
2. 전용 Jenkins Compose에 정의된 `/apps/smart-drain:/deploy/smart-drain` mount를 사용한다.
3. Jenkins Job을 `Pipeline script from SCM`으로 만들고 SmartDrain `develop` 브랜치를 지정한다.
4. Job의 SSH SCM Credential을 등록한다.
5. `.env` 내용으로 Jenkins Secret File credential `smartdrain-dev-env-file`을 등록한다.
6. 기존 Job과 같은 주기로 Poll SCM을 설정한다.

## 기존 health-center Jenkins를 원래대로 유지하는 방법

SmartDrain 전용 Jenkins 방식에서는 health-center 프로젝트 파일을 수정할 필요가 없다.

이미 아래 변경을 health-center에 적용했다면 되돌려도 된다.

- `infra/jenkins/docker-compose.jenkins.yml`의 `- /apps/smart-drain:/deploy/smart-drain` mount 제거
- `infra/jenkins/Dockerfile`에 SmartDrain을 위해 추가한 `git`, `openssh-client` 패키지 제거

health-center Jenkins를 재생성할 때는 Jenkins 설정 volume을 지우지 않는다.

```bash
cd /path/to/health-center-smart-reservation/infra/jenkins
docker compose -f docker-compose.jenkins.yml up -d --build
# down -v 는 실행하지 않는다.
```

기존 `jenkins-home` named volume을 유지하면 health Jenkins의 Job, Credential, plugin 설정은 그대로 남는다.
