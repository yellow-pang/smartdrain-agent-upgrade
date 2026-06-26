# PR 31 개발 서버 시연 자동화 모듈

## 작업 내용

- 개발 서버 전용 demo simulator를 backend에 추가했다.
- simulator는 기본 off이며, dev compose 환경변수로만 켤 수 있다.
- `direct` 모드에서 센서, YOLO, XGBoost, AnalysisJob 데이터를 직접 생성하고 기존 WebSocket 이벤트를 발행한다.
- `async` 모드에서는 기존 Backend -> AI Service -> Backend callback 흐름을 사용할 수 있다.
- 메인 대시보드 요약 캐시가 `DRAIN_STATUS_UPDATED` 이벤트에 맞춰 즉시 갱신되도록 보강했다.
- 상세 센서 차트가 30초 단위 시연 데이터를 구분할 수 있도록 시간 라벨에 초를 포함했다.
- DR-003 상태별 이미지가 있으면 `/api/mock-images/demo/drain_3_{state}.*`를 우선 사용하고, 없으면 기존 `drain_3.jpg`로 fallback한다.
- 센서값과 분석값은 상태별 범위 안에서 랜덤 샘플링해 숫자가 매번 너무 똑같아 보이지 않도록 했다.
- 실행 가이드와 이미지 생성 프롬프트를 `step-39` 문서에 정리했다.

## 주요 파일

| 파일 | 설명 |
|---|---|
| `backend/app/services/demo_simulator.py` | 시연 자동화 loop, 직접 결과 생성, WebSocket broadcast |
| `backend/app/core/config.py` | demo simulator 설정 추가 |
| `backend/app/main.py` | startup/shutdown 연결 |
| `docker-compose.dev.yml` | dev 환경변수 연결 |
| `.env.example` | compose demo env 예시 |
| `backend/.env.example` | backend 단독 실행 env 예시 |
| `frontend/components/realtime-drain-sync.tsx` | 대시보드 요약 cache 실시간 갱신 |
| `frontend/lib/api/adapters.ts` | 센서 차트 시간 라벨 초 단위 포함 |
| `frontend/app/drains/[id]/page.tsx` | 상세 실시간 센서 포인트 초 단위 포함 |
| `frontend/docs/steps/step-39-dev-demo-automation-module.md` | Docker 실행 가이드, 이미지 규칙, 프롬프트 |

## 실행 방법

기본 개발 서버와 seed:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose --profile seed run --rm seed
```

발표 본시연용 direct 모드:

```powershell
$env:COMPOSE_DEMO_SIMULATOR_ENABLED="true"
$env:COMPOSE_DEMO_SIMULATOR_MODE="direct"
$env:COMPOSE_DEMO_SIMULATOR_INTERVAL_SECONDS="30"
$env:COMPOSE_DEMO_SIMULATOR_START_DELAY_SECONDS="10"
$env:COMPOSE_DEMO_SIMULATOR_TARGET_DRAIN_CODE="DR-003"
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend frontend nginx
```

확인 URL:

```text
http://localhost:8080
http://localhost:8080/drains/DR-003
```

## 이미지 준비

DR-003 상세 시나리오 이미지는 아래 경로에 넣는다.

```text
mock_data/ai_image_samples/demo/drain_3_good.jpg
mock_data/ai_image_samples/demo/drain_3_caution.jpg
mock_data/ai_image_samples/demo/drain_3_danger.jpg
mock_data/ai_image_samples/demo/drain_3_unknown.jpg
```

이미지가 없으면 기존 이미지로 fallback된다.

```text
/api/mock-images/drain_3.jpg
```

## 검증

실행 완료:

```text
python -m compileall backend
npm.cmd run build
docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
```

검증 결과:

- Backend Python 문법 검증 통과
- Frontend Next.js production build 통과
- Docker compose dev config 검증 통과

## 남은 확인 사항

- 실제 Docker 실행 후 메인/상세 화면에서 WebSocket 이벤트 반영을 눈으로 확인해야 한다.
- `direct` 모드는 발표 안정성을 위한 시연 데이터이며 실제 YOLO 모델 판단은 아니다.
- 실제 YOLO 흐름을 보여주려면 `COMPOSE_DEMO_SIMULATOR_MODE=async`로 별도 리허설한다.
- 상태별 이미지는 사용자가 추가해야 한다.
- 시연 반복 후 DB 이력이 많이 쌓이면 발표 전 DB volume 초기화 여부를 결정한다.
