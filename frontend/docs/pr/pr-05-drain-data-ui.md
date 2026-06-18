## PR 제목

[feat] # 배수구 화면 데이터 연결 흐름 적용

## 작업 내용

- API 명세 기준으로 메인 대시보드와 상세 페이지의 데이터 흐름을 정리했습니다.
    - `NEXT_PUBLIC_API_BASE_URL`이 있으면 REST API를 먼저 호출합니다.
    - API base URL이 없거나 호출 실패 시 API 명세형 mock 응답으로 fallback합니다.
    - 화면 컴포넌트는 API 응답을 직접 쓰지 않고 adapter를 거친 UI 타입을 사용합니다.
- 메인 대시보드의 하드코딩 의존을 줄였습니다.
    - 지도, 위험 시설 목록, 상세 패널이 `loadDashboardData()` 결과를 공유합니다.
    - 대시보드 요약 영역을 추가해 전체/위험/주의/양호/판단불가 개수를 표시합니다.
    - 지도 범례 개수는 전달받은 데이터 기준으로 계산합니다.
- 상세 페이지의 하드코딩 표시를 제거했습니다.
    - 주소, 최근 업데이트, 위험 이력, 센서 차트, CCTV 캡처 시간이 상세 데이터 기반으로 표시됩니다.
    - YOLO 막힘 상태, YOLO 신뢰도, XGBoost 위험 점수, 최종 판단 카드를 추가했습니다.
- API 연동 파일을 보강했습니다.
    - `DashboardSummaryDto`, `AnalysisResultDto`, `YoloStatus` 타입을 추가했습니다.
    - `getDashboardSummary()`, `getLatestAnalysis()` 호출 함수를 추가했습니다.
    - 센서/위험 이력 조회 함수가 query parameter를 받을 수 있게 했습니다.

## 주요 변경 파일

- `frontend/lib/api/drain-data.ts`
    - API 우선 호출과 mock fallback을 담당하는 화면 데이터 loader 추가
- `frontend/lib/api/mock-responses.ts`
    - API 명세 형태의 mock 응답 생성 함수 추가
- `frontend/lib/api/adapters.ts`
    - 목록, 상세, 센서 이력, 위험 이력, 요약 데이터 adapter 보강
- `frontend/app/page.tsx`
    - 메인 대시보드를 loader 기반 데이터 흐름으로 변경
- `frontend/app/drains/[id]/page.tsx`
    - 상세 페이지를 상세/센서/위험 이력/분석 데이터 기반으로 변경
- `frontend/components/sensor-trend-chart.tsx`
    - 내부 생성 데이터 대신 props 기반 차트로 변경
- `frontend/components/cctv-snapshot-card.tsx`
    - 내부 timestamp 상수 대신 props 기반 스냅샷 표시로 변경

## 스크린샷 / 테스트 결과

- `npm run lint`
    - 성공
    - 기존 `<img>` 최적화 warning 3건 유지
- `npm run build`
    - 성공
    - Next 설정상 TypeScript validation은 건너뜀
- `.\node_modules\.bin\tsc.cmd --noEmit`
    - 성공
    - 최초 실행은 sandbox EPERM으로 실패했고, 승인 실행 후 타입 검증 통과

## 비고

- Kakao Maps 실제 SDK와 WebSocket 실제 연결은 이번 작업 범위에서 제외했습니다.
- 실제 백엔드 응답이 명세와 달라질 경우 `types.ts`, `drains.ts`, `adapters.ts`, `drain-data.ts`를 함께 갱신해야 합니다.
- mock 지도는 실제 위도/경도를 사용하지 않고 임시 `x/y` 위치를 사용합니다. Kakao Maps 연동 시 별도 교체가 필요합니다.
