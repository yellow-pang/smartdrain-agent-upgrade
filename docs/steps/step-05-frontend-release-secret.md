# Step 05. Frontend Release 키의 Secrets 전환

## 1. 배경과 확인한 문제

PR #8의 main merge commit `7c63a01`에서 시작한 [Release 실행](https://github.com/yellow-pang/smartdrain-agent-upgrade/actions/runs/37191782873)은 Frontend 게시 전 키 누락 검사에서 실패했다. Frontend CI lint/build와 Backend·AI ARM 이미지 게시 Job은 성공했으며 manifest와 Mac 배포 요청은 건너뛰었다. 이 상태는 이번 수정 전 조회에서 확인한 것이며 새 workflow의 원격 검증 결과는 아니다.

기존 workflow는 Repository variable을 build Job 전체에 전달했다. 사용자는 GitHub 설정·로그 노출을 줄이기 위해 Secrets 참조로 변경하도록 승인했다. 작업 시작 시 로컬 `dev`의 HEAD는 `544635c`이고 미커밋 변경은 없었다.

## 2. 구조와 적용 결과

`release.yml`의 키 원본을 `vars`에서 `secrets.COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY`로 바꾸고, Frontend matrix Job일 때만 전달하도록 제한했다. 키 누락 시 Repository secret 등록을 안내하며 기존 `add-mask` 처리를 유지한다.

Secrets의 저장·자동 마스킹을 사용하면서 환경변수 이름과 기존 게시 조건을 유지하는 최소 변경이다. CI placeholder, 수동 build-only 실행, digest/manifest/dispatch 계약은 바꾸지 않았다.

실행 흐름은 `Repository secret → Frontend build Job → 기존 Docker build argument → Next.js 공개 환경값 → 지도 SDK`다. 실제 키를 읽거나 파일·검증 출력에 기록하지 않았다.

## 3. 주요 변경 파일

| 파일 | 변경 내용과 역할 |
| --- | --- |
| `.github/workflows/release.yml` | Secrets 참조, Frontend Job 한정 전달, 누락 안내 수정 |
| `docs/verification/17_배포_운영_런북.md` | Secrets 등록 위치와 공개 범위, 과거 workflow 재시도 기준 안내 |
| `docs/plans/plan-05-frontend-release-secret.md` | 승인 범위·대안·검증 계획 |
| 이 Steps | 실제 검증 결과와 남은 작업 기록 |

## 4. 검증 결과

검증은 실제 키 대신 sentinel을 사용했으며, shell 입력 검사의 ARM·디스크 조회만 임시 함수로 대체했다. 실제 ARM 이미지 빌드는 실행하지 않았다.

| 검증 | 결과 |
| --- | --- |
| Ruby/Psych Release YAML 파싱 | 성공 |
| 추출한 `run` script의 `bash -n` | 5개 성공 |
| inline Python AST 파싱 | 4개 성공 |
| Frontend 게시 + 빈 키 | 예상대로 실패, Repository secret 안내, build 시작 기록 없음 |
| Frontend 게시 + sentinel 키 | 성공, `add-mask` 명령 생성 확인 |
| Backend 게시 + 빈 Frontend 키 | 성공 |
| AI 게시 + 빈 Frontend 키 | 성공 |
| 수동 Frontend build + 빈 키 | 성공, 기존 동작 유지 |
| Secrets 참조·Frontend 한정 조건 검토 | 정적 검사 성공, GitHub expression 런타임은 미실행 |
| `git diff --check` | 성공 |

이번 수정으로 발견한 신규 문법·입력 검사 오류는 없다. 기존 실패 원인은 main Release의 키 설정 누락이며, 새 workflow의 실제 키 등록·로그 마스킹·GHCR 게시를 로컬 검사만으로 완료됐다고 판단하지 않는다.

## 5. 계획 대비와 제한사항

[Plan 05](../plans/plan-05-frontend-release-secret.md)의 승인 범위대로 적용했다. Dockerfile·앱 코드·패키지·환경변수 이름과 외부 저장소 설정은 변경하지 않았다.

- 사용자는 Repository secret `COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY`를 등록해야 한다. Variables에만 등록한 값은 읽지 않는다.
- 이 수정이 포함된 새 main Release에서 검증한다. 과거 run 재시도는 과거 workflow revision을 사용하므로 Secrets 전환을 반영하지 못한다.
- Kakao JavaScript 키는 기존 Docker build argument와 브라우저용 환경값으로 전달된다. Secrets는 GitHub 저장·로그 보호를 강화하지만 빌드 산출물과 브라우저에서 키를 완전히 숨기지 않는다.
- Kakao SDK 허용 도메인은 별도로 제한해야 하며 서버용 비밀키를 이 경로에 공급하지 않는다.
- 실제 키 등록·원격 Actions·GHCR 게시·배포는 이번 파일 수정 단계에서 실행하지 않았다. Frontend 앱 코드를 바꾸지 않아 lint/type/build를 다시 실행하지 않았다.
