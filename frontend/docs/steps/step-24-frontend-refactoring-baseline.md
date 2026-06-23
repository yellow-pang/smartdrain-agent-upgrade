# 24 프론트엔드 리팩터링 기준선 확보 결과

## 작업 목표

`refactor/frontend-component-performance-security` 브랜치에서 컴포넌트화·보안·성능 리팩터링을 시작하기 전에 현재 동작과 정적 검증 결과를 기준선으로 기록했다. 이 단계에서는 애플리케이션 코드를 수정하지 않았다.

## 확인한 대시보드 데이터 흐름

```text
GET /api/drains
  -> useDrainsQuery()
  -> drainListDtoToFacilities()
  -> TanStack Query cache
  -> DashboardPage: 위험도 정렬·선택 시설 계산
  -> 지도 / 위험 목록 / 모바일 요약 / 데스크톱 상세 패널

선택 이벤트
  -> useDrainStore.selectDrain()
  -> selectedDrainId 변경
  -> DashboardPage가 선택 시설과 표시 위치를 동기화

WebSocket 상태 이벤트
  -> RealtimeDrainSync
  -> Query cache의 목록·상세 데이터 병합
  -> Zustand의 이벤트·연결 상태 갱신
  -> 지도 / 목록 / 상세 화면 재렌더링
```

## 기준선 확인 결과

| 구분 | 결과 | 다음 단계에서 유지할 사항 |
| --- | --- | --- |
| 시설 목록 | `useDrainsQuery()`가 목록을 가져오고 adapter가 UI용 `DrainFacility`로 변환한다. | route 또는 표시 컴포넌트가 API DTO를 직접 처리하지 않는다. |
| 대시보드 선택 | `selectedDrainId`는 Zustand에 있고, 목록에 없는 선택 ID는 첫 시설 또는 `null`로 보정한다. | 선택 ID 보정과 `selectDrain` 호출의 소유자를 한 container에 유지한다. |
| 요약 데이터 | `useDashboardSummaryQuery()`는 목록과 독립적으로 로딩·오류·재시도 상태를 가진다. | 요약 바 추출 후에도 재시도 시 두 query가 함께 refetch된다. |
| 실시간 갱신 | `RealtimeDrainSync`가 WebSocket 이벤트를 TanStack Query cache와 Zustand에 반영한다. | 대시보드 표시 컴포넌트가 별도 socket을 열거나 cache를 직접 변경하지 않는다. |
| 위험도 표현 | `good/caution/danger/unknown`이 지도·목록·상세에 공통으로 사용된다. | 상태 의미와 색상 체계를 변경하지 않는다. |
| route 성격 | `app/page.tsx`는 data 조합, 선택 동기화, 요약/로딩/오류/모바일 표시, 레이아웃을 함께 맡는다. | 1단계에서는 이 파일의 표시 영역만 추출하고 query·store 경계는 유지한다. |

## 정적 검증

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건, 경고 1건 |
| `pnpm.cmd build` | 통과 | Next.js 16.2.6 production build 성공. `/` 정적 생성, `/drains/[id]` 동적 렌더링 확인 |
| `git diff --check` | 다음 단계 완료 시 재실행 예정 | 이 단계에서 애플리케이션 코드 변경 없음 |

### lint 경고

`components/fallback-image.tsx:23`에서 `<img>` 사용에 대한 `@next/next/no-img-element` 경고가 1건 있다. 이는 현재 기준선의 기존 경고이며, 이미지 최적화 정책과 외부 이미지 URL 처리 방식을 함께 검토할 4~5단계 후보로 기록한다. 이번 기준선 단계에서는 동작 변경을 피하기 위해 수정하지 않았다.

### 검증 환경 비고

PowerShell 실행 정책으로 `pnpm` 스크립트 래퍼는 실행되지 않아 `pnpm.cmd`를 사용했다. 또한 샌드박스에서 설치된 ESLint 의존성 파일 읽기가 제한되어 검증 명령은 권한 승인 후 실행했다. 두 명령 모두 실제 프로젝트 의존성으로 정상 완료됐다.

## 수동 확인 범위와 남은 리스크

개발 서버를 실행한 브라우저 수동 점검은 이번 단계에서 수행하지 않았다. 다음 단계의 코드 변경 후 아래 시나리오를 대시보드와 상세 화면에서 확인한다.

1. 지도와 위험 목록에서 시설을 선택했을 때 같은 시설이 강조되고 상세 정보가 바뀌는지 확인한다.
2. 목록 재조회 또는 WebSocket 이벤트 뒤 선택 시설이 유효하게 유지되거나 안전한 fallback으로 전환되는지 확인한다.
3. 양호·주의·위험·판단불가, 로딩·오류·빈 상태가 기존처럼 표시되는지 확인한다.
4. 360px, 768px, 1280px에서 지도·목록·모바일 요약·데스크톱 상세 패널의 배치가 유지되는지 확인한다.

## 다음 단계

1단계에서는 `app/page.tsx`의 요약 바, 요약 loading/error 상태, 모바일 선택 시설 요약, 대시보드 레이아웃 표시를 dashboard 컴포넌트로 추출한다. `useDrainsQuery`, `useDashboardSummaryQuery`, `useDrainStore`, 선택 ID 보정, WebSocket 갱신 흐름은 route/container에 유지한다.
