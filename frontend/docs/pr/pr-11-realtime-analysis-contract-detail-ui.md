# PR 11 - realtime analysis contract detail ui

### **PR 작성 규칙**

**☑️ PR 제목**

```text
[feat] 실시간 분석 계약 기반 상세 화면 개선
```

**☑️ PR 내용**

## 작업 내용

<!-- 어떤 변경 사항이 있었는지 주요 내용을 적어주세요. -->

- `YOLO_RESULT_UPDATED`, `XGBOOST_RESULT_UPDATED` WebSocket 이벤트 타입과 수신 처리를 추가했습니다.
- 상세 화면 진입 시 `GET /api/drains/{drain_id}/analysis/history?limit=10` 기준으로 분석 이력을 조회하도록 추가했습니다.
- history API가 실패하거나 아직 없을 때도 기존 최신 분석 API와 상세 API로 화면이 유지되도록 fallback을 적용했습니다.
- 상세 화면 상단에 막힘 정도, 수위, 유속, 위험 점수, 최종 판단을 한눈에 볼 수 있는 분석 요약 카드를 추가했습니다.
- AI 판단 정보를 `요약 / YOLO / XGBoost / 이력` 탭으로 나누어 모델별 판단 근거를 확인할 수 있게 변경했습니다.
- CCTV 이미지는 고정 높이 메인 뷰어와 가로 썸네일 스트립으로 표시해 과거 이미지가 늘어나도 아래 UI가 밀리지 않도록 개선했습니다.
- mock YOLO/XGBoost 이력을 추가해 백엔드 history API가 없어도 상세 UI 상태를 확인할 수 있게 했습니다.
- 코드 수정 전 계획 문서 `docs/plans/plan-06-realtime-analysis-contract-detail-ui.md`를 추가했습니다.
- 작업 완료 기록 문서 `docs/steps/step-08-realtime-analysis-contract-detail-ui.md`를 추가했습니다.

## 스크린샷 / 테스트 결과

<!-- API 응답 결과(Postman/Swagger)나 실행 결과 스크린샷을 첨부해주세요. -->

- 사용자가 로컬 실행 후 화면 확인 완료
- `cmd.exe /c pnpm.cmd lint` 통과
    - 기존 `components/fallback-image.tsx`의 `<img>` 사용 warning 1개는 유지
- `cmd.exe /c pnpm.cmd build` 통과
- `cmd.exe /c pnpm.cmd exec tsc --noEmit` 통과

## 비고

- PowerShell에서 `pnpm lint` 직접 실행 시 실행 정책 때문에 `pnpm.ps1` 로드가 막혀 `pnpm.cmd`로 검증했습니다.
- 실제 신규 WebSocket 이벤트와 history REST 응답은 백엔드 구현 완료 후 통합 테스트가 필요합니다.
- 백엔드가 통합 history endpoint 대신 분리 endpoint를 제공하면 `getDrainAnalysisHistory` 내부 구현만 조정하면 됩니다.
- XGBoost가 참조한 YOLO 결과와 최신 YOLO 이미지가 달라질 수 있으므로, 이후 필요하면 “최신 YOLO”와 “최종 판단 참조 YOLO”를 더 명확히 구분하는 UI를 보강할 수 있습니다.

## 변경 파일

| 파일                                                                  | 내용                                                |
| --------------------------------------------------------------------- | --------------------------------------------------- |
| `frontend/docs/plans/plan-06-realtime-analysis-contract-detail-ui.md` | 구현 전 계획과 사용자 확인 항목 기록                |
| `frontend/docs/steps/step-08-realtime-analysis-contract-detail-ui.md` | 변경 이유, 선택 근거, 검증 결과 기록                |
| `frontend/docs/pr/pr-11-realtime-analysis-contract-detail-ui.md`      | PR 요약 문서                                        |
| `frontend/lib/api/types.ts`                                           | 신규 이벤트/이력 타입 추가                          |
| `frontend/lib/api/drains.ts`                                          | 분석 이력 API 함수 추가                             |
| `frontend/lib/api/drain-data.ts`                                      | 상세 데이터 로딩에 분석 이력 추가                   |
| `frontend/lib/api/mock-responses.ts`                                  | mock 분석 이력 추가                                 |
| `frontend/lib/websocket/drain-status-socket.ts`                       | WebSocket 이벤트 분기 확장                          |
| `frontend/components/cctv-snapshot-card.tsx`                          | 고정 높이 CCTV 뷰어와 이력 썸네일 개선              |
| `frontend/app/drains/[id]/page.tsx`                                   | 상세 요약 카드, AI 판단 탭, 실시간 이벤트 반영 추가 |
