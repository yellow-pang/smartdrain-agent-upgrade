# 02_drain data ui 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/drain-data-ui` |
| 작업 범위 | `/frontend` 내부 |
| 작업 목적 | API 명세 기준으로 메인 대시보드와 상세 화면의 하드코딩을 줄이고 mock/API adapter 데이터 흐름을 연결 |

이번 작업은 실제 Kakao Maps SDK와 WebSocket 연결을 제외하고, REST API 명세 형태의 데이터가 화면까지 흐르도록 만드는 데 집중한다.

```text
REST API 또는 API 명세형 mock 응답
→ lib/api/adapters.ts
→ UI 표시용 데이터
→ 메인 대시보드 / 상세 페이지 / 센서 차트 / 분석 결과 카드
```

## 2. 할 일

| 구분 | 작업 |
|---|---|
| 대시보드 | `GET /api/drains`, `GET /api/dashboard/summary` 기준으로 목록, 지도, 상세 패널 데이터 흐름 정리 |
| 상세 페이지 | 주소, 업데이트 시간, 위험 이력, 센서 차트, CCTV/분석 표시의 고정값 제거 |
| 센서 차트 | API 센서 이력과 요약 데이터를 props로 받아 표시 |
| YOLO/XGBoost | 최신 분석 결과 DTO를 상세 화면 카드에 표시 |
| adapter | API DTO와 mock fallback을 같은 UI 타입으로 변환 |
| 검증 | `npm run lint`, `npm run build` 실행 |

## 3. 제외할 일

| 제외 항목 | 이유 |
|---|---|
| Kakao Maps 실제 SDK | 이번 범위는 데이터 연결이며 지도 SDK 연동은 별도 작업 |
| WebSocket 실제 연결 | 실제 서버 이벤트 연결은 제외하고 REST 초기 데이터와 mock fallback만 연결 |
| 새 패키지 설치 | 현재 의존성 안에서 처리 |

## 4. 남은 리스크

| 리스크 | 대응 |
|---|---|
| 백엔드 미실행 환경 | `NEXT_PUBLIC_API_BASE_URL`이 없거나 호출 실패 시 API 명세형 mock 응답으로 fallback |
| 실제 좌표와 mock 지도 위치 차이 | Kakao Maps 전까지 mock 지도용 `x/y`는 adapter에서 임시 계산 |
| API 응답 변경 | DTO, API 함수, adapter를 함께 갱신 |
