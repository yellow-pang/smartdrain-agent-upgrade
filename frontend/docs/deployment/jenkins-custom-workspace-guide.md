# SmartDrain Jenkins Custom Workspace 적용 메모

> Notion에 그대로 붙여넣기 위한 최종 적용 방식 정리입니다.

## 적용 결론

SmartDrain은 Jenkins와 VM host가 모두 `/home/yp/apps/apps/smart-drain`을 Custom Workspace로 사용한다. Docker socket 환경에서 Compose의 상대 bind mount가 VM host에서도 같은 source를 가리키게 하려면, Jenkins container와 host의 workspace 절대 경로가 같아야 한다.

```text
VM /home/yp/apps/opt/smartdrain (Jenkins bootstrap clone)
        ↓ Jenkins container 시작
VM /home/yp/apps/apps/smart-drain
        ⇅ bind mount
Jenkins /home/yp/apps/apps/smart-drain (Custom Workspace, 배포 source)
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
| Git 인증 | Jenkins Job SCM Credential | Jenkins Job SCM Credential (`Username with password` + GitHub PAT) |
| `.env` | Jenkins Secret File 복사 | Jenkins Secret File 복사 |
| 실행 폴더 | Jenkins 기본 workspace | `/home/yp/apps/apps/smart-drain` Custom Workspace |
| Compose | workspace에서 실행 | Custom Workspace에서 실행 |

즉, Git과 Secret 관리 흐름은 health-center와 같다. SmartDrain은 실제 VM workspace를 Jenkins container에도 같은 절대 경로로 mount해 Docker socket의 path 해석 차이를 없앤다.

## Jenkinsfile의 핵심

```groovy
agent {
    node {
        label 'built-in'
        customWorkspace '/home/yp/apps/apps/smart-drain'
    }
}
```

`checkout scm` 직후 아래 Credential의 파일을 `.env`로 복사한다.

```text
Credential type: Secret file
Credential ID: smartdrain-dev-env-file
Destination: /home/yp/apps/apps/smart-drain/.env
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
| 배포 source mount | `/home/yp/apps/apps/smart-drain:/home/yp/apps/apps/smart-drain` |
| Jenkins bootstrap clone | `/home/yp/apps/opt/smartdrain` |
| 외부 YOLO 모델 | `/home/yp/apps/opt/smartdrain-data/models/best.pt` |

`/home/yp/apps/apps/smart-drain`은 Jenkins가 checkout하는 배포 전용 workspace이므로 최초 실행 전에 비어 있어야 한다. Jenkins Compose와 Dockerfile을 제공하는 bootstrap clone은 `/home/yp/apps/opt/smartdrain`에 별도로 둔다.

```bash
git clone -b dev https://github.com/<owner>/<repository>.git /home/yp/apps/opt/smartdrain
mkdir -p /home/yp/apps/apps/smart-drain
mkdir -p /home/yp/apps/opt/smartdrain-data/models
cd /home/yp/apps/opt/smartdrain/jenkins
docker compose -f docker-compose.jenkins.yml up -d --build
```

Jenkins container는 Docker socket을 사용하므로 같은 VM의 Docker daemon에 접근한다. 따라서 Jenkins UI·Credential은 분리되지만 Docker daemon 자체의 권한은 health 프로젝트와 완전히 격리되지 않는다. 완전한 격리가 필요하면 별도 VM 또는 별도 Docker daemon/agent가 필요하다.

## VM과 Jenkins에서 필요한 설정

1. VM에 `/home/yp/apps/opt/smartdrain` bootstrap clone, 빈 `/home/yp/apps/apps/smart-drain` 디렉터리, `/home/yp/apps/opt/smartdrain-data/models` 디렉터리를 만든다.
2. 전용 Jenkins Compose에 정의된 `/home/yp/apps/apps/smart-drain:/home/yp/apps/apps/smart-drain` mount를 사용한다.
3. Jenkins Job을 `Pipeline script from SCM`으로 만들고 SmartDrain `dev` 브랜치를 지정한다.
4. HTTPS repository URL과 GitHub 사용자명/PAT를 사용하는 `Username with password` SCM Credential을 등록한다.
5. `.env` 내용으로 Jenkins Secret File credential `smartdrain-dev-env-file`을 등록한다. VM 배포 값에는 `SMARTDRAIN_YOLO_MODEL_PATH=/home/yp/apps/opt/smartdrain-data/models/best.pt`를 포함한다.
6. 기존 Job과 같은 주기로 Poll SCM을 설정한다.

## AI 모델 배치 기준

- YOLO `best.pt`는 Git과 Docker image에 넣지 않고 VM의 `/home/yp/apps/opt/smartdrain-data/models/best.pt`에 저장한다.
- Compose는 이 파일만 컨테이너의 `/app/ai_service/model/best.pt`에 읽기 전용으로 mount한다.
- XGBoost `ai_service/model/sewer_xgboost_model.json`은 Git 추적 파일이며 image에 포함된다. 디렉터리 전체를 mount하면 이 JSON이 가려지므로 사용하지 않는다.
- Jenkins Validate 단계는 두 모델 파일이 컨테이너에서 비어 있지 않은지 확인한 뒤 배포한다.
- 모델 교체 뒤에는 `docker compose -p smartdrain-dev up -d --force-recreate ai-service`로 AI 서비스만 재생성한다.

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
