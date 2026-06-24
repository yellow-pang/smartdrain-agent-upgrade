# 21 Jenkins 스크립트 실행 권한 보정 결과

## 변경 요약

Jenkins가 Custom Workspace(`/deploy/smart-drain`)에서 배포 스크립트를 직접 실행할 때 발생할 수 있는 `Permission denied` 오류를 방지했다. Git에 셸 스크립트 실행 권한을 저장하고, Pipeline은 스크립트 파일을 직접 실행하지 않고 `sh` 인터프리터로 실행하도록 변경했다.

## 변경 전/후

| 항목 | 변경 전 | 변경 후 |
| --- | --- | --- |
| Git 스크립트 권한 | `.jenkins/scripts/*.sh`가 `100644`로 추적되어 checkout 뒤 실행 권한이 없음 | 6개 스크립트를 `100755`로 추적 |
| Jenkins 실행 방식 | `.jenkins/scripts/preflight.sh`처럼 파일을 직접 실행 | `sh .jenkins/scripts/preflight.sh`처럼 셸이 파일을 읽어 실행 |
| `noexec` mount 대응 | 실행 비트가 있어도 mount 옵션에 따라 직접 실행이 실패할 수 있음 | `sh script.sh` 실행으로 직접 실행 제한 영향을 줄임 |

## 적용 파일

| 파일 | 적용 내용 |
| --- | --- |
| `Jenkinsfile` | Preflight, Validate, Deploy, Seed, Smoke test, failure log 수집 단계를 `sh .jenkins/scripts/...` 방식으로 변경 |
| `.jenkins/scripts/collect-logs.sh` | Git 실행 권한 추가 |
| `.jenkins/scripts/deploy.sh` | Git 실행 권한 추가 |
| `.jenkins/scripts/preflight.sh` | Git 실행 권한 추가 |
| `.jenkins/scripts/seed.sh` | Git 실행 권한 추가 |
| `.jenkins/scripts/smoke-test.sh` | Git 실행 권한 추가 |
| `.jenkins/scripts/validate.sh` | Git 실행 권한 추가 |

## Jenkins 실행 흐름

```text
Jenkins checkout (Git 100755 유지)
    -> Prepare environment (.env 복사)
    -> sh .jenkins/scripts/preflight.sh
    -> sh .jenkins/scripts/validate.sh
    -> sh .jenkins/scripts/deploy.sh
    -> sh .jenkins/scripts/smoke-test.sh
    -> 실패 시 sh .jenkins/scripts/collect-logs.sh
```

`sh script.sh` 방식은 스크립트 파일 자체의 실행 비트가 누락되었거나 workspace mount에 `noexec`가 적용된 경우에도 셸이 파일 내용을 읽어 실행할 수 있다. Git의 `100755` 설정은 checkout 이후에도 올바른 권한을 유지하는 영구 조치다.

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| `git ls-files --stage .jenkins/scripts` | 통과 | 6개 셸 스크립트가 모두 `100755`로 표시됨 |
| `git diff --cached --summary` | 통과 | `100644 => 100755` mode 변경 6건 확인 |
| `git diff --check` | 통과 | Jenkinsfile 공백 오류 없음 |
| `git diff --cached --check` | 통과 | 실행 권한 변경의 공백 오류 없음 |
| 로컬 셸 구문 검사 | 미실행 | 현재 Windows 작업 환경에 `sh` 실행기가 없음 |
| VM Jenkins 재빌드 | 미실행 | `dev` 반영 뒤 Jenkins 컨테이너에서 확인 필요 |

## VM 확인 사항

1. Jenkins Job의 SCM Branch Specifier가 `*/dev`인지 확인한다.
2. Jenkins 컨테이너에서 `cd /deploy/smart-drain && git ls-files --stage .jenkins/scripts`를 실행해 `100755`인지 확인한다.
3. `Build Now`로 Preflight부터 Smoke test까지 통과하는지 확인한다.
4. 여전히 `Permission denied`가 발생하면 Jenkins 컨테이너에서 `findmnt -T /deploy/smart-drain`을 실행해 `noexec` 여부와 workspace volume 권한을 확인한다.

## 권장 커밋 메시지

```text
fix: Jenkins 스크립트 실행 권한 보정

- 배포용 셸 스크립트에 Git 실행 권한을 추가한다.
- Jenkins Pipeline에서 sh 인터프리터로 스크립트를 실행한다.
```
