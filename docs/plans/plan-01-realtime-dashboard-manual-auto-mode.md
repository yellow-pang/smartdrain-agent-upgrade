# Plan 01. 실시간 대시보드 수동/자동 갱신 모드 추가

## 1. 요청 배경과 해결 문제

- 현재 실시간 대시보드 시연/검증 시 데이터 갱신이 수동 절차 중심이라 반복 시연과 운영 리허설에 시간이 많이 든다.
- 기존 수동 방식은 유지하면서, 동일한 화면 흐름에서 자동으로 센서/분석 갱신 이벤트를 발생시키는 자동화 모드를 추가한다.
- 목표는 "수동 모드 회귀 없이 자동 모드를 선택적으로 켤 수 있는 상태"를 만드는 것이다.

## 2. 현재 구현 상태와 확인 근거

| 항목 | 현재 상태 | 확인 근거 |
| --- | --- | --- |
| 수동 분석 트리거 | `POST /api/analysis/async-run` 호출 기반으로 존재 | `backend/app/routers/analysis.py`, `backend/README.md` |
| 자동 스케줄러 | 백엔드 내부 scheduler 구현은 있으나 기본 비활성 | `backend/app/services/analysis_scheduler.py`, `backend/.env.example`(`ANALYSIS_SCHEDULER_ENABLED=false`) |
| 대시보드 실시간 반영 | WebSocket 이벤트 수신 시 Query cache patch로 화면 반영 | `frontend/components/realtime-drain-sync.tsx` |
| 자동 시뮬레이션 운영 절차 | 문서 기준 수동 통합 확인 중심, 자동 E2E/자동 시뮬레이션 절차 부재 | `docs/verification/12_프론트엔드_백엔드_API연동_테스트_문서.md`, `docs/verification/16_테스트_전략_및_E2E_검증.md` |

## 3. 작업 범위 / 제외 범위

### 작업 범위

- 기존 수동 분석 트리거 동작은 유지한다.
- 백엔드에 "자동 시뮬레이션 시작/중지/상태 확인" 런타임 제어를 추가한다.
- 자동 모드가 주기적으로 센서 데이터를 생성하고 비동기 분석 요청을 호출하도록 연결한다.
- 프론트 대시보드에서 자동 모드 상태를 확인하고 시작/중지할 수 있는 최소 UI를 추가한다.
- 자동/수동 모드 사용법과 검증 절차를 문서에 반영한다.

### 제외 범위

- 기존 API/WS 계약을 깨는 변경
- DB schema 및 Alembic migration 변경
- AI 모델 로직(YOLO/XGBoost) 자체 수정
- Docker/Nginx/CI 구조 변경

## 4. 구현 방향 비교와 추천

### 옵션 A. 기존 startup scheduler 환경변수만 사용

- 장점: 구현량이 작다.
- 단점: 모드 전환 시 백엔드 재시작이 필요하고, 시연 중 수동/자동 전환이 어렵다.

### 옵션 B. 런타임 제어 가능한 시뮬레이터 API 추가 (추천)

- 장점: 수동/자동 모드를 실행 중에 전환할 수 있고, 프론트 제어 UI와 연결이 쉽다.
- 장점: 기존 수동 API는 그대로 유지되어 회귀 위험이 낮다.
- 단점: 백엔드/프론트/문서 수정 범위가 옵션 A보다 넓다.

### 추천 이유

- 요청 핵심이 "수동은 유지하고 자동을 추가"이므로, 런타임 전환이 가능한 구조가 요구사항에 가장 직접적으로 맞다.
- 기존 scheduler를 완전히 제거하지 않고, 별도 시뮬레이터 계층으로 추가해 책임을 분리하면 유지보수성이 좋다.

## 5. 예상 변경 파일

| 경로 | 변경 내용 |
| --- | --- |
| `backend/app/services/realtime_simulator.py` (신규) | 자동 시뮬레이션 루프, 시작/중지/상태 관리 |
| `backend/app/routers/realtime_simulator.py` (신규) | start/stop/status API |
| `backend/app/main.py` | 앱 수명주기에서 simulator 리소스 정리 연결 |
| `backend/app/schemas/` 하위 일부 (신규) | simulator 요청/응답 DTO |
| `backend/app/routers/__init__` 또는 router 등록부 | 신규 router 등록 |
| `frontend/lib/api/` 하위 일부 | simulator 제어 API client 추가 |
| `frontend/components/dashboard/` 하위 일부 | 자동 모드 토글/상태 표시 UI 추가 |
| `docs/reference/11_API명세서.md` | simulator API 명세 반영 |
| `docs/verification/16_테스트_전략_및_E2E_검증.md` | 수동/자동 검증 시나리오 구분 보강 |
| `docs/steps/step-01-realtime-dashboard-manual-auto-mode.md` (예정) | 구현 완료 후 작업 기록 |

## 6. 단계별 작업 계획

1. 백엔드 시뮬레이터 서비스 초안 구현
- 루프 실행 상태, interval, 대상 drain 선택 정책, graceful stop을 구현한다.

2. 시뮬레이터 제어 API 추가
- `start`, `stop`, `status` 엔드포인트를 추가하고 중복 start/stop 예외를 정리한다.

3. 분석/센서 데이터 연결
- 자동 루프에서 센서 데이터 생성 후 기존 비동기 분석 서비스 호출로 WebSocket 이벤트까지 연결한다.
- 수동 `POST /api/analysis/async-run` 동작은 그대로 유지한다.

4. 프론트 제어 UI 추가
- 대시보드에서 자동 모드 상태 배지와 시작/중지 버튼을 제공한다.
- 실패 시 사용자에게 원인 메시지를 노출하고 기존 화면 흐름은 유지한다.

5. 문서/검증 정리
- API 명세, 검증 문서를 갱신하고 steps 문서에 변경/검증/리스크를 기록한다.

## 7. 예상 영향과 위험 요소

- 자동 루프가 너무 짧은 주기로 실행되면 DB write/분석 요청이 과도해질 수 있다.
- 수동 실행과 자동 실행이 같은 drain에 동시에 들어오면 중복 job이 생길 수 있다.
- 시뮬레이터 상태를 프론트가 polling할 경우 네트워크 호출이 늘 수 있다.

## 8. 검증 계획

- 백엔드
1. 시뮬레이터 start/stop/status API 단위 확인
2. 자동 모드 실행 시 `sensor_data`, `analysis_jobs(trigger_type)`, callback 결과 생성 확인
3. 수동 `POST /api/analysis/async-run` 회귀 확인

- 프론트
1. 자동 모드 시작/중지 UI 상태 전환 확인
2. WebSocket 이벤트 수신 후 대시보드 카드/목록 실시간 반영 확인
3. 자동 모드 OFF 상태에서 기존 수동 방식 동작 확인

- 공통
1. `npm --prefix frontend run lint`
2. `npm --prefix frontend run build`
3. 실행 가능한 범위의 backend pytest 또는 API smoke

## 9. 사용자 승인 필요 결정 사항

1. 자동화 방식
- 추천: 옵션 B(런타임 제어 API + 대시보드 제어 UI)
- 대안: 옵션 A(기존 scheduler env on/off 중심)

2. 자동 실행 주기 기본값
- 추천: 20~30초 (시연 체감과 부하 균형)
- 대안: 5초 이하(변화는 빠르지만 부하 증가)

3. `analysis_jobs.trigger_type` 기록값
- 추천: 기존 값 체계 유지(`manual`/`scheduled` 중 자동 모드는 `scheduled` 재사용)
- 대안: `automated` 신규 값 사용(분류는 명확하지만 하위 문서/조회 로직 점검 필요)

승인 후 위 방향으로 구현 및 검증, steps 문서 작성까지 진행한다.
