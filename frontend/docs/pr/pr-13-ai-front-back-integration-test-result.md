# PR 13 AI 포함 프론트-백엔드 통합 테스트 결과

## PR 제목

```text
[docs] AI 포함 프론트-백엔드 통합 테스트 결과 정리
```

## 작업 내용

- AI Service까지 포함한 프론트-백엔드 통합 테스트 계획을 정리했다.
- Swagger, curl, Postman에서 재사용할 AI 통합 테스트 데이터를 추가했다.
- AI Service pytest, Backend-AI smoke test, REST 조회, WebSocket 수동 확인 절차와 결과를 문서화했다.
- WebSocket 이벤트는 한 번의 `POST /api/analysis/async-run` 요청 기준으로 아래 3개가 수신되는 것을 정상 기준으로 정리했다.

```text
YOLO_RESULT_UPDATED
XGBOOST_RESULT_UPDATED
DRAIN_STATUS_UPDATED
```

## 테스트 결과

| 구분              | 결과 | 내용                                          |
| ----------------- | ---- | --------------------------------------------- |
| AI Service pytest | 통과 | `45 passed`                                   |
| Backend health    | 통과 | `GET /` 200                                   |
| AI Service docs   | 통과 | `GET /docs` 200                               |
| Frontend build    | 통과 | `npm.cmd --prefix frontend run build` 성공    |
| Frontend lint     | 통과 | error 없음, `<img>` 사용 경고 1건             |
| Backend async-run | 통과 | `POST /api/analysis/async-run` 성공           |
| AI callback 저장  | 통과 | YOLO/XGBoost 결과가 DB에 저장됨               |
| 최신 분석 조회    | 통과 | `analysis/latest`가 최신 분석 결과 반환       |
| 위험 이력 조회    | 통과 | `risk-history`가 최신 위험 이력 반환          |
| WebSocket 이벤트  | 통과 | Node WebSocket 기준 3개 이벤트 모두 수신      |
| 잘못된 drainId    | 통과 | `DR-NOT-FOUND` 요청 시 `DRAIN_NOT_FOUND` 반환 |

## 리뷰 포인트

| 항목             | 확인 내용                                                                                        |
| ---------------- | ------------------------------------------------------------------------------------------------ |
| 테스트 범위      | 모델 정확도가 아니라 Backend-AI-Frontend 연결 계약 검증으로 기록했는지 확인                      |
| WebSocket 기준   | 한 번의 분석 요청마다 3개 이벤트가 오는 것을 정상 기준으로 이해할 수 있는지 확인                 |
| 반복 테스트 주의 | 테스트 반복 시 `yoloResultId`, `xgboostResultId`, timestamp가 계속 증가하는 점이 기록됐는지 확인 |
| 남은 리스크      | AI mock 이미지 URL, 테스트 DB 이력 누적, 자동 브라우저 테스트 부재가 과장 없이 정리됐는지 확인   |

## 변경 파일

| 파일                                                     | 변경 내용                                                           |
| -------------------------------------------------------- | ------------------------------------------------------------------- |
| `docs/plans/plan-08-ai-front-back-integration-test.md`   | AI 포함 통합 테스트 계획 작성                                       |
| `docs/test/ai-front-back-integration/test-data.json`     | async-run, AI 직접 호출, callback, 기대 WebSocket payload 예시 추가 |
| `docs/steps/step-10-ai-front-back-integration-result.md` | 실제 자동/수동 테스트 결과와 수동 확인 절차 기록                    |
| `docs/images/통합테스트_수동테스트결과화면.jpg`          | WebSocket 수동 확인 결과 이미지 추가                                |
| `docs/pr/pr-13-ai-front-back-integration-test-result.md` | PR 리뷰용 요약 문서 추가                                            |

## 스크린샷 / 테스트 결과

- WebSocket 수동 확인 이미지는 `docs/images/통합테스트_수동테스트결과화면.jpg`를 참고한다.
- DevTools `Network > WS > /ws/drains/status > Messages`에서 `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED`, `DRAIN_STATUS_UPDATED` 수신을 확인했다.
- 한 번의 Swagger 실행에서 3개 이벤트가 오는 것은 정상이다.
- 같은 3개 이벤트 묶음이 여러 번 보이면, 이전 자동 테스트나 반복 실행으로 실제 분석 이력이 여러 번 생성된 것인지 `analysis/history`에서 확인한다.

## 남은 리스크

- AI Service는 현재 fake YOLO와 rule-based XGBoost baseline 기준이므로 모델 정확도 검증은 별도 범위다.
- `ai-server://mock/{id}` 이미지는 브라우저에서 실제 이미지로 렌더링되지 않을 수 있으며, 현재는 fallback 표시를 정상으로 본다.
- 통합 테스트를 반복하면 DB에 YOLO/XGBoost 이력이 누적되므로, 재현 테스트 전에는 seed 상태와 실행 시각을 함께 기록해야 한다.
- Playwright 같은 브라우저 E2E 자동화는 아직 없어서, 화면 반영 최종 확인은 DevTools와 브라우저 수동 확인에 의존한다.
