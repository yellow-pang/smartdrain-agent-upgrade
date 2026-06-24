## PR 제목

[chore] 개발 VM Jenkins 경로와 Nginx mount 검증 정렬

## 작업 내용

- Jenkins Custom Workspace와 `DEPLOY_DIR`를 `/home/yp/apps/apps/smart-drain`으로 통일했습니다.
- Jenkins container의 workspace bind mount도 같은 절대 경로로 변경해, Docker socket을 통한 Compose 상대 bind mount가 VM host에서 올바른 source를 가리키게 했습니다.
- Nginx 설정 파일 `nginx/default.conf`의 존재를 Preflight 단계에서 확인합니다.
- Validate 단계에서 Compose가 Nginx 설정을 workspace source, `/etc/nginx/conf.d/default.conf` target, read-only로 해석하는지 확인합니다.
- Deploy 단계에서 Docker daemon이 실제 Nginx container에 연결한 mount source와 read-only 상태를 검사합니다.
- Smoke test를 Jenkins container의 `127.0.0.1:8099` 호출 방식에서 Nginx container 내부의 `/`, `/api/dashboard/summary` 확인 방식으로 변경했습니다.
- 실제 개발 VM에서 기존 SmartDrain 컨테이너·image cache·고아 `/apps`, `/deploy` 경로를 안전하게 점검하고 전환하는 상세 가이드를 추가했습니다.

## 변경 파일

| 구분 | 파일 |
| --- | --- |
| Jenkins Pipeline | `Jenkinsfile` |
| Jenkins container mount | `jenkins/docker-compose.jenkins.yml` |
| 배포 검증 | `.jenkins/scripts/preflight.sh`, `validate.sh`, `deploy.sh`, `smoke-test.sh` |
| 배포 가이드 | `docs/deployment/jenkins-custom-workspace-guide.md`, `docs/deployment/development-production-guide.md` |
| 계획·실행 기록 | `docs/plans/plan-20-*`, `docs/steps/step-23-*` |

## 검증 결과

- `git diff --check` 통과
- `docker compose -f jenkins/docker-compose.jenkins.yml config --quiet` 통과
  - 로컬 Windows Docker 사용자 설정 파일 접근 경고는 있었으나 Compose 설정 검증은 성공했습니다.
- Jenkins 셸 스크립트의 실제 Linux 실행·Docker build·VM 컨테이너 재기동은 미실행입니다.
  - 현재 작업 환경은 개발 VM과 Docker daemon에 접근할 수 없습니다.
  - VM 실행 절차는 `docs/steps/step-23-dev-vm-jenkins-path-nginx-migration-guide.md`를 따릅니다.

## 리뷰 포인트

- `jenkins/docker-compose.jenkins.yml`의 host/container workspace가 동일한 `/home/yp/apps/apps/smart-drain`인지 확인합니다.
- Jenkins Job이 `Pipeline script from SCM`, Script Path `Jenkinsfile`, Branch Specifier `*/dev`로 설정되어 있는지 확인합니다.
- Jenkins Secret File의 `SMARTDRAIN_YOLO_MODEL_PATH`가 `/home/yp/apps/opt/smartdrain-data/models/best.pt`인지 확인합니다.
- 최초 Jenkins build에서 Nginx mount 검사와 Nginx 내부 smoke test가 모두 통과하는지 확인합니다.
- VM 루트 `/apps`, `/deploy`는 다른 서비스 mount 여부를 확인한 뒤 SmartDrain 고아 경로만 정리하는지 확인합니다.

## 비고

- Nginx의 `/api`, `/ws`, frontend proxy 규칙은 변경하지 않았습니다.
- PostgreSQL volume, Jenkins home volume, YOLO 모델 파일은 정리 대상이 아닙니다.
- 실제 VM 전환, GitHub PR 생성·push는 담당자가 진행합니다.
