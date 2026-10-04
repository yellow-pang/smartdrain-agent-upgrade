# Step 01. 실시간 대시보드 수동/자동 모드 병행 구현

## 1. 작업 목적과 배경

실시간 대시보드 데이터 갱신을 수동 분석 요청 중심으로 운영하던 흐름에, 시연·검증 효율을 높이기 위한 자동 실행 모드를 추가했다. 기존 수동 방식은 유지하고, 필요할 때만 자동 모드를 켜고 끌 수 있는 런타임 제어를 목표로 했다.

## 2. 변경 전 문제/제약사항

- 수동 방식은 `POST /api/analysis/async-run` 호출을 반복해야 해서 연속 시연과 회귀 점검에 시간이 많이 들었다.
- backend에는 scheduler 코드가 있었지만 기본 비활성이고 startup 설정 기반이라 실행 중 즉시 전환에 제약이 있었다.
- 대시보드에서 자동 모드 상태를 확인하거나 제어할 UI가 없었다.

## 3. 실제 확인한 코드와 구조

- 수동 분석 시작 API: `backend/app/routers/analysis.py`
- 비동기 분석 job 시작 로직: `backend/app/services/analysis_async_service.py`
- startup 기반 scheduler: `backend/app/services/analysis_scheduler.py`
- 대시보드 실시간 반영 경계: `frontend/components/realtime-drain-sync.tsx`
- 대시보드 화면 route: `frontend/app/page.tsx`

## 4. 적용한 해결 방법

### 4.1 Backend 런타임 자동 시뮬레이터 추가

- `backend/app/services/realtime_simulator.py`를 추가해 메모리 상태 기반의 start/stop/status 제어 루프를 구현했다.
- 자동 루프는 drain별로 센서 데이터를 생성한 뒤 기존 `start_analysis_for_drain(..., trigger_type="scheduled")`를 호출한다.
- 진행 중 분석 job(`processing`, `yolo_completed`)이 있으면 해당 drain은 skip해 중복 실행을 줄였다.

### 4.2 Backend 제어 API 추가

- `backend/app/routers/realtime_simulator.py`에 아래 endpoint를 추가했다.
1. `GET /api/realtime-simulator/status`
2. `POST /api/realtime-simulator/start`
3. `POST /api/realtime-simulator/stop`
- `backend/app/main.py`에 router 등록과 shutdown 시 시뮬레이터 정리(`shutdown_realtime_simulator`)를 연결했다.

### 4.3 Frontend 제어 UI 추가

- API 타입/가드/클라이언트에 시뮬레이터 상태 DTO와 start/stop/status 함수를 추가했다.
- React Query 키와 상태 조회 hook(`useRealtimeSimulatorStatusQuery`)을 추가했다.
- `frontend/components/dashboard/realtime-simulator-control.tsx`를 신설해 상태 배지, 시작/중지 버튼, 최근 tick/실행 횟수, 오류 메시지 표시를 구현했다.
- `frontend/app/page.tsx`에서 요약 섹션 아래에 제어 UI를 배치했다.

## 5. 해당 방법을 선택한 이유

- startup 환경변수만으로 자동화를 제어하면 서버 재시작이 필요해 수동/자동 병행 요구와 맞지 않는다.
- 런타임 제어 API는 수동 방식을 건드리지 않고 자동 모드를 선택적으로 추가할 수 있어 회귀 위험이 낮다.
- 프론트 제어 UI를 함께 제공해 운영자가 현재 상태를 즉시 확인하고 전환할 수 있다.

## 6. 수정한 주요 파일과 역할

| 파일 | 역할 |
| --- | --- |
| `backend/app/services/realtime_simulator.py` | 자동 시뮬레이터 루프, 상태 관리, 센서 생성, 분석 시작 |
| `backend/app/routers/realtime_simulator.py` | 시뮬레이터 상태/시작/중지 API |
| `backend/app/schemas/realtime_simulator.py` | 시뮬레이터 요청/응답 스키마 |
| `backend/app/main.py` | 시뮬레이터 router 등록 및 종료 정리 |
| `frontend/components/dashboard/realtime-simulator-control.tsx` | 자동 모드 제어 UI |
| `frontend/lib/api/drains.ts` | 시뮬레이터 API 호출 함수 |
| `frontend/lib/api/types.ts`, `frontend/lib/api/response-guards.ts` | 시뮬레이터 DTO 타입/응답 검증 |
| `frontend/lib/query/drain-query-keys.ts`, `frontend/lib/query/drain-queries.ts` | 시뮬레이터 상태 query 키/조회 hook |
| `frontend/app/page.tsx` | 제어 UI를 대시보드에 포함 |
| `backend/README.md`, `docs/reference/11_API명세서.md`, `docs/verification/16_테스트_전략_및_E2E_검증.md` | 신규 API 및 검증 기준 문서 반영 |

## 7. 주요 데이터/실행 흐름

1. 운영자가 대시보드에서 자동 시뮬레이터 시작 버튼을 누른다.
2. frontend가 `POST /api/realtime-simulator/start`를 호출한다.
3. backend 시뮬레이터 루프가 주기적으로 drain별 센서 데이터를 생성한다.
4. 각 drain에 대해 기존 비동기 분석 서비스가 job을 생성하고 AI 요청을 보낸다.
5. callback 저장 후 WebSocket 이벤트가 발행되고, 대시보드가 기존 실시간 경로로 갱신된다.
6. 운영자가 중지 버튼을 누르면 루프가 cancel되어 자동 실행이 종료된다.

## 8. 수행한 검증과 결과

| 검증 항목 | 결과 |
| --- | --- |
| `npm.cmd run lint` (`frontend/`) | 통과(기존 경고 1건 유지: `fallback-image.tsx`의 `<img>` 사용) |
| `npm.cmd run build` (`frontend/`) | 통과 |
| backend import/실행 검증 | 미실행(로컬 환경에 `sqlalchemy` 미설치) |
| backend compileall 검증 | 미실행(`__pycache__` 권한 문제로 환경 제약 발생) |

## 9. 계획 대비 달라진 내용과 이유

- 계획에서 제시한 자동 주기 기본값 범위(20~30초) 중 20초를 구현 기본값으로 확정했다.
- `trigger_type`은 신규 값을 추가하지 않고 기존 체계(`scheduled`)를 재사용했다.
- scheduler 설정(`ANALYSIS_SCHEDULER_ENABLED`)은 유지하고, 별도 런타임 시뮬레이터를 추가해 목적을 분리했다.

## 10. 남은 제한사항/후속 작업

- backend 테스트 환경(의존성/DB) 준비 후 시뮬레이터 API와 `analysis_jobs`/callback/WebSocket 연계를 통합 검증해야 한다.
- 자동 모드 시작/중지 API의 인증·권한 제어는 아직 없다.
- 자동 주기(`intervalSeconds`)를 UI에서 조정하는 입력 UX는 후속 개선 대상으로 남긴다.
