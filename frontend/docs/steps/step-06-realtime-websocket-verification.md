# 06_realtime websocket verification 작업 기록

## 1. 테스트 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `test/realtime-websocket-verification` |
| 작업 범위 | `/frontend` 내부 테스트 보조 이미지 및 통합 테스트 결과 문서화 |
| Backend | `http://localhost:8000` |
| Frontend | `http://localhost:3000` |
| WebSocket | `ws://localhost:8000/ws/drains/status` |
| 기준 이벤트 | `POST /api/analysis/xgboost` 후 발생하는 `DRAIN_STATUS_UPDATED` |

이번 단계에서는 백엔드 코드를 수정하지 않고, 실제 실행 중인 백엔드와 프론트 dev 서버를 대상으로 WebSocket 연결, 이벤트 수신, 화면 갱신 경로, 이미지 URL 저장/표시 기준을 확인했다.

## 2. 서버 실행 상태

| 확인 항목 | 결과 | 비고 |
|---|---|---|
| Backend listen | 통과 | `127.0.0.1:8000` LISTEN 확인 |
| Frontend listen | 통과 | `0.0.0.0:3000`, `[::]:3000` LISTEN 확인 |
| Backend health check | 통과 | `GET /` 응답 `success: true`, `data.status: ok` |
| Frontend 응답 | 통과 | `GET http://localhost:3000` HTML 응답 확인 |
| 정적 이미지 경로 | 통과 | `HEAD /test-snapshots/drain-001-a.jpg` 응답 `200 image/jpeg` |

`Get-NetTCPConnection`은 로컬 권한 문제로 실패했기 때문에 `netstat -ano`와 HTTP 요청으로 실행 상태를 확인했다.

## 3. 테스트 이미지 준비

`frontend/public/test-snapshots/`에 아래 테스트 파일을 배치했다.

| 파일 | 용도 | 정적 URL 확인 |
|---|---|---|
| `drain-001-a.jpg` | 첫 번째 YOLO imageUrl | `/test-snapshots/drain-001-a.jpg` |
| `drain-001-b.jpg` | 두 번째 YOLO imageUrl | `/test-snapshots/drain-001-b.jpg` |
| `drain-001-c.jpg` | 세 번째 YOLO imageUrl | `/test-snapshots/drain-001-c.jpg` |

## 4. 테스트 데이터 생성 결과

테스트용 시설을 생성한 뒤, 내부 숫자 ID를 `2`로 보고 센서/YOLO/XGBoost 데이터를 생성했다.

| 순서 | API | 결과 | 주요 응답 |
|---|---|---|---|
| 1 | `POST /api/drains` | 통과 | `data.id: DR-WS-017879`, `riskLevel: good` |
| 2 | `POST /api/sensor-data` | 통과 | `data.id: 2`, `drainId: DR-WS-017879`, `waterLevelCm: 92`, `flowVelocityMps: 0.03` |
| 3 | `POST /api/analysis/yolo` | 통과 | id `2`, imageUrl `/test-snapshots/drain-001-a.jpg`, obstructionRatio `0.31` |
| 4 | `POST /api/analysis/yolo` | 통과 | id `3`, imageUrl `/test-snapshots/drain-001-b.jpg`, obstructionRatio `0.74` |
| 5 | `POST /api/analysis/yolo` | 통과 | id `4`, imageUrl `/test-snapshots/drain-001-c.jpg`, obstructionRatio `0.22` |
| 6 | `POST /api/analysis/xgboost` | 통과 | `riskLevel: caution`, `riskScore: 0.739`, `yoloResultId: 3` |

## 5. WebSocket 연결 및 이벤트 수신

Node WebSocket 클라이언트를 `ws://localhost:8000/ws/drains/status`에 연결한 상태에서 `POST /api/analysis/xgboost`를 실행했다.

| 확인 항목 | 결과 | 비고 |
|---|---|---|
| WebSocket open | 통과 | `WS open` 확인 |
| 이벤트 수신 | 통과 | `DRAIN_STATUS_UPDATED` 수신 |
| drainId 매칭 | 통과 | payload `drainId: DR-WS-017879` |
| 위험도 값 | 통과 | payload `riskLevel: caution`, `riskScore: 0.739` |
| 센서 값 | 통과 | payload `waterLevelCm: 92`, `flowVelocityMps: 0.03` |
| 최종 판단 | 통과 | payload `finalDecision` 포함 |

수신 payload 요약:

```json
{
  "type": "DRAIN_STATUS_UPDATED",
  "payload": {
    "drainId": "DR-WS-017879",
    "riskLevel": "caution",
    "riskScore": 0.739,
    "waterLevelCm": 92,
    "flowVelocityMps": 0.03,
    "obstructionRatio": 0.22,
    "finalDecision": "상태를 주의 깊게 모니터링하고 예방 점검이 필요합니다.",
    "updatedAt": "2026-06-19T12:17:35.424430+09:00"
  }
}
```

## 6. 화면 갱신 경로 확인

실제 화면 렌더링 확인은 Chrome headless GPU 오류로 스크린샷 생성이 실패했다. 대신 실행 중인 프론트 코드 경로와 실제 이벤트 payload를 함께 확인했다.

| 화면 영역 | 결과 | 확인 기준 |
|---|---|---|
| 대시보드 지도 | 코드 경로 확인 | `app/page.tsx`에서 이벤트 수신 후 `dashboardData.drains`를 `drainId` 기준 병합하고 `RiskMap`에 전달 |
| 위험 시설 목록 | 코드 경로 확인 | 병합 후 `sortFacilitiesByRisk(drains)`로 재정렬하고 `DrainRiskList`에 전달 |
| 선택 시설 패널 | 코드 경로 확인 | `selectedId`가 같은 시설이면 병합된 `selected`가 `DrainSummaryPanel`에 전달 |
| 상세 화면 | 코드 경로 확인 | 현재 상세 ID와 payload `drainId`가 같을 때 상태 값을 부분 갱신 |
| WebSocket 상태 chip | 코드 경로 확인 | `waiting`, `connected`, `reconnecting`, `error`가 각각 `실시간 연결 대기`, `실시간 연결됨`, `재연결 중`, `연결 실패`로 표시 |

Chrome headless 실패 로그의 핵심 원인은 GPU process 오류였다.

```text
GPU process isn't usable. Goodbye.
```

따라서 브라우저에서 눈으로 보는 최종 UI 확인은 수동 확인 항목으로 남긴다.

## 7. 여러 이미지 URL 저장 및 상세 표시 기준

여러 YOLO 결과를 저장한 뒤 `GET /api/drains/DR-WS-017879`와 `GET /api/drains/DR-WS-017879/analysis/latest`를 확인했다.

| 확인 항목 | 결과 |
|---|---|
| 여러 YOLO imageUrl 저장 | 통과 |
| 최신 분석 조회의 `yoloResult.imageUrl` | `/test-snapshots/drain-001-c.jpg` |
| 상세 조회의 `imageUrl` | `/test-snapshots/drain-001-c.jpg` |
| 상세 화면 이미지 선택 코드 | `analysis.yoloResult.imageUrl`을 우선 사용하고, 없으면 `detail.imageUrl`, 그 다음 placeholder 사용 |

주의할 점:

`POST /api/analysis/xgboost` 요청에는 `yoloResultId: 3`을 넣었지만, 최신 분석 조회와 WebSocket payload의 `obstructionRatio`는 최신 YOLO 결과인 id `4`의 `0.22` 기준으로 내려왔다. 즉, 현재 백엔드는 XGBoost 요청에 사용한 `yoloResultId`와 별개로 상세/최신 상태에서는 가장 최근 YOLO 결과를 우선 반영하는 것으로 보인다.

### 7.1 수동 화면 확인 후 보강

사용자가 실제 브라우저에서 상세 화면을 확인한 결과, 최신 CCTV 이미지는 표시되지만 과거 이미지 이동은 정상 테스트가 이루어진 것으로 보기 어렵다.

첨부 화면 기준 관찰:

| 항목 | 실제 화면 상태 | 판단 |
|---|---|---|
| 최신 이미지 표시 | `drain-001-c.jpg`로 보이는 최신 스냅샷이 CCTV 영역에 표시됨 | 부분 통과 |
| 썸네일/과거 이미지 이동 | 이전/다음 버튼이 보이지만 과거 이미지로 이동되는지 확인되지 않음 | 보류 |
| 과거 이미지 이력 | 현재 상세 API와 프론트 매핑은 최신 이미지 1장 중심 | 정상 완료로 보기 어려움 |
| 이미지 크기 | CCTV 이미지와 썸네일 영역이 크게 표시되어 주변 레이아웃을 밀어냄 | 후속 UI 개선 필요 |
| 지도/상태 영역 영향 | 왼쪽 이미지 영역 높이가 커져 지도 또는 하단 영역 배치가 답답해짐 | 후속 UI 개선 필요 |

현재 `CctvSnapshotCard`는 여러 스냅샷을 받을 수 있는 UI 구조를 갖고 있지만, `getSnapshots()`는 `analysis.yoloResult.imageUrl` 또는 `detail.imageUrl`에서 최신 1장만 만들어 넘긴다. 따라서 여러 YOLO 결과를 DB에 저장하더라도 프론트 상세 화면에서는 과거 이미지 목록을 충분히 검증할 수 없다.

후속 UI 개선 때 함께 다룰 항목:

| 개선 항목 | 방향 |
|---|---|
| 과거 이미지 데이터 | 백엔드가 YOLO 결과 목록 또는 이미지 이력 endpoint를 제공해야 함 |
| 상세 화면 이미지 배열 | 최신 1장이 아니라 여러 imageUrl을 `CctvSnapshotCard`에 전달 |
| 이미지 높이 제한 | 큰 이미지가 지도/상태 카드 레이아웃을 밀지 않도록 max-height 또는 고정 비율 조정 |
| 썸네일 크기 | 썸네일 영역 높이를 제한하고 버튼이 1장일 때는 비활성/숨김 처리 |
| 지도와 상세 카드 배치 | CCTV 이미지가 커져도 오른쪽 지도/상태 영역이 과도하게 밀리지 않도록 grid 높이 재검토 |

## 8. 발견한 문제와 백엔드 확인 필요 항목

| 번호 | 발견 위치 | 실제 결과 | 영향 | 후속 조치 |
|---|---|---|---|---|
| 1 | `POST /api/drains` 응답 | 화면용 문자열 ID만 내려오고, 다음 POST에 필요한 숫자형 `drainId`가 응답에 없음 | Swagger 순서 테스트 시 사용자가 내부 숫자 ID를 알기 어려움 | 백엔드 응답에 내부 ID를 추가하거나, 후속 POST가 문자열 drain code를 받도록 계약 정리 필요 |
| 2 | `POST /api/drains` 한글 주소 | 응답 주소가 `????? ??? ???? 19`로 깨짐 | 지도/상세 주소 표시 품질 저하 | 요청/DB/응답 인코딩 경로 확인 필요 |
| 3 | `GET /api/drains/{id}` 및 최신 분석 응답 | 일부 한글 `finalDecision`이 mojibake 형태로 표시됨 | 화면 문구가 깨질 수 있음 | 백엔드 JSON 응답 인코딩 또는 DB 저장 인코딩 확인 필요 |
| 4 | XGBoost와 최신 YOLO 기준 | XGBoost 응답은 `yoloResultId: 3`, 최신 조회/WS obstructionRatio는 YOLO id `4` 기준 | 분석에 사용한 이미지와 화면 표시 이미지/막힘률이 달라질 수 있음 | `latest` 기준인지, XGBoost 연결 결과 기준인지 API 계약 확정 필요 |
| 5 | `DRAIN_STATUS_UPDATED` payload | `imageUrl`, `yoloStatus`, `confidenceScore`, `yoloResultId`가 없음 | WebSocket만으로 상세 이미지 실시간 갱신은 불가 | 이벤트 payload 확장 또는 이벤트 수신 후 최신 분석 REST 재조회 필요 |
| 6 | 화면 자동 갱신 수동 검증 | headless 브라우저 스크린샷 실패 | 실제 브라우저 UI의 시각적 갱신 확인은 보류 | 로컬 브라우저 DevTools 또는 Playwright 환경에서 재확인 필요 |
| 7 | 상세 CCTV 과거 이미지 이동 | 최신 이미지 1장 중심으로 표시되어 과거 이미지 이동을 정상 검증하기 어려움 | 여러 YOLO 결과 저장 테스트가 화면 이력 테스트로 이어지지 않음 | YOLO 이미지 이력 API 또는 상세 API의 snapshots 배열 필요 |
| 8 | 상세 CCTV 이미지 레이아웃 | 이미지와 썸네일 영역이 커서 지도/상태 영역을 밀어내는 느낌이 있음 | 실제 사용 화면에서 정보 밀도가 떨어지고 스크롤 부담 증가 | 후속 UI 개선 브랜치에서 이미지 높이와 grid 레이아웃 조정 |

## 8.1 추가로 놓치기 쉬운 테스트 항목

이번 테스트에서 아직 충분히 확인하지 못했거나, 수동 재검증 때 같이 확인하면 좋은 항목이다.

| 항목 | 현재 상태 | 수동 확인 방법 |
|---|---|---|
| WebSocket reconnect | 코드 경로만 확인 | 백엔드 서버를 재시작하고 chip이 `재연결 중`에서 `실시간 연결됨`으로 돌아오는지 확인 |
| WebSocket error | 코드 경로만 확인 | 백엔드를 끈 상태에서 프론트 진입 후 `연결 실패` 또는 재연결 상태 확인 |
| 다른 시설 이벤트 무시 | 미확인 | 상세 화면을 `DR-WS-017879`로 열고 `DR-INT-001` 이벤트 발생 시 상세 값이 바뀌지 않는지 확인 |
| 위험도순 재정렬 | 코드 경로 확인 | XGBoost 결과로 `DR-WS-017879` 위험도가 바뀔 때 목록 순위 변화 확인 |
| 센서 차트 다건 추세 | 제한적 | 센서 데이터를 3건 이상 만든 뒤 차트 선/점이 여러 개 표시되는지 확인 |
| 위험 이력 다건 표시 | 제한적 | XGBoost를 2회 이상 실행해 과거 위험 이력에 여러 행이 쌓이는지 확인 |
| 잘못된 imageUrl fallback | 미확인 | YOLO imageUrl에 없는 경로를 넣고 placeholder 표시 확인 |
| 새로고침 후 유지 | 미확인 | WebSocket 갱신 후 새로고침했을 때 REST 조회 값도 동일한지 확인 |
| 모바일 레이아웃 | 미확인 | 브라우저 responsive mode에서 CCTV/차트/상태 카드 겹침 확인 |
| 시간 표시 형식 | 개선 필요 | ISO 문자열이 그대로 길게 표시되는 영역을 사람이 읽기 쉬운 형식으로 바꿀지 검토 |

## 9. 검증 명령 결과

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 통과 | 기존 `components/fallback-image.tsx`의 `<img>` 경고 1개 |
| `npm run build` | 통과 | Next.js 16.2.6 production build 성공 |

초기 `npm run lint`는 sandbox 권한 때문에 `node_modules`의 ESLint 실행 파일 접근이 `EPERM`으로 막혔다. 승인 후 동일 명령을 다시 실행해 통과를 확인했다.

## 10. 결론

| 최종 산출 항목 | 결과 |
|---|---|
| WebSocket 연결 확인 | 통과 |
| `DRAIN_STATUS_UPDATED` 수신 여부 | 통과 |
| 대시보드/상세 갱신 | 코드 경로와 이벤트 payload 기준 가능, 시각적 수동 확인은 보류 |
| 여러 이미지 URL 저장 및 표시 | REST 기준 최신 imageUrl은 `/test-snapshots/drain-001-c.jpg`로 확인 |
| 과거 이미지 이동 | 현재 최신 1장 중심 구조라 정상 테스트 완료로 보기 어려움 |
| 이미지 UI | 이미지/썸네일 영역이 커서 레이아웃을 밀어내는 문제가 있어 후속 UI 개선 필요 |
| 남은 문제 | 내부 숫자 ID 미노출, 한글 응답 깨짐, XGBoost 사용 YOLO와 최신 YOLO 기준 불일치 가능성, 이미지 이력 API 부재 |

## 10.1 수동 테스트 절차 분리

수동 브라우저 테스트의 세부 절차는 별도 문서로 분리했다.

| 문서 | 역할 |
|---|---|
| `frontend/docs/test/maual_test_websocket.md` | 사용자가 실제 Swagger/브라우저에서 따라갈 수 있는 수동 테스트 체크리스트 |
| `frontend/docs/plans/plan-05-realtime-websocket-manual-verification.md` | 현재 DB 상태 기준 수동 테스트 계획과 완료 기준 |

따라서 이 Step 문서는 전체 절차를 반복하지 않고, 실제로 확인된 결과와 남은 판단만 기록한다. 이후 테스트 단계는 아래처럼 줄여 진행한다.

1. 수동 테스트 문서의 8번 결과 기록 양식만 채운다.
2. 실패/보류 항목만 이 Step 문서 또는 후속 Step 문서에 옮긴다.
3. WebSocket 계약이 바뀌면 `plan-06-realtime-analysis-websocket-contract.md`를 먼저 갱신한다.

## 11. 추천 커밋 메시지

제목:

```text
test: 실시간 WebSocket 통합 검증 결과 기록
```

내용:

```text
- /ws/drains/status 연결과 DRAIN_STATUS_UPDATED 수신 결과를 기록한다.
- 테스트 스냅샷 이미지 URL 저장 및 상세 화면 표시 기준을 확인한다.
- XGBoost 기준 YOLO와 최신 YOLO 표시 기준 차이를 백엔드 확인 항목으로 남긴다.
- lint와 build 검증 결과를 문서화한다.
```
