# XGBoost 담당 범위

이 문서는 `ai_service/xgboost`가 담당하는 일과 담당하지 않는 일을 구분합니다.

## 담당 결론

XGBoost는 이미지 분석이나 YOLO 실행을 하지 않습니다. 이미 저장된 YOLO 결과 레코드와 센서 데이터를 읽어 최종 침수 위험도를 판단합니다.

```text
yolo_result 레코드
+ sensor 레코드
→ Feature 생성
→ XGBoost 예측
→ 상태 해석
→ final_decision 결정
→ xgboost_data 저장
```

## 전체 시스템에서의 위치

```text
CCTV
→ OpenCV 전처리
→ YOLO 분석
→ YOLO 결과 DB 저장
→ XGBoost 분석
→ XGBoost 결과 DB 저장
→ 백엔드 API/WebSocket
→ 프론트 화면 표시
```

현재 폴더는 `YOLO 결과 DB 저장 이후`부터 `XGBoost 결과 DB 저장`까지의 흐름만 다룹니다.

## XGBoost가 직접 책임지는 것

- `yolo_result_id` 기준 현재 YOLO 결과 조회
- 같은 `drain_id`의 최근 YOLO 이력 조회
- 같은 `drain_id`의 센서 이력 조회
- `captured_at` 이후 센서 데이터 제외
- 24개 Feature 생성
- 센서 stale, no-valid, spike, stuck 등 품질 진단
- XGBoost 예측
- `risk_level`, `risk_score` 산출
- `state_code`, `reason_codes` 해석
- `final_decision` 결정
- `xgboost_data`, `analysis_trace` 저장

## XGBoost가 담당하지 않는 것

- YOLO 모델 구조 정의
- YOLO 학습 또는 재학습
- YOLO 모델 파일 로드
- 이미지 전처리
- CCTV/RTSP 연결
- 센서 장비 수집 주기 결정
- PostgreSQL DDL 최종 결정
- FastAPI 라우터 구현
- WebSocket 이벤트 발행
- 프론트 대시보드 렌더링

## 데이터 연결 방식

금지 방식:

```text
XGBoost 코드가 YOLO 모듈 import
XGBoost 코드가 YOLO 모델 파일 직접 로드
XGBoost 코드가 이미지 파일 직접 분석
```

권장 방식:

```text
YOLO 또는 백엔드가 yolo_result를 DB에 저장
→ 백엔드 또는 실행 스크립트가 yolo_result_id 전달
→ XGBoost가 repository를 통해 필요한 데이터 조회
```

## Repository 경계

XGBoost 로직은 아래 저장소 인터페이스에만 의존해야 합니다.

```text
YoloResultRepository
SensorRepository
XgboostResultRepository
AnalysisTraceRepository
```

현재는 JSONL 파일이 DB 테이블 역할을 합니다. 이후 PostgreSQL adapter로 교체해도 Feature 생성, 품질 진단, 예측, 상태 해석 로직은 유지되어야 합니다.

## 현재 완성된 부분

- JSONL 목업 기반 분석 흐름
- Feature 생성
- 품질 게이트
- 센서 이상 진단
- 상태 해석
- 결과/trace 저장
- 18개 시나리오 검증
- pytest 기반 회귀 테스트

## 남은 부분

- PostgreSQL repository 실제 SQL 구현
- 백엔드 API 실행 트리거 연결
- WebSocket 이벤트 발행 연결
- 실제 운영 데이터 기반 재학습과 검증
