# XGBoost work scope

## 소유 영역

```text
YOLO 결과 조회
→ 센서 최신값·과거 이력 조회
→ 최근 YOLO 이력 조회
→ 데이터 품질 검사
→ 시계열 Feature 생성
→ XGBoost 위험도 추론
→ state_code / reason_codes 해석
→ final_decision 결정
→ 결과 저장
```

## 비소유 영역

- YOLO 모델 구조와 클래스 정의
- YOLO 모델 학습·고도화
- 이미지 전처리
- 센서 장비와 수집 주기
- PostgreSQL DDL 최종 결정
- FastAPI 엔드포인트
- WebSocket 이벤트 발행
- 대시보드 렌더링

## 통합 경계

XGBoost는 아래 저장소 인터페이스에만 의존한다.

```text
YoloResultRepository
SensorRepository
XgboostResultRepository
AnalysisTraceRepository
```

현재 구현은 JSONL이다. PostgreSQL 연동 시 repository 구현만 교체한다.

## 고도화의 의미

이 프로젝트에서 XGBoost 고도화는 단순 하이퍼파라미터 조정이 아니다. 핵심은 다음이다.

1. YOLO 결과와 센서 최신·과거 데이터를 시간적으로 결합한다.
2. 센서 현재값뿐 아니라 변화량, 기울기, 표준편차, 유효 데이터 비율을 만든다.
3. 최근 YOLO obstruction 추세를 Feature로 만든다.
4. 센서 spike/stuck/stale/no-valid 같은 품질 문제를 별도로 처리한다.
5. `risk_level`과 `state_code`를 분리해 다양한 상황을 표현한다.
6. DB 연동 전에도 JSONL 목업으로 전체 파이프라인을 검증한다.
