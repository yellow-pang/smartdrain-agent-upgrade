# 02_drain data ui 작업 기록

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/drain-data-ui` |
| 작업 범위 | `/frontend` 내부 |
| 작업 목적 | API 명세 기준으로 메인/상세 화면의 하드코딩을 줄이고 데이터 흐름 연결 |

이번 작업에서는 실제 Kakao Maps SDK와 WebSocket 연결은 제외했다. 대신 REST API가 준비된 환경에서는 API를 먼저 호출하고, `NEXT_PUBLIC_API_BASE_URL`이 없거나 호출에 실패하면 API 명세 형태의 mock 응답으로 fallback하도록 구성했다.

```text
API 또는 API 명세형 mock 응답
→ lib/api/adapters.ts
→ lib/api/drain-data.ts
→ 대시보드 / 상세 페이지 컴포넌트
```

## 2. 변경 내용

| 구분 | 변경 내용 |
|---|---|
| API 타입 | `DashboardSummaryDto`, `AnalysisResultDto`, `YoloStatus` 타입 추가 |
| API 함수 | 대시보드 요약, 최신 분석 결과, 센서/위험 이력 query parameter 호출 함수 추가 |
| mock/API adapter | API 명세형 mock 응답 파일과 화면 데이터 loader 추가 |
| 메인 대시보드 | `DRAINS` 직접 참조를 제거하고 loader 결과로 지도, 목록, 상세 패널, 요약 영역 표시 |
| 상세 페이지 | 주소, 업데이트 시간, 센서 차트, 위험 이력, CCTV, YOLO/XGBoost 표시를 상세 데이터 기반으로 변경 |
| 지도 | 범례 개수를 전역 mock 상수가 아니라 전달받은 `drains` 기준으로 계산 |
| 센서 차트 | 내부 생성 데이터 대신 props로 받은 센서 이력과 요약값 표시 |
| placeholder fallback | API 미연결 또는 호출 실패 시 지도, CCTV, 센서 차트 영역에 placeholder 이미지와 `mock fallback` 배지 표시 |
| 위험 시설 목록 상태 | 목록은 이미지 placeholder 대신 loading skeleton, empty, error, success 상태 컴포넌트로 처리 |
| mock 값 미노출 | fallback 상태에서는 대시보드 현황 숫자, 목록 row, 상세 수치, 위험 이력, 분석 결과 mock 값을 실제 데이터처럼 표시하지 않음 |

## 3. 변경 전/후

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 대시보드 데이터 | `app/page.tsx`가 `DRAINS`와 `getDrainById` 직접 사용 | `loadDashboardData()`에서 API/mock fallback을 통합 처리 |
| 상세 데이터 | 상세 페이지 내부 고정 주소, 고정 시간, 고정 위험 이력 사용 | `loadDrainDetailData(id)` 결과로 시설, 센서, 위험 이력, 분석 결과 표시 |
| CCTV | 컴포넌트 내부 상수 timestamp와 이미지 사용 | 상세 분석 결과의 `imageUrl`, `analyzedAt` 사용 |
| 센서 차트 | 컴포넌트 내부에서 mock series 생성 | API 센서 이력 DTO를 adapter로 변환한 `SensorPoint[]` 사용 |
| 분석 표시 | YOLO/XGBoost 결과 화면 없음 | 최신 분석 결과 카드 추가 |
| fallback 시각화 | mock 데이터가 실제 API 데이터처럼 보일 수 있음 | placeholder 이미지로 API 미수신 상태를 구분 |
| 목록 fallback | mock 시설 row가 실제 데이터처럼 보일 수 있음 | 연결 실패 상태와 다시 시도 버튼으로 API 미수신 상태를 구분 |
| 상세 fallback | mock 상세 수치와 이력이 실제 데이터처럼 보일 수 있음 | 상세 fallback 전용 화면에서 연결 대기 상태만 표시 |

## 4. 검증 결과

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 성공 | 기존 `<img>` 최적화 warning 3건 유지 |
| `npm run build` | 성공 | Next 설정상 TypeScript validation은 건너뜀 |
| `.\node_modules\.bin\tsc.cmd --noEmit` | 성공 | 최초 sandbox EPERM 후 승인 실행으로 타입 검증 통과 |

## 5. 남은 리스크

| 리스크 | 설명 |
|---|---|
| 실제 백엔드 응답 차이 | 실제 FastAPI 응답이 명세와 다르면 `types.ts`, `drains.ts`, `adapters.ts`를 함께 갱신해야 한다. |
| mock 지도 좌표 | Kakao Maps SDK 제외 범위라 실제 위도/경도는 mock map 위치로 임시 변환한다. |
| WebSocket 미연결 | 실시간 갱신은 제외 범위라 현재는 초기 REST 조회와 fallback 흐름만 구성했다. |
| 이미지 최적화 warning | 기존 `<img>` 사용 warning이 남아 있으며 별도 `next/image` 전환 작업으로 분리 가능하다. |
| fallback 판별 | placeholder가 보이면 실제 API가 아니라 fallback 상태로 판단한다. 실제 API 응답이 오면 지도/차트/이미지가 데이터 UI로 바뀌어야 한다. |
| 목록 상태 | fallback 상태에서는 mock rows를 표시하지 않는다. 실제 API 목록 응답이 오면 위험 시설 목록 row가 표시되어야 한다. |
| 대시보드/상세 상태 | fallback 상태에서는 mock summary와 mock detail 값을 표시하지 않는다. 실제 API 응답이 오면 현황 숫자와 상세 수치가 표시되어야 한다. |

## 6. 추천 커밋 메시지

제목:

```text
feat: 배수구 화면 데이터 연결 흐름 적용
```

내용:

```text
- 대시보드와 상세 페이지가 API/mock adapter 기반 데이터를 사용하도록 변경한다.
- 센서 이력 차트와 YOLO/XGBoost 분석 결과 표시를 상세 데이터에 연결한다.
- 실제 API base URL이 없거나 호출 실패 시 API 명세형 mock 응답으로 fallback한다.
```
