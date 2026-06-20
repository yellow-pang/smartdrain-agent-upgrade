# 13 Dashboard UI Profiler Baseline 기록

## 1. 목적

UI 개선 전 기준선(Baseline) 렌더링 지표를 기록한다.

- 시나리오별 commit 수
- 주요 컴포넌트 렌더 횟수
- 선택 변경 시 목록 item 갱신 범위

## 2. 측정 환경

| 항목          | 값                                                          |
| ------------- | ----------------------------------------------------------- |
| 브랜치        | `refactor/dashboard-ui-responsiveness`                      |
| URL           | `http://localhost:3000/`                                    |
| 브라우저      | Chrome + React DevTools                                     |
| Profiler 옵션 | `Record why each component rendered while profiling` 활성화 |

## 3. 시나리오 정의

| 시나리오 | 동작                    |
| -------- | ----------------------- |
| A        | 지도 마커 1회 클릭      |
| B        | 위험 목록 item 1회 클릭 |
| C        | 지도 마커 3회 연속 클릭 |

## 4. Baseline 측정 표

| 시나리오 | Commit 수 | DashboardPage 렌더 횟수 | DrainRiskList 렌더 횟수 | 선택/직전 외 item 렌더 여부 | 비고                    |
| -------- | --------: | ----------------------: | ----------------------: | --------------------------- | ----------------------- |
| A        |         1 |                       1 |         관찰됨(약 10ms) | 있음                        | 전체 duration 약 26.8ms |
| B        |         1 |                       1 |        관찰됨(약 9.6ms) | 있음                        | 전체 duration 약 25.5ms |
| C        |         1 |                       1 |       관찰됨(약 16.7ms) | 있음                        | 전체 duration 약 33.5ms |

요약 판단:

- 사용자 동작 1회당 commit 1회로 측정되어 연속 commit 폭증은 보이지 않았다.
- Test C(마커 변경)에서 목록/상세/지도 갱신이 함께 일어나 A/B 대비 비용이 상대적으로 높았다.
- 단계 1~3에서 목록 item 경계와 선택 상태 전달 범위를 줄이는 개선이 유효하다.

## 5. 캡처 첨부 규칙

1. 파일명

- `baseline-A.png`
- `baseline-B.png`
- `baseline-C.png`

2. 저장 위치

- `frontend/docs/images/`

3. 문서 링크(캡처 후 업데이트)

- A: 사용자 첨부 예정
- B: 사용자 첨부 예정
- C: 사용자 첨부 예정

## 6. 측정 절차 체크리스트

1. Profiler `Clear`
2. `Record`
3. 시나리오 동작 수행
4. `Stop`
5. 최대 렌더 commit 선택
6. 표에 수치 입력
7. 캡처 저장 및 링크 반영

## 7. 다음 단계 진입 조건

다음 조건이 채워지면 단계 1(UI 개선 코드 변경)로 진행한다.

1. 시나리오 A/B/C 수치가 표에 입력됨
2. 캡처 3장이 `frontend/docs/images/`에 저장됨
3. 선택/직전 외 item 렌더 여부가 기록됨
4. 단계 1(UI 안정화) 코드 변경 착수 승인됨

## 8. 단계 종료 시 Git 확인 및 커밋 메시지 제안

이 단계 종료 시 아래 순서로 진행한다.

1. `git status -sb`로 미커밋 변경 파일 확인
2. 변경 파일별 핵심 diff 요약
3. 한글 커밋 메시지 제안

커밋 제목 템플릿:

- `docs: 대시보드 프로파일러 기준선 기록 정리`

커밋 본문 템플릿:

- 대시보드 UI 개선 전 Baseline 측정 목적과 범위를 문서화한다.
- 시나리오 A/B/C 기준 측정 표와 체크리스트를 추가한다.
- 사용자 캡처 저장 규칙과 다음 단계 진입 조건을 명시한다.

## 9. 현재 진행 현황 업데이트

이 문서는 Baseline 기록으로 시작했지만, 토큰 제한으로 작업 주체가 바뀌어도 바로 이어갈 수 있도록 현재 상태를 함께 정리한다.

1. 완료된 범위

- 단계 0: Baseline 측정 표 기록 완료
- 단계 1: 메인 대시보드의 모바일 높이, 텍스트 처리, 날짜 포맷, 상세 정보 우선순위 조정 완료
- 단계 2: 위험 목록 item 디자인 정리와 item 단위 memoization 적용 완료
- 단계 3: 선택 변경 시 콜백/렌더 경계 일부 안정화 완료
- 테마 기능: 시스템/라이트/다크 순환 토글과 초기 테마 동기화 오류 수정 완료

2. 최근에 반영된 주요 UI/구조 변경

- 모바일/태블릿에서는 고정 바텀시트 대신 인라인 요약 카드로 상세 정보를 노출한다.
- 데스크톱 상세 패널은 큰 화면에서만 유지한다.
- 헤더는 모바일에서 짧은 제목을 사용하도록 분기했다.
- 대시보드 스크롤 영역은 커스텀 스크롤바 스타일을 사용한다.
- 날짜 표시는 공통 포맷 유틸 기준으로 통일했다.

3. 최근 오류 수정 상태

- `next/script` 기반 테마 초기화는 제거하고 `app/layout.tsx`의 `head` 인라인 스크립트로 전환했다.
- `ThemeToggle`은 SSR/CSR 초기 렌더 불일치를 피하도록 hydration-safe 패턴으로 정리했다.

## 10. 현재 검증 상태

1. 확인 완료

- `cmd /c pnpm lint` 기준 신규 error는 없다.
- 남은 lint warning은 `components/fallback-image.tsx`의 기존 `img` 사용 경고 1건이다.
- 브라우저 재로드 후 테마 버튼과 `html[data-theme-mode]` 반영은 정상 확인했다.

2. 마지막 확인 기준

| 항목                             | 상태      |
| -------------------------------- | --------- |
| 테마 초기화 스크립트 오류        | 해결      |
| ThemeToggle hydration mismatch   | 해결      |
| 메인 화면 모바일/태블릿 레이아웃 | 반영 완료 |
| 전/후 Profiler 비교 문서화       | 미완료    |
| 상세 화면 UI 개선                | 미착수    |

## 11. 다음 에이전트 인수인계 메모

다음 작업자는 아래 순서로 이어서 진행한다.

1. 우선순위 1: 단계 4 문서화

- 단계 0 Baseline 표를 기준으로 개선 후 Profiler 결과를 다시 측정해 전/후 비교 문서를 정리한다.
- commit 수, 주요 컴포넌트 렌더 횟수, 체감 개선 포인트, 남은 리스크를 함께 기록한다.

2. 우선순위 2: 상세 화면 UI 개선

- 사용자 요청 순서상 메인 화면 정리가 먼저이며, 그 다음 상세 화면 UX를 다룬다.
- 메인 화면의 반응형/테마 방향성과 어긋나지 않게 상세 화면을 확장한다.

3. 작업 전 확인 파일

- `app/page.tsx`
- `app/layout.tsx`
- `app/globals.css`
- `components/app-header.tsx`
- `components/drain-risk-list.tsx`
- `components/drain-summary-panel.tsx`
- `components/risk-map.tsx`
- `components/theme-toggle.tsx`
- `components/theme-provider.tsx`
- `lib/date-format.ts`

4. 작업 전 검증 루틴

- 현재 브랜치와 변경 파일 상태를 먼저 확인한다.
- `components/theme-toggle.tsx`는 직전 수정 이력이 있으므로 새 편집 전 반드시 최신 내용을 다시 읽는다.
- UI 수정 후 `cmd /c pnpm lint`와 브라우저 재검증을 함께 수행한다.

5. 단계 종료 공통 처리

- `git status -sb`로 변경 파일 확인
- 변경 요약 3~5줄 정리
- 한글 커밋 메시지 제목/본문 제안
