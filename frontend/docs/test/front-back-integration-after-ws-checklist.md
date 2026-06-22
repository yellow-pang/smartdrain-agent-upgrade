# WebSocket 이후 프론트-백엔드 통합 테스트 체크리스트

## 1. 테스트 정보

| 항목 | 값 |
|---|---|
| 테스트 일자 | 2026-06-19 |
| 테스트 담당 | 사용자 수동 확인 |
| 브랜치 | `test/frontend-backend-integration-after-ws` |
| Backend URL | `http://localhost:8000` |
| Swagger URL | `http://localhost:8000/docs` |
| Frontend URL | `http://localhost:3000` |
| WebSocket URL | `ws://localhost:8000/ws/drains/status` |
| 기본 테스트 drain code | `DR-004` |
| 추가 테스트 drain code | `DR-INT-WS-001` |
| 숫자 drainId | Swagger 응답 기준 확인 완료 |
| 최신 sensorDataId | Swagger 응답 기준 확인 완료 |
| 최신 yoloResultId | Swagger 응답 기준 확인 완료 |
| 최신 xgboostResultId | Swagger 응답 기준 확인 완료 |

상태 값은 `통과`, `실패`, `보류`, `해당 없음` 중 하나로 기록한다.

## 2. 환경 준비 체크

| 구분 | 체크 항목 | 기대 결과 | 실제 결과 | 상태 | 비고 |
|---|---|---|---|---|---|
| Git | 현재 브랜치 확인 | `test/frontend-backend-integration-after-ws` | 정상 | 통과 |  |
| Git | 테스트 전 작업 트리 확인 | 의도하지 않은 코드 변경 없음 | 정상 | 통과 |  |
| DB | PostgreSQL 실행 | DB 컨테이너 정상 실행 | 정상 | 통과 |  |
| Backend | FastAPI 실행 | `http://localhost:8000/` 정상 응답 | 정상 | 통과 |  |
| Backend | Swagger 접속 | `http://localhost:8000/docs` 표시 | 정상 | 통과 |  |
| Backend | CORS 설정 | `http://localhost:3000` 허용 | 정상 | 통과 |  |
| Frontend | `.env.local` | `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` | 정상 | 통과 |  |
| Frontend | Next dev server | `http://localhost:3000` 접속 가능 | 정상 | 통과 |  |
| Seed | 기존 seed 실행 | `backend/app/seeds/seed_mock_data.py` 실행 완료 | 정상 | 통과 |  |
| Seed | 기본 테스트 데이터 | `DR-004` 조회 가능 | 정상 | 통과 |  |

## 3. 테스트 데이터 생성 체크

기본 통합 테스트는 기존 seed의 `DR-004`로 먼저 진행한다. 아래 POST 데이터 생성은 추가 케이스가 필요할 때만 실행한다.

| 순서 | API | 사용 예시 데이터 | 기대 결과 | 실제 결과 | 상태 | 기록할 ID |
|---|---|---|---|---|---|---|
| 1 | `POST /api/drains` | `createDrain` | 테스트 시설 생성 | 정상 | 통과 | Swagger 응답 기준 확인 |
| 2 | `POST /api/sensor-data` | `sensorData.caution` | 센서 데이터 생성 | 정상 | 통과 | Swagger 응답 기준 확인 |
| 3 | `POST /api/sensor-data` | `sensorData.danger` | 최신 센서 데이터 생성 | 정상 | 통과 | Swagger 응답 기준 확인 |
| 4 | `POST /api/analysis/yolo` | `yoloResults.partiallyBlocked` | YOLO 결과 생성 | 정상 | 통과 | Swagger 응답 기준 확인 |
| 5 | `POST /api/analysis/yolo` | `yoloResults.blocked` | 최신 YOLO 결과 생성 | 정상 | 통과 | Swagger 응답 기준 확인 |
| 6 | `POST /api/analysis/xgboost` | `xgboostRequests.danger` | XGBoost 위험도 생성 | 정상 | 통과 | Swagger 응답 기준 확인 |

주의:

- 예시 데이터의 `drainId`, `sensorDataId`, `yoloResultId`는 실제 Swagger 응답 ID로 바꾼다.
- 문자열 drain code와 숫자 drainId가 다르면 두 값을 모두 기록한다.

## 4. REST 조회 체크

| 구분 | API | 기대 결과 | 실제 결과 | 상태 | 비고 |
|---|---|---|---|---|---|
| 목록 | `GET /api/drains` | `DR-004` 또는 추가 테스트 시설 표시, 필수 필드 존재 | 정상 | 통과 |  |
| 상세 | `GET /api/drains/{drain_id}` | 상세 화면 필드 존재 | 정상 | 통과 |  |
| 센서 | `GET /api/drains/{drain_id}/sensors?range=24h&limit=48` | 최신 센서 데이터 포함 | 정상 | 통과 |  |
| 위험 이력 | `GET /api/drains/{drain_id}/risk-history?days=7&limit=10` | XGBoost 결과 이력 포함 | 정상 | 통과 |  |
| 최신 분석 | `GET /api/drains/{drain_id}/analysis/latest` | 최신 YOLO/XGBoost 결과 포함 | 정상 | 통과 |  |
| 분석 이력 | `GET /api/drains/{drain_id}/analysis/history?limit=10` | YOLO/XGBoost 목록 최신순 반환 | 정상 | 통과 |  |
| 요약 | `GET /api/dashboard/summary` | 상태별 count 합계 정상 | 정상 | 통과 |  |

## 5. WebSocket 체크

Chrome DevTools에서 확인한다.

```text
F12 > Network > WS > /ws/drains/status > Messages
```

| 구분 | 확인 항목 | 기대 결과 | 실제 결과 | 상태 | 비고 |
|---|---|---|---|---|---|
| 연결 | WebSocket 연결 | 101 또는 연결 유지 | 정상 | 통과 |  |
| 기본 이벤트 | `DRAIN_STATUS_UPDATED` | XGBoost 실행 후 수신 | 정상 | 통과 |  |
| YOLO 이벤트 | `YOLO_RESULT_UPDATED` | YOLO 저장 후 수신 | 정상 | 통과 |  |
| XGBoost 이벤트 | `XGBOOST_RESULT_UPDATED` | XGBoost 저장 후 수신 | 정상 | 통과 |  |
| payload | drainId 기준 | 현재 상세 화면 drain과 같은 이벤트만 반영 | 정상 | 통과 |  |
| payload | 위험도 필드 | `riskLevel`, `riskScore`, `finalDecision` 존재 | 정상 | 통과 |  |
| payload | YOLO 필드 | `imageUrl`, `obstructionRatio`, `confidenceScore`, `yoloStatus` 존재 | 정상 | 통과 |  |
| payload | 참조 ID | `sensorDataId`, `yoloResultId`, `xgboostResultId` 추적 가능 | 정상 | 통과 |  |

## 6. 대시보드 화면 체크

URL:

```text
http://localhost:3000
```

| 구분 | 확인 항목 | 기대 결과 | 실제 결과 | 상태 | 비고 |
|---|---|---|---|---|---|
| 화면 | 대시보드 렌더링 | 화면이 깨지지 않음 | 정상 | 통과 |  |
| 요약 | 상태 count | API 요약 값 반영 | 정상 | 통과 |  |
| 지도 | 테스트 시설 표시 | 위치 또는 상태 마커 표시 | 정상 | 통과 |  |
| 지도 | 위험도 색상 | `good` green, `caution` yellow/amber, `danger` red | 정상 | 통과 |  |
| 목록 | 위험 시설 목록 | 위험도/점수 기준 표시 | 정상 | 통과 |  |
| 선택 | 선택 패널 | 수위, 유속, 막힘률, 최종 판단 표시 | 정상 | 통과 |  |
| 실시간 | WebSocket 상태 | connected 또는 연결 상태 표시 | 정상 | 통과 |  |
| 갱신 | XGBoost 후 화면 반영 | 새 위험도와 수치로 갱신 | 정상 | 통과 |  |

## 7. 상세 화면 체크

URL:

```text
http://localhost:3000/drains/DR-004
```

| 구분 | 확인 항목 | 기대 결과 | 실제 결과 | 상태 | 비고 |
|---|---|---|---|---|---|
| 화면 | 상세 페이지 렌더링 | 화면이 깨지지 않음 | 정상 | 통과 |  |
| 기본 정보 | 시설 ID/주소 | 테스트 시설 정보 표시 | 정상 | 통과 |  |
| 요약 | 위험도 | XGBoost 결과 기준 표시 | 정상 | 통과 |  |
| 요약 | 위험 점수 | 0~100 또는 화면 기준 변환 표시 | 정상 | 통과 |  |
| 요약 | 수위/유속 | 최신 센서 데이터 표시 | 정상 | 통과 |  |
| 요약 | 막힘률 | 최신 또는 참조 YOLO 결과 표시 | 정상 | 통과 |  |
| CCTV | 최신 이미지 | `imageUrl` 이미지 표시 | 정상 | 통과 |  |
| CCTV | 이미지 fallback | 잘못된 이미지에서도 화면 유지 | 정상 | 통과 |  |
| YOLO 탭 | 분석 정보 | 막힘률, confidence, 상태, 시각 표시 | 정상 | 통과 |  |
| XGBoost 탭 | 판단 정보 | 위험도, 점수, 판단 문구, 참조 ID 표시 | 정상 | 통과 |  |
| 이력 탭 | 분석 이력 | history API 결과 표시 | 정상 | 통과 |  |
| 실시간 | YOLO 이벤트 반영 | 최신 이미지와 YOLO 값 갱신 | 정상 | 통과 |  |
| 실시간 | XGBoost 이벤트 반영 | 위험도와 판단 문구 갱신 | 정상 | 통과 |  |
| 필터링 | 다른 drain 이벤트 | 현재 상세 화면 값이 덮어써지지 않음 | 정상 | 통과 |  |

## 8. 새로고침과 fallback 체크

| 구분 | 확인 항목 | 기대 결과 | 실제 결과 | 상태 | 비고 |
|---|---|---|---|---|---|
| 새로고침 | 대시보드 | 최신 DB/REST 상태 유지 | 정상 | 통과 |  |
| 새로고침 | 상세 화면 | 최신 분석 정보 유지 | 정상 | 통과 |  |
| 에러 | 없는 drain 접근 | 오류 또는 없음 상태 표시 | 정상 | 통과 |  |
| 에러 | history API 미제공 | 상세 화면은 유지 | 정상 | 통과 | history API 정상 제공 확인 |
| 에러 | 백엔드 중지 | 화면이 하얗게 깨지지 않음 | 정상 | 통과 |  |
| 반응형 | 모바일 화면 | 카드/텍스트 겹침 없음 | 정상 | 통과 |  |

## 9. 이슈 기록

| 번호 | 발견 위치 | 재현 순서 | 기대 결과 | 실제 결과 | 심각도 | 담당 | 상태 |
|---|---|---|---|---|---|---|---|
| 1 | 해당 없음 | 해당 없음 | 이슈 없음 | 정상 | 해당 없음 | 해당 없음 | 완료 |

심각도 기준:

| 심각도 | 기준 |
|---|---|
| High | 서버 실행 불가, 주요 API 500, 화면 진입 불가, 데이터 저장/조회 불가 |
| Medium | 특정 필드 누락, 화면 일부 깨짐, count 불일치, WebSocket 이벤트 누락 |
| Low | 문구, 표시 형식, 정렬, fallback 배지 등 사용성 문제 |

## 10. 최종 판단

| 항목 | 결과 |
|---|---|
| 전체 판단 | 정상 완료 |
| 통과 항목 요약 | DB, Backend, Frontend, REST, WebSocket, 대시보드, 상세 화면, fallback 확인 통과 |
| 실패 항목 요약 | 없음 |
| 보류 항목 요약 | 없음 |
| 프론트 수정 필요 | 없음 |
| 백엔드 수정 필요 | 없음 |
| 후속 테스트 필요 | 자동화 테스트 전환 시 Playwright/API 테스트 추가 검토 |
