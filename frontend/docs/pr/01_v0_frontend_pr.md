## PR 제목

[feat] # v0 프론트엔드 MVP 대시보드 구현

## PR 기준 정보

- 기준 브랜치: `dev`
- 작업 브랜치: `chore/01-v0-frontend-create`
- 작업 범위: v0로 생성한 프론트엔드 화면을 로컬 프로젝트에 반영하고, Next.js 기반으로 실행 및 빌드 가능한 MVP 화면 구성
- 주요 검증 기준: 프론트엔드 화면 정상 출력, ESLint 검사 통과, 프로덕션 빌드 성공 여부 확인

## 작업 내용

- `frontend` 디렉터리에 Next.js 16 기반 프론트엔드 프로젝트를 추가했습니다.
- 지능형 도시 침수 관리 대시보드의 메인 화면을 구현했습니다.
    - 도시 배수 시설 위험도 지도 영역 추가
    - 위험 시설 목록 영역 추가
    - 선택된 배수 시설의 상세 요약 패널 추가
    - 위험도 기준 정렬 및 선택 상태 표시 기능 추가
- 배수 시설 상세 페이지를 구현했습니다.
    - `/drains/[id]` 동적 라우트 추가
    - CCTV 스냅샷 카드 추가
    - 위치 지도 카드 추가
    - 센서 데이터 추세 차트 추가
    - 현재 위험 상태 카드 추가
    - 시설 정보 및 현재 상태 카드 추가
    - 최근 7일 위험 이력 카드 추가
- 프론트엔드 화면 구성을 위한 공통 컴포넌트를 추가했습니다.
    - `AppHeader`: 상단 헤더, 메뉴, 알림, 사용자 아이콘 영역
    - `RiskMap`: 배수 시설 위치와 위험도 마커를 표시하는 임시 지도 컴포넌트
    - `DrainRiskList`: 위험 시설 목록 및 정렬 UI
    - `DrainSummaryPanel`: 선택 시설 요약 정보 패널
    - `CctvSnapshotCard`: CCTV 이미지 및 썸네일 전환 UI
    - `SensorTrendChart`: 24시간 및 7일 센서 추세 차트
    - `StatusBadge`, `MetricProgress`: 상태 표시와 수치 진행률 표시 공통 컴포넌트
- UI 구현에 필요한 기본 UI 컴포넌트를 추가했습니다.
    - `badge`
    - `button`
    - `card`
    - `progress`
    - `select`
    - `separator`
    - `tooltip`
- 임시 데이터 레이어를 추가했습니다.
    - 배수 시설 목록 데이터
    - 위험 상태 메타 정보
    - 위험도 정렬 로직
    - 센서 추세 데이터 생성 함수
    - 위험 이력 데이터
    - 센서 임계값 및 요약 데이터
- 전역 스타일과 디자인 토큰을 추가했습니다.
    - Tailwind CSS 4 설정
    - shadcn 스타일 import
    - light/dark color token 정의
    - Geist 폰트 적용
- 프론트엔드 실행에 필요한 설정 파일을 추가했습니다.
    - `package.json`
    - `pnpm-lock.yaml`
    - `pnpm-workspace.yaml`
    - `eslint.config.mjs`
    - `next.config.mjs`
    - `postcss.config.mjs`
    - `tsconfig.json`
    - `components.json`
- ESLint 검증 환경을 추가했습니다.
    - `eslint` 9.x 의존성 추가
    - `eslint-config-next` 의존성 추가
    - Next.js core web vitals 기준 ESLint flat config 추가
    - `.next`, `out`, `build`, `next-env.d.ts`는 lint 대상에서 제외
- 정적 이미지 리소스를 추가했습니다.
    - CCTV 스냅샷용 이미지
    - favicon 및 앱 아이콘
    - placeholder 이미지
- 기존 개발 문서와 와이어프레임 참고 이미지를 함께 추가했습니다.
    - 프로젝트 정의서
    - 페르소나 및 시나리오
    - 요구사항 정의서
    - MVP 범위
    - 와이어프레임
    - 시스템 아키텍처
    - ERD
    - 기술 스택 선정 근거
    - YOLO/XGBoost PoC 문서
    - 역할 분담, 일정, 발표 목차

## 주요 화면 구성

### 메인 대시보드

- 경로: `/`
- 도시 배수 시설의 위험도를 한 화면에서 확인할 수 있도록 지도, 위험 시설 목록, 상세 요약 패널을 3개 영역으로 구성했습니다.
- 지도 마커를 클릭하면 선택된 배수 시설이 변경되고, 목록과 상세 패널이 선택 상태에 맞춰 갱신됩니다.
- 위험도 상태는 `위험`, `주의`, `정상`, `판단불가`로 구분할 수 있도록 색상과 배지를 적용했습니다.
- 위험 시설 목록은 위험도순, 최신순, 시설 ID순으로 정렬할 수 있도록 구성했습니다.

### 배수 시설 상세 페이지

- 경로: `/drains/[id]`
- 메인 대시보드에서 선택한 배수 시설의 상세 정보를 확인할 수 있도록 동적 라우트를 추가했습니다.
- CCTV 스냅샷, 위치 지도, 센서 추세, 현재 위험 상태, 시설 정보, 과거 위험 이력을 분리된 카드 형태로 배치했습니다.
- 센서 추세 차트는 24시간 보기와 7일 보기 전환을 지원합니다.
- 24시간 보기에서는 임시 실시간 갱신 효과를 적용해 관제 대시보드 형태를 확인할 수 있도록 구성했습니다.

## 변경 파일 요약

- `frontend/app/page.tsx`: 메인 대시보드 화면 추가
- `frontend/app/drains/[id]/page.tsx`: 배수 시설 상세 페이지 추가
- `frontend/app/layout.tsx`: 메타데이터, 폰트, 전역 레이아웃 설정 추가
- `frontend/app/globals.css`: Tailwind CSS, shadcn, 전역 디자인 토큰 추가
- `frontend/components/*`: 대시보드와 상세 화면에서 사용하는 컴포넌트 추가
- `frontend/components/ui/*`: 기본 UI 컴포넌트 추가
- `frontend/lib/mock-data.ts`: 화면 확인용 임시 데이터 및 유틸 함수 추가
- `frontend/lib/utils.ts`: className 병합 유틸 추가
- `frontend/public/*`: 화면 출력에 필요한 정적 이미지와 아이콘 추가
- `frontend/package.json`: 프론트엔드 실행, 빌드, 린트 스크립트와 의존성 추가
- `frontend/pnpm-lock.yaml`: pnpm 기준 의존성 lock 파일 추가
- `frontend/pnpm-workspace.yaml`: pnpm 허용 빌드 패키지 설정 추가
- `frontend/eslint.config.mjs`: Next.js ESLint flat config 추가
- `docs/*`: 프로젝트 개발 문서와 참고 이미지 추가

## 스크린샷 / 테스트 결과

- 로컬 개발 서버 실행 후 프론트엔드 화면 출력 확인을 진행했습니다.
    - 실행 명령어: `pnpm dev`
    - 확인 URL: `http://localhost:3000`
    - 확인 내용: 메인 대시보드 화면 출력, 지도 마커 선택, 위험 시설 목록 선택, 상세 페이지 이동 흐름 확인
- ESLint 검증을 완료했습니다.
    - 실행 명령어: `npm run lint`
    - 결과: 성공
    - 확인 내용: ESLint error 없음
    - 참고 사항: Next.js `@next/next/no-img-element` 경고 3건 확인
        - `frontend/components/cctv-snapshot-card.tsx`의 CCTV 이미지 태그 2건
        - `frontend/components/drain-summary-panel.tsx`의 CCTV 이미지 태그 1건
        - 현재는 v0 기반 MVP 화면 검증 단계이므로 경고로만 기록하고, 이미지 최적화가 필요한 시점에 `next/image` 전환을 검토합니다.
- 프로덕션 빌드 검증을 완료했습니다.
    - 실행 명령어: `npm run build`
    - 결과: 성공
    - 확인된 라우트:
        - `/`
        - `/_not-found`
        - `/drains/[id]`

## 비고

- 현재 프론트엔드 데이터는 실제 API 연동 전 화면 검증을 위한 mock 데이터입니다.
- `RiskMap`은 실제 지도 SDK 연동 전 화면 흐름을 확인하기 위한 임시 지도 컴포넌트입니다. 추후 Kakao Maps, Naver Maps, Mapbox 등 실제 지도 SDK로 교체할 수 있도록 `drains`, `selectedId`, `onSelect` 기반 props 구조로 작성했습니다.
- `next.config.mjs`에서 `typescript.ignoreBuildErrors`가 `true`로 설정되어 있어 프로덕션 빌드 시 타입 검증을 건너뜁니다. 추후 실제 API 연동 및 타입 정리가 완료되면 타입 검증을 활성화하는 것이 좋습니다.
- 현재 ESLint 검증은 통과하지만, `<img>` 사용으로 인한 Next.js 이미지 최적화 경고가 3건 남아 있습니다.
- v0 생성 결과를 기준으로 MVP 화면을 먼저 확인하는 단계이므로, 실제 백엔드 API, 인증, 알림, 지도 SDK, 실시간 센서 데이터 연동은 후속 작업으로 분리하는 것이 적절합니다.
