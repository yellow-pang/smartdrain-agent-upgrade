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

## VM과 Jenkins에서 필요한 설정

1. VM에 빈 `/apps/smart-drain` 디렉터리를 만든다.
2. 기존 Jenkins Compose 파일에 아래 mount를 추가한다.

```yaml
- /apps/smart-drain:/deploy/smart-drain
```

3. Jenkins를 재생성한다. 기존 `jenkins-home`, Docker socket, Maven/npm cache volume은 그대로 유지한다.
4. Jenkins Job을 `Pipeline script from SCM`으로 만들고 SmartDrain `develop` 브랜치를 지정한다.
5. Job의 SSH SCM Credential을 등록한다.
6. `.env` 내용으로 Jenkins Secret File credential `smartdrain-dev-env-file`을 등록한다.
7. 기존 Job과 같은 주기로 Poll SCM을 설정한다.

## 외부 health-center 프로젝트 변경 범위

수정이 필요한 것은 아래 Compose 파일의 mount 한 줄뿐이다.

```text
C:\Dev\health-center-smart-reservation\infra\jenkins\docker-compose.jenkins.yml
```

이번 최종 방식에서는 Jenkins가 별도 `git fetch`나 `ssh` 명령을 실행하지 않는다. 따라서 health-center Jenkins Dockerfile에 `openssh-client`를 추가할 필요가 없다.
