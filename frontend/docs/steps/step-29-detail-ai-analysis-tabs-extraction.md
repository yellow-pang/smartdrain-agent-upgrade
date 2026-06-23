# 29 상세 AI 분석 탭 컴포넌트 분리 결과

## 작업 목표

상세 route에 있던 AI 분석 탭의 상태 관리와 YOLO·XGBoost·분석 이력 표시를 전용 client 컴포넌트로 분리했다. route는 최신 분석 결과와 이력 배열을 선택해 전달하고, API 요청과 WebSocket 병합은 기존 위치에 유지했다.

## 변경 내용

| 구분 | 변경 전 | 변경 후 |
| --- | --- | --- |
| AI 탭 상태 | 상세 route 내부 `useState` | `components/drain-detail/ai-analysis-tabs.tsx` 내부 |
| YOLO/XGBoost 표시 | route 내부 표시 helper | 전용 탭 컴포넌트 내부 |
| 분석 이력 목록 | route 내부 이력·빈 상태 표시 | 전용 탭 컴포넌트 내부 |
| 최신 결과 선택 | 표시 컴포넌트가 `DrainDetailData` 전체를 직접 조회 | route가 최신 YOLO/XGBoost 결과를 선택해 props로 전달 |

`AiAnalysisTabs`는 요약 슬롯, 최신 YOLO/XGBoost 결과, YOLO/XGBoost 이력 배열만 받는다. 이를 통해 탭 UI가 상세 API 응답 전체와 분리되고, route의 데이터 병합 책임은 유지된다.

## 유지한 동작

- 요약·YOLO·XGBoost·이력 탭의 순서, 기본 선택 탭, 버튼 스타일을 유지한다.
- YOLO 상태, 막힘률·신뢰도, XGBoost 상태·참조 ID·최종 판단 문구의 표시 기준을 유지한다.
- 분석 이력의 최대 높이, 상태 색상, 날짜 형식, 빈 상태 메시지를 유지한다.
- 최신 결과 선택 순서와 WebSocket 이벤트가 상세 데이터에 반영되는 흐름은 route의 기존 helper를 그대로 사용한다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건, 기존 `components/fallback-image.tsx`의 `<img>` 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공. `/` 정적 생성 및 `/drains/[id]` 동적 route 확인 |

## 다음 단계

상세 route에 남은 지도·현재 위험 상태·fallback 표시 컴포넌트를 우선순위에 따라 분리하거나, 이후 4단계에서 이미지 URL·route parameter·API/WS payload 경계를 보안·견고성 관점으로 점검한다.
