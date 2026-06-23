# 22 MVP 발표용 데이터 정확성 개선 결과

## 작업 목표

발표용 MVP 화면에서 백엔드 API 계약과 다른 단위·시간·위험도 의미가 표시되지 않도록 정리했다. 새 기능을 추가하지 않고, 관리자가 대시보드와 상세 화면에서 **현재 상태, 최신 측정값, 최종 판단**을 오해 없이 읽는 데 집중했다.

## 변경 요약

| 구분 | 변경 결과 |
| --- | --- |
| 단위 | 수위는 `cm`, 유속은 `m/s`, 막힘률은 `%`로 표시한다. 기존 `waterLevelPct`, `waterLevelM`, `m³/min`, `유량` 표기를 제거했다. |
| 센서 현재값 | 상세 화면은 `sensorSummary`를 우선 사용하고, 요약값이 없을 때에만 시간순 이력의 마지막 값을 현재값으로 사용한다. |
| 차트 | 이력을 측정 시각 오름차순으로 정렬한다. 24시간·7일 탭, 임의 샘플링, 14:30 기준선, 근거 없는 최고값 카드를 제거했다. |
| 위험도 | `riskScore` 점수 UI와 센서별 고정 위험·주의 배지를 제거했다. 최종 상태 배지와 `finalDecision` 문구를 유지한다. |
| 예외 처리 | 목록·상세·센서 이력 DTO의 누락 가능 값을 nullable로 반영하고, 화면은 `-`로 표시한다. 상세 API 요청 실패 시 mock 데이터 대신 오류 안내 화면을 표시한다. |

## 변경 전/후

| 항목 | 변경 전 | 변경 후 |
| --- | --- | --- |
| 수위 | API의 `waterLevelCm`을 퍼센트·진행 바로 표현 | `85 cm`처럼 원본 단위로 표현 |
| 유속 | `유량 0.4 m³/min`으로 표시 | `유속 0.4 m/s`로 표시 |
| 현재 센서값 | 이력 배열 마지막 값에 의존 | `sensorSummary` 우선, 정렬 이력 fallback |
| 센서 차트 | 실제 기간 조회가 없는 24시간·7일 탭과 고정 기준선 표시 | 현재 API가 반환한 최근 측정 이력만 표시 |
| 위험 점수 | 위험도 의미가 확정되지 않은 점수와 progress 표시 | 최종 상태와 최종 판단 문구를 반응형 전체 행 카드로 강조 |
| API 실패 | 상세 화면이 로딩 또는 fallback 표현에 머물 가능성 | 서버 연결 확인을 안내하는 오류 화면 표시 |

## 데이터 처리 흐름

```text
REST 상세 응답
    -> adapters.ts: DTO nullable 값과 단위 보존
    -> sensorHistoryDtoToPoints(): measuredAt 오름차순 정렬
    -> DrainDetailPage
        -> 현재 카드: sensorSummary 우선
        -> 차트: 정렬된 sensorHistory
        -> 위험도: riskLevel + finalDecision
```

WebSocket `DRAIN_STATUS_UPDATED` 이벤트는 수위·유속 값이 모두 있을 때만 센서 이력에 추가하며, 추가 후에도 측정 시각순으로 정렬한다.

## 적용 파일

| 파일 | 실제 변경 내용 |
| --- | --- |
| `app/page.tsx` | 모바일 선택 시설 요약의 수위·유속 단위와 null 표시 수정 |
| `app/drains/[id]/page.tsx` | 상세 요약, 센서 카드, 시설 정보, 위험 이력, API 오류 화면 및 현재값 선택 기준 수정 |
| `components/sensor-trend-chart.tsx` | 기간 탭·기준선·최고값·고정 배지 제거, 최근 측정 이력 전용 차트로 변경 |
| `components/drain-summary-panel.tsx`, `components/drain-risk-list.tsx` | 수위·유속 표기와 null 표시 통일 |
| `lib/api/adapters.ts` | ratio 변환, 이력 시간 정렬, API DTO→UI 타입 변환 및 WebSocket 병합 기준 수정 |
| `lib/api/types.ts` | 목록·상세·요약·센서 이력의 nullable 계약 반영 |
| `lib/mock-data.ts`, `lib/api/mock-responses.ts` | UI 타입과 mock 응답을 cm/m/s 기준으로 동기화 |

## 반응형 UI 적용

| 화면 폭 | 최종 상태·판단 영역 |
| --- | --- |
| 모바일 | 수위·유속·막힘률 카드 뒤에 최종 판단을 전체 폭으로 표시해 문구가 잘리지 않게 한다. |
| 태블릿 | 두 열 카드 배치를 유지하고 최종 판단을 두 열 전체에 걸쳐 표시한다. |
| 데스크톱 | 세 열 지표 뒤에 최종 판단을 세 열 전체에 걸쳐 표시해 점수보다 판단 문구가 먼저 읽히게 한다. |

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| `npm.cmd exec tsc -- --noEmit` | 통과 | nullable DTO 변경을 포함한 TypeScript 검사 완료 |
| `npm.cmd run lint` | 통과 | 오류 없음. 기존 `components/fallback-image.tsx`의 `<img>` 경고 1건만 남음 |
| `npm.cmd run build` | 통과 | Next.js production build 및 정적 페이지 생성 완료 |
| `git diff --check` | 통과 | 공백 오류 없음 |

## 남은 확인 사항

1. 실제 FastAPI 응답을 최신순·오래된순·측정시각 누락 조합으로 준비해 차트 순서와 현재값 fallback을 수동 확인한다.
2. 360px, 768px, 1280px 폭에서 최종 판단 문구의 줄바꿈과 수위·유속 단위가 겹치지 않는지 확인한다.
3. 상세 API를 실패시켜 오류 화면이 mock 데이터 없이 표시되는지 발표 환경에서 확인한다.

## 권장 커밋 메시지

```text
docs: MVP 데이터 정확성 개선 작업 기록 보강

- 실제 데이터 변환과 반응형 UI 변경 흐름을 완료 문서에 기록한다.
- 검증 결과와 발표 전 수동 확인 항목을 구체화한다.
```
