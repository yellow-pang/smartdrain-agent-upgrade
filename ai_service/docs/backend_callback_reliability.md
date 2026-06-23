# 백엔드 callback 안정성 정책

이 문서는 AI 서버가 백엔드 요청 기반 worker로 동작할 때의 callback 예외처리와 관측성 정책을 정리한다.

## 유지하는 계약

- Backend -> AI: `POST /ai/analysis/run`
- AI -> Backend YOLO callback: `POST /api/ai-callback/yolo-result`
- AI -> Backend XGBoost callback: `POST /api/ai-callback/xgboost-result`
- `/ai/analysis/run`의 accepted response shape는 변경하지 않는다.
- YOLO/XGBoost callback payload field는 변경하지 않는다.

## 책임 경계

AI 서버가 담당하는 것:

- 백엔드가 요청한 분석 job 처리
- `drain_id` 기반 image source resolve
- YOLO 분석
- XGBoost 분석
- 백엔드 callback 전송
- callback 전송 실패 로그 기록

AI 서버가 담당하지 않는 것:

- DB write
- scheduler 실행
- queue worker orchestration
- 백엔드 job 상태 직접 변경
- 백엔드 callback endpoint contract 임의 변경

DB 저장, job 상태 변경, WebSocket broadcast는 백엔드 책임이다.

## callback 실패 정책

callback 전송은 best-effort 정책을 유지한다.

- callback 성공/실패는 이미 반환된 accepted response를 바꾸지 않는다.
- YOLO callback이 실패해도 XGBoost callback은 계속 시도한다.
- XGBoost callback이 실패하면 실패 로그를 남기고 background task는 종료한다.
- persistent retry queue는 현재 도입하지 않는다.
- Redis, RabbitMQ, Celery는 현재 범위 밖이다.

현재 로그에는 다음 정보를 남긴다.

- callback 종류: `yolo`, `xgboost`
- callback URL
- `request_id`
- `job_id`
- attempt 번호
- 최대 attempt 수
- 예외 타입
- 예외 메시지

payload 전체는 로그에 남기지 않는다.

## background task 실패 정책

`/ai/analysis/run`은 요청 검증 후 accepted response를 즉시 반환하고, 실제 분석은 FastAPI background task에서 수행한다.

background task에서 YOLO/XGBoost 분석 또는 model load가 실패하면 현재 AI 서버는 백엔드에 실패 callback을 보내지 않는다. 대신 로그에 아래 정보를 남긴다.

- `request_id`
- `job_id`
- `drain_id`
- exception traceback

따라서 백엔드 job 상태를 `failed`로 반영하려면 백엔드 쪽에서 다음 중 하나가 필요하다.

- 오래된 `processing` job timeout 처리
- 별도 failure callback endpoint contract 확정

후보 endpoint:

```text
POST /api/ai-callback/analysis-failed
```

이 endpoint는 아직 확정된 백엔드 contract가 아니므로 AI 서버 코드에서 호출하지 않는다.

## readiness 검토

현재 `/health`는 프로세스 생존 여부만 확인한다.

모델 준비 상태까지 확인하려면 기존 `/health` contract를 깨지 말고 별도 `/ready` endpoint를 검토한다.

`/ready`에서 확인할 후보:

- YOLO model file 존재 여부: `ai_service/model/best.pt`
- XGBoost model file 존재 여부: `ai_service/model/sewer_xgboost_model.json`
- mock image source resolve 가능 여부
- 필수 dependency import 가능 여부: `cv2`, `ultralytics`, `xgboost`

이번 단계에서는 readiness endpoint를 필수로 구현하지 않는다. 백엔드 배포/운영 기준이 정해지면 별도 작업으로 추가한다.

## 백엔드와 맞춰야 할 사항

AI 서버 안정성 로그만으로는 백엔드 job 상태가 자동 변경되지 않는다.

백엔드에서 별도 검토가 필요한 항목:

- AI 호출 전에 `analysis_job` 선저장
- callback 멱등성 처리
- 오래된 `processing` job timeout 처리
- failure callback endpoint 도입 여부
- `request_id`, `job_id` unique 및 조회 조건 정리
