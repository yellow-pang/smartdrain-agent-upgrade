# 30 상세 지도·현재 위험 상태 패널 분리 결과

## 작업 목표

상세 route에 남아 있던 위치 지도와 현재 위험 상태 카드의 표시 책임을 전용 컴포넌트로 분리했다. 상세 데이터 요청, 최신 결과 선택, WebSocket 이벤트 병합은 route에 유지했다.

## 변경 내용

| 컴포넌트 | 새 위치 | 책임 |
| --- | --- | --- |
| `LocationMapCard` | `components/drain-detail/drain-detail-status-panels.tsx` | API source의 상세 지도, mock fallback 지도 placeholder, 주소 표시 |
| `CurrentRiskCard` | `components/drain-detail/drain-detail-status-panels.tsx` | 상태·막힘률·수위·유속·업데이트 시각·판정 결과 표시 |
| `RiskTile` | 같은 파일 내부 | 현재 위험 상태 카드의 공통 metric tile 표시 |

`CurrentRiskCard`는 `DrainFacility`만 받고 상태 메타를 내부에서 계산한다. `LocationMapCard`는 시설 정보와 상세 데이터 source만 받아, API 여부에 따른 지도/placeholder 분기를 담당한다.

## 유지한 동작

- `source === "api"`일 때 중심 고정 detail map을 표시하고, 그 외에는 기존 mock fallback placeholder를 표시한다.
- 위치 지도 카드의 고정 좌표 표시 방식, 주소, 카드 크기를 유지한다.
- 위험 상태별 배지·색상·막힘률 progress bar와 수위 cm·유속 m/s 표기를 유지한다.
- AI 탭의 요약 슬롯에는 분리된 `CurrentRiskCard`를 전달해 기존 기본 탭 표시를 유지한다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건, 기존 `components/fallback-image.tsx`의 `<img>` 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공. `/` 정적 생성 및 `/drains/[id]` 동적 route 확인 |

## 다음 단계

상세 route에 남은 mock fallback 화면과 보조 상태 UI를 정리한 뒤, 4단계인 입력 경계 보안·견고성 점검으로 진행한다. 점검 대상은 route parameter, 외부 이미지 URL, API/WS payload의 nullable·예상 밖 값 처리다.
