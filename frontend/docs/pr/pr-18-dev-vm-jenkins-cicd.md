## PR 제목

[feat] SmartDrain 전용 Jenkins 개발 VM CI/CD 구성

## 작업 내용

- SmartDrain 전용 Jenkins 컨테이너를 `8082` UI 포트와 별도 Jenkins home volume으로 구성했습니다.
- Jenkinsfile은 `/apps/smart-drain`과 연결된 `/deploy/smart-drain` Custom Workspace에서 실행됩니다.
- Jenkins SCM checkout 뒤 Secret File credential `smartdrain-dev-env-file`을 `.env`로 복사해 비밀값을 Git에서 분리했습니다.
- frontend lint와 AI pytest를 Docker CI target으로 분리하고, Compose 검증·배포·선택 seed·smoke test 스크립트를 추가했습니다.
- 개발 VM 적용 절차, HTTPS PAT 기반 SCM credential, Cloudflare Tunnel, 설계 변경 이력을 step 및 deployment 문서로 정리했습니다.

## 주요 변경 파일

| 구분                   | 파일                                                                                                                                                                     |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Jenkins pipeline       | `Jenkinsfile`, `.jenkins/scripts/*`                                                                                                                                      |
| 전용 Jenkins 실행 환경 | `jenkins/Dockerfile`, `jenkins/docker-compose.jenkins.yml`                                                                                                               |
| CI Docker target       | `frontend/Dockerfile`, `ai_service/Dockerfile`                                                                                                                           |
| 문서                   | `frontend/docs/plans/plan-13-dev-vm-jenkins-cicd.md`, `frontend/docs/steps/step-15-dev-vm-jenkins-cicd.md`, `frontend/docs/deployment/jenkins-custom-workspace-guide.md` |

## 변경 전/후

| 항목              | 변경 전                                  | 변경 후                                                     |
| ----------------- | ---------------------------------------- | ----------------------------------------------------------- |
| Jenkins 관리 범위 | 기존 health 프로젝트 Jenkins 재사용 검토 | SmartDrain 전용 `smartdrain-jenkins` 컨테이너               |
| source checkout   | 별도 SSH clone/fetch 방식 검토           | Custom Workspace에서 Jenkins SCM checkout 1회               |
| Git 인증          | SSH Deploy Key 방식 검토                 | 팀 repository 접근에 맞춘 HTTPS + PAT Jenkins credential    |
| `.env` 관리       | VM 파일 사전 생성 방식 검토              | Jenkins Secret File을 checkout 직후 복사                    |
| 배포 검증         | 수동 Compose 검증 중심                   | lint, AI pytest, Compose config, smoke test pipeline 단계화 |

## 테스트 결과

| 검증                           | 결과   | 비고                                                       |
| ------------------------------ | ------ | ---------------------------------------------------------- |
| `git diff --check`             | 통과   | 공백 오류 없음                                             |
| Jenkinsfile/스크립트 정적 검토 | 통과   | Custom Workspace, Secret File, Compose project 이름을 확인 |
| frontend lint Docker target    | 미실행 | 로컬 Docker Desktop daemon이 실행 중이 아니었음            |
| AI pytest Docker target        | 미실행 | 로컬 Docker Desktop daemon이 실행 중이 아니었음            |
| 전용 Jenkins Compose 기동      | 미실행 | 팀 합의와 개발 VM 적용 전 단계                             |
| Cloudflare Tunnel 연결         | 미실행 | 개발 VM 배포 후 진행                                       |

## 리뷰 포인트

- 팀 합의 후 `develop`에 반영한 뒤에만 VM 자동 배포를 시작합니다.
- Jenkins Job SCM은 HTTPS repository URL과 GitHub PAT의 `Username with password` credential을 사용합니다. PAT와 `.env`는 PR, Git, Jenkins console log에 남기지 않습니다.
- Jenkins Secret File credential ID는 `smartdrain-dev-env-file`이며, checkout 직후 `/deploy/smart-drain/.env`로 복사됩니다.
- 전용 Jenkins는 health Jenkins의 Job·Credential·volume을 수정하지 않습니다. 다만 두 Jenkins는 같은 VM Docker socket을 공유하므로 Docker daemon 권한까지 완전히 격리되지는 않습니다.
- 최초 seed가 필요할 때만 Jenkins parameter `SEED_MOCK_DATA=true`로 실행합니다. 일반 polling 배포는 기존 DB volume과 데이터를 보존합니다.

## 비고

- 실제 VM 적용 순서는 `frontend/docs/steps/step-15-dev-vm-jenkins-cicd.md`의 **현재 확정 구성**과 **실제 적용 7단계**를 확인합니다.
- Notion 공유용 요약은 `frontend/docs/deployment/jenkins-custom-workspace-guide.md`를 사용합니다.
- 실제 commit, push, Pull Request 생성, 브랜치 종료는 담당자가 진행합니다.
