# 28 Frontend 보안·성능·유지보수성 강화 계획

## 1. 작업 개요

| 항목        | 내용                                                                                                                                            |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 작업 브랜치 | `refactor/frontend-security-performance-hardening`                                                                                              |
| 작업 규모   | 큰 작업 — React/Next.js의 신뢰 경계, 렌더링, 번들, 예외 처리, 코드 책임을 측정 근거로 점검한다.                                                 |
| 최종 목표   | 현재 MVP의 UI·API·WebSocket 동작을 유지하면서, 발표·운영에 영향을 주는 보안·정확성·성능 문제만 최소 범위로 개선한다.                            |
| 기본 원칙   | 현황 측정 → 문제 분류 → 변경 후보 제시 → 사용자 승인 → 최소 변경 → 동일 조건 재검증. 근거가 없으면 `NO_CHANGE`로 기록한다.                      |
| 작업 범위   | `/frontend` 내부 코드와 frontend 계획·완료·PR 문서                                                                                              |
| 제외 범위   | Backend·AI·DB schema·API/WebSocket 계약 변경, 상태 관리 교체, 라우팅 재설계, 지도/차트 교체, 패키지 대규모 업데이트, 루트 문서·인프라 파일 수정 |

## 2. 기존 개선 사항과 유지 기준

이미 완료된 Step을 기준으로 아래 구조는 기본적으로 다시 바꾸지 않는다.

| 기존 기록           | 확인된 방향                                     | 이번 작업에서 유지할 기준                                                        |
| ------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------- |
| `step-24`~`step-30` | route·표시 컴포넌트 분리                        | query·선택 상태·WebSocket 병합 책임을 표시 컴포넌트로 다시 섞지 않는다.          |
| `step-31`           | 시설 ID 인코딩과 이미지 URL allowlist           | URL 입력 경계는 유지하고, API 계약을 임의로 바꾸지 않는다.                       |
| `step-32`           | 지도·CCTV의 선택적 memoization                  | 실제 비교 근거 없이 `memo`·`useMemo`·`useCallback`을 추가하거나 제거하지 않는다. |
| `step-33`~`step-37` | 이미지 URL 정책·WebSocket 검증·차트/이미지 점검 | 이미지 도메인, WebSocket 계약, 차트 동작을 회귀시키지 않는다.                    |
| `step-39`~`step-40` | 모바일 UX·다크 모드 대비                        | 성능 변경 후에도 모바일 흐름·상태 색상·다크 모드 가독성을 유지한다.              |

## 3. 현재 진단 출발점

| ID   | 위치                                                | 분류                         | 현재 확인 결과                                                                       | 실제 영향                                                  | 우선순위 |
| ---- | --------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------- | -------- |
| F-01 | `app/page.tsx`, `app/drains/[id]/page.tsx`          | CLIENT_BOUNDARY              | route 전체가 client component이며 query·WebSocket·이벤트가 존재한다.                 | 필요 이상의 client boundary인지 번들 측정 필요             | P2       |
| F-02 | `components/risk-map.tsx`, `sensor-trend-chart.tsx` | PERFORMANCE_SPACE / TIME     | 지도·차트 라이브러리는 무거울 수 있으나 첫 화면/상세 핵심 UI다.                      | bundle 측정 전 dynamic import 적용 금지                    | P2       |
| F-03 | `components/fallback-image.tsx`                     | PERFORMANCE_SPACE / SECURITY | 일반 `<img>`를 사용하며 URL allowlist는 이미 적용돼 있다.                            | Next 경고 1건. remote image 정책·레이아웃 안정성 확인 필요 | P1       |
| F-04 | `app/layout.tsx`                                    | SECURITY                     | `dangerouslySetInnerHTML`은 정적 테마 초기화 스크립트에 한정된다.                    | 외부 입력 삽입 여부·CSP 호환성 확인 필요                   | P1       |
| F-05 | `lib/api/*`, `lib/websocket/*`                      | NETWORK / CORRECTNESS        | TypeScript DTO는 있으나 API·WebSocket payload의 런타임 검증 범위는 별도 확인 필요다. | 예기치 않은 payload가 화면 오류로 이어질 수 있음           | P1       |
| F-06 | `app/drains/[id]/page.tsx`의 Effect·이벤트 병합     | EFFECT / STATE               | 상세 WebSocket 병합과 요청 순서 보호가 존재한다.                                     | cleanup·의존성·중복 갱신을 실제 흐름으로 점검              | P1       |
| F-07 | `components/drain-risk-list.tsx`                    | PERFORMANCE_TIME             | 정렬과 항목 memoization이 이미 있다.                                                 | 실제 목록 크기·Profiler 근거 없이 virtualization 도입 금지 | P3       |
| F-08 | `package.json`                                      | DEPENDENCY                   | React 19·Next 16·TanStack Query·Zustand·지도·차트 라이브러리가 이미 있다.            | 사용하지 않는 의존성은 import·실행 경로 확인 뒤에만 후보화 | P3       |

위 항목은 수정 목록이 아니다. 실제 측정과 코드 추적으로 재확인한 뒤 `수정`, `추가 측정`, `NO_CHANGE`, `발표 후`로 결정한다.

## 4. 단계별 권장 진행 방향

### 1단계 — 기준선 측정과 보안 인벤토리

1. `lint`, `tsc --noEmit`, production build를 실행하고 기존 경고·실패를 분리 기록한다.
2. `NEXT_PUBLIC_*` 참조와 client component import 경로를 확인해 비밀값·서버 전용 값이 번들에 포함되지 않는지 점검한다.
3. `dangerouslySetInnerHTML`, 외부 URL, 이미지 URL, `window`/`localStorage`, API·WebSocket payload 진입점을 목록화한다.
4. React DevTools Profiler 또는 재현 가능한 수동 시나리오로 대시보드 선택·정렬·WebSocket 이벤트·상세 탭 전환의 render 비용을 측정한다.
5. bundle analyzer 도입 승인 시에만 지도·차트·Client Component의 실제 번들 크기를 기록한다.

### 2단계 — P0/P1 최소 수정

아래 조건이 실제로 확인된 경우에만 수정한다.

| 후보                | 수정 조건                                                         | 권장 최소 변경                                                               |
| ------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 환경변수 노출       | `NEXT_PUBLIC_*`에 secret·내부 token·비공개 URL이 포함된 사실 확인 | client 환경변수 참조 제거 또는 server 경계로 이동. API 계약 변경은 별도 승인 |
| XSS/URL 입력        | allowlist 우회·외부 입력의 HTML 삽입·안전하지 않은 redirect 확인  | 공통 URL/HTML 경계 helper 보강. 이미 정적 테마 스크립트인 경우 `NO_CHANGE`   |
| 런타임 payload 오류 | API·WebSocket의 누락/잘못된 값이 화면 예외를 재현                 | trust boundary에서 좁은 type guard 또는 schema 검증과 fallback 추가          |
| Effect/소켓 cleanup | 중복 listener, 재연결 뒤 중복 fetch, unmount 뒤 state 갱신을 재현 | 해당 Effect의 cleanup·dependency·요청 취소만 보정                            |
| 오류 화면           | API 실패·이미지 실패·지도 key 누락에서 빈 화면/조작 불가를 재현   | 기존 `PlaceholderState`/retry 패턴을 재사용해 최소 fallback 추가             |

### 3단계 — 측정된 성능·공간 최적화

| 후보                                   | 적용 조건                                                                           | 적용하지 않을 조건                                                         |
| -------------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `next/dynamic`으로 지도·차트 지연 로딩 | bundle 측정에서 초기 JS 비중이 크고, 해당 기능이 첫 화면 즉시 필요하지 않음         | 대시보드 지도·상세 핵심 차트의 첫 표시가 늦어져 UX가 나빠지는 경우         |
| 이미지 최적화                          | 실제 CCTV 이미지 크기·LCP·layout shift 문제가 확인되고 허용 도메인을 좁게 정의 가능 | 동적 외부 URL 정책을 넓게 열어야 하거나 fallback 신뢰 경계가 약해지는 경우 |
| 리스트 virtualization                  | 실제 시설 수와 Profiler에서 목록 렌더링이 병목임을 확인                             | 현재 MVP 수준의 짧은 목록, 키보드/선택 UX를 복잡하게 만드는 경우           |
| memoization 조정                       | Profiler로 반복 렌더 비용과 prop 안정성 필요성이 확인                               | “혹시 빠를 수 있음” 수준의 추측뿐인 경우                                   |
| 중복 코드 정리                         | 동일한 정책·표현이 3곳 이상 중복되고 공통화로 읽기 쉬워짐                           | 한두 곳만 쓰는 미래 대비 추상화인 경우                                     |

### 4단계 — 검증과 기록

- 변경 파일별 영향 경로와 전/후 측정 결과를 Step 문서에 기록한다.
- 대시보드 선택·지도·목록·모바일 요약·상세 직접 URL·WebSocket 갱신·이미지 fallback을 회귀 확인한다.
- lint, 타입 검사, build 및 가능한 수동 profiler 측정을 재실행한다.

## 5. 라이브러리 도입 판단

새 라이브러리는 기능 부족 또는 측정 결과가 명확할 때만 하나씩 도입한다. 패키지 설치·`package.json`·lockfile 변경은 별도 사용자 승인 후에만 수행한다.

| 라이브러리                | 추천 판단                                          | 도입 조건                                                                     | 현재 권장                                     |
| ------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------- |
| `zod`                     | API/WebSocket 런타임 경계 검증에 유용              | 실제 payload 누락·형식 오류를 재현했고 type guard보다 schema 공유가 명확할 때 | **조건부 추천**                               |
| `react-hook-form`         | 다단계·검증 많은 입력 폼의 상태/접근성 관리에 유용 | 설정·분석 요청·관리자 입력처럼 복잡한 폼을 새로 구현할 때                     | **현재 도입 보류** — 현 UI에 복잡한 폼이 없음 |
| `@next/bundle-analyzer`   | 번들 크기 측정에 유용한 dev 도구                   | 지도·차트 lazy loading 여부를 객관적으로 결정해야 할 때                       | **1순위 조건부 추천**                         |
| `@tanstack/react-virtual` | 대용량 목록 렌더링에 유용                          | 실제 시설 수가 크고 Profiler로 목록 병목이 확인될 때                          | **현재 도입 보류**                            |
| `dompurify`               | 사용자 제공 HTML을 렌더링할 때 XSS 방어에 유용     | 신뢰하지 않는 HTML을 표시해야 할 때                                           | **현재 도입 보류** — HTML 렌더링 기능이 없음  |
| `@sentry/nextjs`          | 운영 오류 추적에 유용                              | DSN·개인정보 마스킹·운영 대응 담당이 확정될 때                                | **발표 후 권장**                              |
| Playwright                | E2E 회귀 방지에 유용                               | 발표 일정 이후 핵심 시나리오 자동화 시간을 확보할 때                          | **발표 후 권장**                              |

## 6. 사용자 확인이 필요한 사항

| 확인 항목            | 추천 방향                                                      | 이유                                                                                       |
| -------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 1차 범위             | **진단·P0/P1 최소 수정부터**                                   | 현재 MVP가 동작하므로 측정 없는 구조 개편 위험을 피한다.                                   |
| bundle analyzer      | **`@next/bundle-analyzer` devDependency 도입 승인 후 사용**    | 지도·차트 lazy loading을 추측이 아닌 실제 bundle 수치로 결정한다.                          |
| Zod                  | **payload 오류가 재현된 경계에만 도입**                        | 전 DTO를 한 번에 schema화하면 범위와 bundle이 불필요하게 커진다.                           |
| React Hook Form      | **이번 범위에서는 도입하지 않음**                              | 현재 복잡한 폼이 없어 의존성·추상화만 늘어난다.                                            |
| 보안 헤더/CSP        | **Nginx·배포 환경과 함께 별도 승인 후 적용**                   | Kakao 지도·외부 이미지·inline theme script와 충돌할 수 있어 frontend 단독 변경이 위험하다. |
| 이미지 컴포넌트 전환 | **실제 이미지 크기·허용 도메인 확인 후 제한적으로 진행**       | 넓은 `remotePatterns`는 보안 정책을 약화시킬 수 있다.                                      |
| 패키지 정리          | **실제 import와 Docker/Jenkins 사용 여부 확인 후 후보만 제시** | 발표 직전 의존성 제거·lockfile 변경은 재현성을 깨뜨릴 수 있다.                             |
| 범위 밖 시스템       | **Backend·AI·DB·API/WebSocket 계약은 수정하지 않음**           | frontend 리팩터링이 통합 계약을 임의로 바꾸지 않게 한다.                                   |

## 7. 예상 변경 파일

실제 진단 결과와 승인에 따라 아래 파일 중 필요한 최소 집합만 변경한다.

| 목적                     | 예상 경로                                                                                                  |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| 기준선·후보 기록         | `docs/plans/plan-28-frontend-security-performance-hardening.md`                                            |
| API/이미지/URL 신뢰 경계 | `lib/api/*`, `lib/drain-route.ts`, `components/fallback-image.tsx`                                         |
| WebSocket/Effect 안정성  | `components/realtime-drain-sync.tsx`, `lib/websocket/drain-status-socket.ts`, `app/drains/[id]/page.tsx`   |
| 번들·Client boundary     | `app/page.tsx`, `app/drains/[id]/page.tsx`, `components/risk-map.tsx`, `components/sensor-trend-chart.tsx` |
| 설정·분석 도구           | `next.config.mjs`, `package.json`, lockfile — **별도 승인 시에만**                                         |
| 완료 기록                | `docs/steps/step-42-frontend-security-performance-hardening.md`                                            |
| PR 요약                  | `docs/pr/pr-33-frontend-security-performance-hardening.md`                                                 |

## 8. 검증 계획

| 검증      | 기준                                                                                    |
| --------- | --------------------------------------------------------------------------------------- |
| 정적 검사 | `pnpm lint`, `pnpm exec tsc --noEmit`, `pnpm build`                                     |
| 보안 경계 | 허용/차단 URL, 잘못된 시설 ID, 누락·잘못된 API/WS payload, 외부 입력 렌더링 여부 확인   |
| 성능 측정 | bundle analyzer 승인 시 결과 파일, Profiler 또는 동일 수동 시나리오의 전/후 render 기록 |
| 기능 회귀 | 대시보드·상세 직접 URL·로딩/오류·이미지 fallback·지도·차트·WebSocket 재연결·모바일 확인 |
| 의존성    | 추가/삭제 패키지마다 build와 Dockerfile pnpm install 재현 확인                          |

## 9. 승인 후 제안 커밋 메시지

제목:

```text
docs: frontend 보안·성능 리팩터링 계획을 추가
```

내용:

```text
- 측정 근거 기반의 보안·정확성·성능 개선 원칙을 정의한다.
- 기존 URL 경계와 실시간 렌더링 최적화의 유지 기준을 기록한다.
- 라이브러리 도입 조건과 사용자 승인 항목을 분리한다.
```

## 10. 2단계 번들 측정 결과

`@next/bundle-analyzer`를 devDependency로 추가하고, `ANALYZE=true`일 때만 분석 wrapper가 동작하도록 설정했다. 기본 Turbopack build에서는 이 플러그인이 리포트를 만들지 않으므로, 측정 전용으로 아래 명령을 사용했다.

```text
ANALYZE=true pnpm exec next build --webpack
```

| 측정 항목 | 결과 | 해석 |
| --- | --- | --- |
| Webpack client 공통 chunk | parsed 약 354KB, gzip 약 103KB | `recharts`, `react-kakao-maps-sdk`와 그 하위 의존성이 함께 포함된 가장 큰 client chunk다. |
| 대시보드 route 전용 chunk | parsed 약 29KB, gzip 약 7KB | 대시보드 자체 표시 코드 비중은 상대적으로 작다. |
| 상세 route 전용 chunk | parsed 약 31KB, gzip 약 8KB | 상세 표시 코드 비중은 상대적으로 작다. |
| 기본 Turbopack build | analyzer 리포트 미생성 | 현재 Next.js 16에서는 `@next/bundle-analyzer` 측정 시에만 Webpack flag가 필요하다. 기본 production build 설정은 바꾸지 않는다. |

### 측정 후 결정

- **추가 측정:** 지도와 차트가 공통 chunk를 키우는 사실은 확인됐지만, 실제 첫 화면 LCP·모바일 입력 지연·네트워크 속도 측정은 아직 없다.
- **NO_CHANGE:** 대시보드 지도는 핵심 첫 화면 기능이므로 이번 단계에서 지연 로딩하지 않는다.
- **다음 승인 필요:** 상세 화면의 차트만 제한적으로 dynamic import해 공통 chunk 분리를 시도할지 여부는, 실제 모바일 성능 측정과 기존 loading/fallback UX 검토 후 별도로 결정한다.
