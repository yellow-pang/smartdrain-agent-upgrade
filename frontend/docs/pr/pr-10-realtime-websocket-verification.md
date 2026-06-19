# PR 10 - realtime websocket verification

## PR 제목

```text
[docs] WebSocket 수동 검증과 분석 이벤트 계약 정리
```

## 작업 배경

`/ws/drains/status`와 `DRAIN_STATUS_UPDATED` 기준의 1차 실시간 갱신은 구현됐지만, 실제 브라우저 수동 테스트와 YOLO/XGBoost 원천 데이터 실시간 반영에는 아직 정리할 항목이 남아 있다.

이번 PR 문서는 아래 목적을 가진다.

| 목적 | 내용 |
|---|---|
| 수동 테스트 단계 축소 | 자세한 실행 절차는 `docs/test/maual_test_websocket.md`에 모으고 Step 문서는 결과 중심으로 유지 |
| 테스트 결과 정리 | WebSocket 연결, 이벤트 수신, 화면 반영, 이미지 표시/보류 항목을 분리 |
| 후속 계약 준비 | YOLO/XGBoost WebSocket 이벤트를 백엔드와 확정하기 위한 요청 데이터 정리 |

## 작업 내용

| 영역 | 내용 |
|---|---|
| 수동 테스트 문서 | 사용자가 작성한 `frontend/docs/test/maual_test_websocket.md`를 기준 절차 문서로 채택 |
| Step 06 | 수동 테스트 절차를 반복하지 않고 test 문서로 연결하도록 보강 |
| Step 07 | 수동 테스트 요약, 테스트 단계 축소 방식, 놓치기 쉬운 항목 정리 |
| Plan 06 | YOLO/XGBoost WebSocket 이벤트 계약 요청안과 백엔드 질문 목록 정리 |
| 다음 프롬프트 | 백엔드 계약 확정 후 프론트 구현을 시작할 프롬프트 작성 |
| 브랜치 | 후속 작업용 `feature/realtime-analysis-websocket-contract` 생성 |

## 변경 파일

| 파일 | 변경 내용 |
|---|---|
| `frontend/docs/test/maual_test_websocket.md` | 수동 테스트 실행 절차와 결과 기록 양식 |
| `frontend/docs/steps/step-06-realtime-websocket-verification.md` | 수동 테스트 절차 분리 기준 추가 |
| `frontend/docs/steps/step-07-realtime-websocket-manual-test-summary.md` | 수동 테스트 요약과 단계 축소 방식 추가 |
| `frontend/docs/plans/plan-05-realtime-websocket-manual-verification.md` | 현재 DB 기준 수동 검증 계획 |
| `frontend/docs/plans/plan-06-realtime-analysis-websocket-contract.md` | YOLO/XGBoost WebSocket 백엔드 계약 요청안 |
| `frontend/docs/pr/pr-10-realtime-websocket-verification.md` | 이번 PR 요약 |

## 테스트 판단

| 항목 | 결과 |
|---|---|
| WebSocket 연결 | CLI 기준 확인 완료, 브라우저 수동 확인 문서화 |
| `DRAIN_STATUS_UPDATED` 수신 | 확인 완료 |
| 대시보드 반영 | 수동 테스트 기준 문서화 |
| 상세 화면 반영 | 수동 테스트 기준 문서화 |
| 최신 이미지 표시 | REST 기준 확인 완료 |
| 과거 이미지 이동 | 현재 API/프론트 구조상 정상 완료로 보기 어려워 보류 |
| 이미지 크기/레이아웃 | 후속 UI 개선 필요 |

## 백엔드 확인 필요 항목

| 항목 | 요청 |
|---|---|
| YOLO WebSocket | `YOLO_RESULT_UPDATED` 또는 동등 이벤트 broadcast |
| XGBoost WebSocket | `XGBOOST_RESULT_UPDATED` 또는 동등 이벤트 broadcast |
| 기존 이벤트 확장 | `DRAIN_STATUS_UPDATED`에 `imageUrl`, `yoloResultId`, `xgboostResultId` 등 추가 가능 여부 |
| 이미지 이력 | 상세 화면 과거 이미지 이동용 YOLO result list 또는 snapshots 배열 |
| ID 계약 | `POST /api/drains` 응답에 후속 POST용 내부 숫자 ID 제공 |
| 인코딩 | 한글 주소와 `finalDecision` 깨짐 확인 |

## 리뷰 포인트

| 항목 | 확인 내용 |
|---|---|
| 테스트 문서 역할 | 수동 절차는 `docs/test`, 결과는 `docs/steps`, 요약은 `docs/pr`로 나뉘었는지 |
| 보류 기준 | 과거 이미지 이동을 이번 WebSocket 테스트 완료 기준에서 제외한 판단이 맞는지 |
| 백엔드 계약 | 이벤트를 추가할지, 기존 `DRAIN_STATUS_UPDATED`를 확장할지 팀 합의 필요 |
| 다음 브랜치 | `feature/realtime-analysis-websocket-contract`에서 계약 확정 후 구현 진행 |

## 검증

이번 변경은 문서 중심이라 lint/build는 새로 실행하지 않았다.

이전 검증 결과:

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 통과 | 기존 `<img>` 경고 1개 |
| `npm run build` | 통과 | Next.js production build 성공 |

## 커밋 메시지

제목:

```text
docs: WebSocket 수동 검증과 분석 이벤트 계약 정리
```

내용:

```text
- 수동 WebSocket 테스트 절차를 docs/test 기준으로 정리한다.
- Step 문서에는 결과와 보류 판단 중심으로 테스트 단계를 축소한다.
- YOLO/XGBoost WebSocket 이벤트 계약 요청안과 후속 구현 프롬프트를 추가한다.
```
