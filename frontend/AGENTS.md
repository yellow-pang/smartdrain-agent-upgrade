# SmartDrain Frontend Codex Guidelines

SmartDrain frontend 작업을 위한 Codex 전용 기준 문서입니다. 이 문서는 길게 설명하기보다, 작업 중 먼저 확인해야 할 문서와 수정 범위, 승인 기준, 검증 기준을 정리합니다.

This AGENTS.md applies only to the frontend directory. Do not modify files outside the frontend directory unless the user explicitly asks.

Root-level docs may be read for project direction, requirements, architecture, and planning context, but they must not be modified unless the user explicitly asks.

## 프로젝트 기준

- SmartDrain은 지능형 도시 침수 관리 및 모니터링 시스템입니다.
- frontend의 목적은 관리자가 도시 빗물받이와 배수구 상태를 쉽게 확인할 수 있는 화면을 제공하는 것입니다.
- 현재 frontend는 Next.js App Router 기반입니다.
- 주요 화면과 UI는 메인 대시보드, 위험도 지도 UI, 배수구 상세 페이지, CCTV 분석 결과, 가상 센서 데이터, 실시간 변화 차트, 위험 시설 목록, 정상/주의/위험 상태 표시입니다.
- 위험도 상태 색상은 일관되게 사용합니다.
  - 정상: green 계열
  - 주의: yellow 또는 amber 계열
  - 위험: red 계열

## 작업 전 실제 구조 확인

작업을 시작하기 전에 실제 파일 구조와 `package.json`을 확인합니다. 문서와 실제 코드 또는 스크립트가 다르면, 실제 코드 기준으로 판단하고 차이를 사용자에게 짧게 보고합니다.

현재 기준 구조는 다음과 같습니다.

- `app/`: Next.js App Router 라우트
- `app/page.tsx`: 메인 대시보드
- `app/drains/[id]/page.tsx`: 배수구 상세 페이지
- `components/`: 재사용 React 컴포넌트
- `components/ui/`: shadcn 스타일 공통 UI primitive
- `lib/`: 유틸 함수, mock data, 공통 로직
- `public/`: 정적 이미지와 아이콘
- `docs/`: frontend 관련 작업 계획, Step 기록, PR 문서
- `docs/convention/`: frontend 코드 컨벤션과 문서화 규칙

## 작업 전 확인 문서

작은 수정은 필요한 코드와 가까운 문서만 확인할 수 있습니다. 중간 이상 작업은 필요한 범위에서 루트 개발 문서와 frontend convention 문서를 확인합니다.

루트 개발 문서는 `/frontend` 기준 `../docs/`에 있으며 읽기 전용 참고 자료입니다. 실제 파일명이 다를 수 있으므로 먼저 `../docs/` 목록을 확인하고, 존재하는 대표 개발 문서 10개를 기준으로 필요한 문서를 읽습니다.

대표 개발 문서는 다음과 같습니다. 단, 실제 파일명이 다를 수 있으므로 작업 전 `../docs/` 목록을 먼저 확인합니다.

1. `../docs/01_프로젝트정의서.md`
2. `../docs/02_페르소나_및_시나리오.md`
3. `../docs/03_요구사항정의서.md`
4. `../docs/04_MVP범위.md`
5. `../docs/05_와이어프레임.md`
6. `../docs/06_시스템아키텍처.md`
7. `../docs/07_ERD.md`
8. `../docs/08_기술스택선정근거.md`
9. `../docs/09_YOLO_XGBoost_PoC.md`
10. `../docs/10_역할분담_일정_발표목차.md`

frontend convention 문서는 다음 기준으로 확인합니다.

- 코드 작성, 리팩터링, 네이밍, 컴포넌트 분리 작업: `docs/convention/code-convention.md`
- plan, step, PR 문서 작성 또는 갱신 작업: `docs/convention/documentation-convention.md`

`docs/plans`, `docs/steps`, `docs/pr`에 기존 문서가 있으면 번호가 가장 큰 최신 문서를 우선 확인합니다.

## Codex 작업 흐름

1. 사용자의 요구사항과 최종 목표를 짧게 요약합니다.
2. 작업이 `/frontend` 내부 작업인지 확인합니다.
3. `git status`로 브랜치와 미커밋 변경을 확인합니다.
4. 관련 루트 개발 문서와 frontend convention 문서를 확인합니다.
5. 요청 범위를 분석해서 작은 작업, 중간 작업, 큰 작업으로 분류합니다.
6. 작업 범위와 추천 브랜치명을 사용자에게 제안합니다.
7. 중간 이상 작업이면 코드 수정 전에 `docs/plans/plan-XX-작업명.md` 문서를 작성하거나 갱신합니다.
8. 사용자 승인 후 코드 수정을 진행합니다.
9. 가능한 검증 명령어를 실행합니다.
10. 구현 후 필요한 범위에서 `docs/steps/step-XX-작업명.md` 또는 `docs/pr/pr-XX-작업명.md`를 작성합니다.
11. 변경 요약, 검증 결과, 남은 리스크, 한글 Conventional Commit 메시지를 제안합니다.

작업이 명확한 작은 수정이면 plan 문서 없이 진행할 수 있습니다. 요청이 모호하거나 넓으면 바로 코드를 수정하지 않고 적절한 작업 범위를 먼저 추천합니다.

## 작업 범위 추천 기준

- "대시보드 개선" 요청은 지도, 차트, 위험 목록, 상세 페이지 중 어떤 범위를 다룰지 나눠서 제안합니다.
- "실시간 데이터 표시" 요청은 UI 표시, mock data 구조, 차트 갱신 흐름, API 연동 준비 범위를 나눠서 제안합니다.
- "디자인 수정" 요청은 색상 체계, 카드 구조, 레이아웃, 모바일 대응 범위를 나눠서 제안합니다.
- "코드 정리" 요청은 네이밍, 중복 제거, 컴포넌트 분리, 성능 개선, 문서화 중 어떤 범위인지 제안합니다.

Codex는 사용자가 승인한 브랜치와 작업 범위 안에서만 수정합니다.

## 작업 규모 기준

작은 수정:

- 오타, UI 문구 수정, 단순 CSS 수정
- 명백한 lint 오류
- 단일 파일의 작은 버그
- 작은 네이밍 개선

중간 작업:

- 컴포넌트 구조 변경
- 대시보드, 지도, 차트 UI 변경
- mock data 구조 변경
- 상세 페이지 정보 구조 변경
- 여러 파일에 걸친 UI 변경
- convention 문서 추가 또는 갱신
- 중복 코드 제거
- 함수 또는 컴포넌트 분리
- 의미 있는 네이밍 정리

큰 작업:

- 새 패키지 추가
- 라우팅 구조 변경
- 폴더 구조 대규모 변경
- API 연동 방식 변경
- 상태 관리 라이브러리 도입
- 지도 라이브러리 또는 차트 라이브러리 교체
- 전체 디자인 시스템 변경
- `/frontend` 밖의 파일 변경
- 루트 `/docs` 개발 문서 수정
- 앱 전체 구조에 영향을 주는 대규모 리팩터링

큰 작업은 반드시 사용자 승인 후 진행합니다.

## 코드 작업 규칙

- TypeScript와 React 함수형 컴포넌트를 사용합니다.
- 기존 4칸 들여쓰기 스타일을 따릅니다.
- 컴포넌트 파일은 `risk-map.tsx`, `sensor-trend-chart.tsx`처럼 lowercase kebab-case를 사용합니다.
- 컴포넌트 export 이름은 PascalCase를 사용합니다.
- 공통 helper는 `lib/`에 둡니다.
- root-relative import가 읽기 쉬울 때는 `@/*` alias를 사용합니다.
- Tailwind CSS 유틸리티와 `components/ui/`의 shadcn 스타일 primitive를 우선 사용합니다.
- 기능 변경과 전체 포맷팅을 한 작업에 섞지 않습니다.
- 불필요한 리팩터링을 하지 않습니다.
- mock data와 실제 API 데이터는 역할이 섞이지 않도록 구분합니다.
- UI 변경 시 모바일부터 데스크톱까지 레이아웃과 텍스트 겹침을 확인합니다.

## 수정 전 사용자 확인이 필요한 항목

다음 항목은 반드시 사용자에게 확인한 뒤 진행합니다.

- `/frontend` 밖의 파일 수정
- 루트 `/docs` 개발 문서 수정
- 새 패키지 설치
- `package.json` 또는 lockfile 변경
- 라우팅 구조 변경
- 폴더 구조 대규모 변경
- 상태 관리 방식 변경
- 지도/차트 라이브러리 교체
- API 연동 방식 변경
- 환경변수 추가 또는 변경
- 기존 mock data 대규모 교체
- UI 전체 디자인 방향 변경
- 대규모 리팩터링
- 성능 최적화를 이유로 코드 가독성을 크게 떨어뜨리는 변경

실제 `git commit`, `git push`는 사용자가 직접 진행합니다.

## 문서 작성 규칙

- 계획 문서는 `docs/plans/plan-XX-작업명.md`에 작성합니다.
- 작업 완료 문서는 `docs/steps/step-XX-작업명.md`에 작성합니다.
- PR 요약 문서는 `docs/pr/pr-XX-작업명.md`에 작성합니다.
- 문서를 작성하기 전에 `docs/convention/documentation-convention.md`를 확인합니다.
- 기존 문서가 있으면 번호가 가장 큰 최신 문서의 흐름을 참고합니다.
- 문서는 기본적으로 한국어로 작성합니다.
- 변경 전/후, 검증 결과, 남은 리스크를 구분해서 기록합니다.
- 한글 문서는 UTF-8 인코딩을 유지합니다.

## 검증 기준

검증 전 `package.json`의 scripts를 확인하고 실제 스크립트 기준으로 실행합니다. 주요 검증 명령어는 다음과 같습니다. 단, 실행 전 `package.json`의 scripts를 먼저 확인합니다.

- `pnpm lint`: ESLint 실행
- `pnpm build`: production build와 framework check 실행
- `pnpm dev`: 개발 서버에서 주요 화면 수동 확인

검증 실패 시 다음을 구분해서 보고합니다.

- 실패한 명령어
- 핵심 원인
- 수정한 내용
- 남은 문제
- 사용자가 추가로 확인해야 할 사항

검증을 실행하지 못한 경우에는 이유와 남은 리스크를 명확히 적습니다.

## 커뮤니케이션 규칙

- 답변은 기본적으로 한국어로 작성합니다.
- 초보 개발자가 이어서 작업할 수 있도록 용어를 풀어서 설명합니다.
- 작업 전 요구사항을 짧게 요약합니다.
- 변경 범위가 `/frontend` 내부인지 먼저 확인합니다.
- 코드 수정 전 어떤 문서를 읽었는지 요약합니다.
- 애매한 요구사항은 추측하지 말고 확인 질문을 합니다.
- 작은 UI 문구 수정이나 명백한 오류 수정은 합리적으로 진행할 수 있습니다.
- 성능 개선이나 리팩터링을 한 경우, 왜 필요한지와 어떤 효과가 있는지 설명합니다.
- 마지막에는 변경 요약, 검증 결과, 남은 리스크, 한글 Conventional Commit 메시지를 제안합니다.
- 실제 `git commit`, `git push`는 사용자가 직접 진행합니다.

## 커밋 메시지 예시

제목:

`docs: 프론트엔드 Codex 작업 규칙 정리`

내용:

- SmartDrain frontend 작업 범위와 승인 기준을 정리한다.
- 루트 개발 문서와 frontend convention 문서 확인 흐름을 추가한다.
- 검증 기준과 한글 Conventional Commit 메시지 제안 규칙을 문서화한다.
