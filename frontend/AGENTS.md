# SmartDrain Frontend Guidelines

이 파일은 `frontend/` 내부 작업에 적용됩니다.

루트 `AGENTS.md`의 공통 규칙을 함께 적용합니다.

## 1. Frontend 책임

Frontend는 다음 책임을 가집니다.

- Next.js 관리자 대시보드
- 지도와 시설 마커
- 위험 시설 목록
- 하수구 상세 화면
- 이미지 및 센서 데이터 표현
- 위험 상태 시각화
- REST API 호출
- WebSocket 상태 갱신
- 사용자 입력과 화면 상태 관리

Frontend는 DB에 직접 접근하지 않습니다.

AI Service를 브라우저에서 직접 호출하지 않고 Backend API를 통해 통신합니다.

## 2. 기술 기준

기존 프로젝트 설정을 우선하며 기본 기술은 다음과 같습니다.

- Next.js App Router
- React
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- pnpm

작업 전 `frontend/package.json`과 실제 디렉터리 구조를 확인합니다.

## 3. 작업 범위

사용자가 별도로 요청하지 않는 한 `frontend/` 밖의 파일을 수정하지 않습니다.

Backend 또는 AI Service 변경이 필요해 보이면 직접 수정하지 않고 다음 내용을 보고합니다.

- 필요한 계약 변경
- 예상 대상 파일
- Frontend에 미치는 영향
- 호환성 위험

## 4. 컴포넌트 규칙

- React 함수형 컴포넌트를 사용합니다.
- 컴포넌트 파일 이름은 lowercase kebab-case를 사용합니다.
- 컴포넌트와 export 이름은 PascalCase를 사용합니다.
- 기존 `components/ui/` primitive를 우선 재사용합니다.
- 페이지 컴포넌트에 지나치게 많은 책임을 넣지 않습니다.
- 화면 표현과 API 데이터 변환 책임을 가능한 한 분리합니다.
- 공통화는 실제 중복과 재사용 근거가 있을 때만 수행합니다.
- 단일 사용만 예상되는 작은 코드를 성급하게 추상화하지 않습니다.

## 5. 상태 관리

서버 상태와 클라이언트 UI 상태를 구분합니다.

서버에서 가져오는 데이터는 기존 TanStack Query 패턴을 우선 사용합니다.

다음 항목을 먼저 확인합니다.

- 기존 query key
- query function
- stale time
- refetch 정책
- loading과 error 처리
- 캐시 갱신 방식
- WebSocket 수신 후 query cache 반영 방식

불필요한 전역 상태를 추가하지 않습니다.

`useEffect`는 외부 시스템 동기화가 필요한 경우에 사용하며, 계산 가능한 값을 동기화하기 위한 용도로 남용하지 않습니다.

## 6. API 및 데이터 변환

- 기존 API DTO와 adapter 패턴을 우선 사용합니다.
- API 응답을 여러 화면에서 반복 가공하지 않습니다.
- API DTO와 UI 전용 타입을 구분합니다.
- 화면 컴포넌트 안에 복잡한 데이터 변환 로직을 직접 작성하지 않습니다.
- 날짜, 위험 상태, 센서 단위의 변환 기준을 일관되게 유지합니다.
- nullable 데이터와 API 오류 상태를 명시적으로 처리합니다.

REST, WebSocket 또는 callback 계약을 임의로 변경하지 않습니다.

계약 변경이 필요하면 producer와 consumer 양쪽 영향을 보고합니다.

## 7. API Base URL

same-origin 배포에서는 API base URL을 비워 두는 방식을 우선합니다.

Frontend가 Backend를 직접 호출하는 로컬 개발 환경에서만 다음 환경변수를 사용합니다.

```text
NEXT_PUBLIC_API_BASE_URL
```

브라우저에 노출되면 안 되는 값을 `NEXT_PUBLIC_` 환경변수에 넣지 않습니다.

## 8. 이미지 및 비동기 상태

시설이나 이미지 대상이 변경될 때 이전 대상의 데이터가 잘못 노출되지 않도록 확인합니다.

다음 상태를 구분합니다.

- 최초 로딩
- 대상 변경 중 로딩
- 데이터 없음
- API 오류
- 이미지 로딩 실패
- 최신 데이터 수신 전 기존 캐시
- WebSocket 재연결 중 상태

임시로 로딩 시간을 늘리는 방식으로 상태 전환 문제를 숨기지 않습니다.

## 9. 스타일링

- Tailwind CSS와 기존 디자인 토큰을 우선 사용합니다.
- 기존 레이아웃과 색상 체계를 유지합니다.
- 인라인 스타일과 임의의 색상값 추가를 최소화합니다.
- 반응형 화면에서 텍스트 겹침과 overflow를 확인합니다.
- 로딩, 오류, 빈 상태에 대한 시각적 피드백을 제공합니다.
- 접근 가능한 버튼, label, alt text를 사용합니다.

## 10. 검증

검증 기준은 `docs/reference/verification-guide.md`를 우선 확인합니다.

작업 전 `frontend/package.json`의 scripts를 확인합니다.

영향 범위에 따라 다음 검증을 실행합니다.

```bash
cd frontend
pnpm lint
pnpm exec tsc --noEmit
pnpm build
```

현재 `package.json`에는 `lint`, `build`, `dev`, `start` script가 있으며, TypeScript 검사는 script가 아니라 `pnpm exec tsc --noEmit`으로 직접 실행합니다.

저장소에 실제 구성된 테스트가 있다면 관련 테스트를 함께 실행합니다.

다음 원칙을 지킵니다.

- 타입 검사를 우회하지 않습니다.
- 빌드 오류를 숨기는 설정을 추가하지 않습니다.
- 검증 도구가 없으면 임의로 추가하지 않고 사용자 승인을 받습니다.
- 실행하지 못한 검증은 이유를 최종 보고에 작성합니다.
- 기존 오류와 이번 변경으로 발생한 오류를 가능한 범위에서 구분합니다.
