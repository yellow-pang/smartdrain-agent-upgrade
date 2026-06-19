# 07_realtime websocket manual test summary 작업 기록

## 1. 작업 목적

이번 단계는 `frontend/docs/test/maual_test_websocket.md`에 정리된 수동 테스트 절차를 기준 문서로 두고, Step/PR 문서에서는 반복되는 테스트 단계를 줄이기 위해 진행했다.

수동 테스트는 실제 브라우저와 Swagger에서 진행할 예정이므로, Step 문서에는 “무엇을 확인했고 무엇을 보류할지”만 남기는 방식으로 정리한다.

## 2. 기준 문서

| 문서 | 역할 |
|---|---|
| `frontend/docs/test/maual_test_websocket.md` | 실제 수동 테스트 실행 절차와 결과 기록 양식 |
| `frontend/docs/plans/plan-05-realtime-websocket-manual-verification.md` | 현재 DB 기준 수동 테스트 계획 |
| `frontend/docs/steps/step-06-realtime-websocket-verification.md` | CLI/WebSocket 검증 결과와 보류 항목 기록 |

앞으로 같은 WebSocket 수동 테스트를 다시 할 때는 Step 문서에 전체 Swagger body를 반복해서 붙이지 않고, `docs/test/maual_test_websocket.md`의 8번 결과 기록 양식만 채운다.

## 3. 현재 판단

| 항목 | 판단 |
|---|---|
| WebSocket 연결 | CLI 기준 연결 확인 완료, 브라우저 수동 확인 예정 |
| `DRAIN_STATUS_UPDATED` | XGBoost 실행 후 수신 확인 완료 |
| 대시보드 갱신 | 코드 경로와 payload 기준 가능, 브라우저 수동 확인 예정 |
| 상세 화면 갱신 | 현재 위험 상태 갱신 가능, 브라우저 수동 확인 예정 |
| 최신 이미지 표시 | REST 기준 `/test-snapshots/drain-001-c.jpg` 표시 확인 |
| 과거 이미지 이동 | 현재 구조상 정상 테스트 완료로 보기 어려움 |
| 이미지 레이아웃 | CCTV/썸네일 영역이 커서 지도와 상태 영역을 밀어내는 UI 개선 필요 |

## 4. 테스트 단계 축소 방식

기존에는 Step 문서마다 Swagger 입력, 확인 항목, 결과 표가 반복됐다. 이후에는 아래처럼 역할을 나눈다.

| 문서 | 작성 범위 |
|---|---|
| test 문서 | 실제 실행 순서, Swagger 입력값, 결과 기록 양식 |
| plan 문서 | 테스트 대상, 완료 기준, 보류 기준 |
| step 문서 | 실행 결과, 발견한 문제, 후속 작업 |
| PR 문서 | 리뷰어가 봐야 할 요약과 남은 리스크 |

## 5. 이번 수동 테스트에서 놓치면 안 되는 항목

| 항목 | 이유 |
|---|---|
| reconnect/error 상태 | 연결 성공만 확인하면 장애 상황 표시가 빠질 수 있음 |
| 다른 시설 이벤트 무시 | 상세 화면이 현재 drainId가 아닌 이벤트로 바뀌면 안 됨 |
| 새로고침 후 유지 | WebSocket 갱신이 DB/REST에도 저장됐는지 확인 필요 |
| 잘못된 imageUrl fallback | 이미지 경로가 깨져도 화면이 무너지면 안 됨 |
| 모바일 레이아웃 | CCTV 이미지가 큰 상태에서 모바일 겹침 가능성 있음 |
| ISO 시간 표시 | 현재 화면에서 시간이 길게 보여 정보 가독성이 떨어짐 |

## 6. 후속 작업 분리

| 후속 작업 | 추천 브랜치 |
|---|---|
| YOLO/XGBoost WebSocket 계약 확정 및 프론트 연결 | `feature/realtime-analysis-websocket-contract` |
| 상세 CCTV 이미지 이력 UI 개선 | `fix/detail-cctv-snapshot-layout` |
| 시간 표시 형식 정리 | `fix/detail-readable-datetime` |

## 7. 추천 커밋 메시지

제목:

```text
docs: WebSocket 수동 테스트 문서 흐름 정리
```

내용:

```text
- 수동 테스트 절차를 docs/test 문서 기준으로 정리한다.
- Step 문서에는 결과와 보류 판단만 남기도록 역할을 분리한다.
- 과거 이미지 이동과 이미지 레이아웃 문제를 후속 작업으로 기록한다.
```
