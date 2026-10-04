# Plan 05. Frontend Release 키의 Secrets 전환

## 1. 요청 배경과 완료 조건

PR #8 병합 후 Release의 Frontend 입력 검사에서 Kakao Maps 키 누락으로 실패했다. 사용자는 Variables에 값이 표시되는 것을 우려해 Repository secret에서 읽도록 파일 수정을 요청했다. 이 요청으로 아래 Secrets 전환 범위를 승인받았으며 추가 승인 대기 없이 적용한다.

완료 조건은 키를 `secrets`에서 읽고 Frontend Job에만 공급하며, 누락 안내와 운영 가이드가 새 등록 위치를 설명하는 것이다. 실제 키는 파일·검증 출력에 기록하지 않는다.

## 2. 현재 구현과 근거

- `.github/workflows/release.yml`: `vars.COMPOSE_FRONTEND_KAKAO_MAP_APP_KEY`를 build Job 전체에 전달하고, 게시 전 입력 검사에서 누락을 차단한다. `::add-mask::` 처리와 Frontend build argument 전달이 있다.
- `frontend/next.config.mjs`, `frontend/components/risk-map.tsx`: 같은 값을 브라우저용 `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`로 사용한다.
- `docs/verification/17_배포_운영_런북.md`: Repository variable 등록을 안내한다.
- 기존 CI의 placeholder, 수동 Release의 build-only 동작, digest/manifest/dispatch 흐름은 유지한다.

## 3. 범위와 대안

| 대안 | 영향 | 판단 |
| --- | --- | --- |
| Variables 유지 + 수동 mask | 설정 화면에서 값 확인 가능, mask 등록 전 출력 가능 | 사용자의 저장 방식 변경 요구를 충족하지 못함 |
| Repository secret 사용 | 암호화 저장·GitHub 자동 로그 마스킹, workflow 참조와 등록 위치 변경 필요 | 승인된 선택 |

수정 대상은 Release workflow, 해당 운영 가이드, 이 Plan과 대응 Steps다. Dockerfile·앱 코드·환경변수 이름·의존성·API·DB는 변경하지 않는다. GitHub 설정 변경, 실제 키 등록, commit/push/merge 및 원격 실행은 이번 파일 수정 범위에 포함하지 않는다.

## 4. 적용 순서와 실행 흐름

1. Secret 참조를 Frontend matrix Job으로 제한한다.
2. 누락 오류를 Repository secret 안내로 바꾸고 기존 mask 처리를 유지한다.
3. 운영 가이드에 등록 위치, 브라우저 공개 범위, workflow 변경 후 재실행 기준을 설명한다.
4. YAML·shell·inline Python 문법과 키 누락/존재 입력 검사, diff를 검증하고 Steps에 결과를 기록한다.

`Repository secret → Frontend build Job → 기존 build argument → Next.js 공개 환경값 → 지도 SDK` 흐름으로 전달한다. Backend와 AI build Job에는 이 키를 공급하지 않는다.

## 5. 영향과 제한

Variables에만 키가 있는 저장소는 같은 이름의 Repository secret 등록이 필요하다. Secret이 없는 main 게시를 차단하는 동작과 수동 build의 빈 키 허용은 유지한다.

Secrets는 GitHub 저장·로그 보호를 위한 것이다. 기존 build argument와 브라우저 SDK에 값이 전달되는 구조이므로 빌드 산출물·브라우저에서 키를 완전히 숨기지 않는다. Kakao JavaScript SDK 허용 도메인은 별도로 설정해야 한다.

## 6. 검증 계획

- Ruby/Psych로 Release YAML 파싱
- 추출한 shell의 `bash -n`, inline Python AST 파싱
- 실제 키 없이 sentinel로 Frontend 게시의 키 유무, 다른 서비스와 수동 실행의 입력 검사
- `git diff --check`, `git status --short`, 최종 diff 검토
- 원격 Actions와 GHCR 게시는 이번 단계에서 실행하지 않으며, 로컬 정적 검증으로 자동 마스킹 완료를 주장하지 않는다.

## 7. 후속 작업

사용자는 GitHub Repository secret을 등록하고 이 수정이 포함된 PR/Release를 실행한다. 과거 실행 재시도는 과거 workflow revision을 사용하므로 코드 수정 반영 여부를 확인한다. Docker build argument·artifact에 남는 키까지 줄이는 변경은 별도 범위로 검토한다.
