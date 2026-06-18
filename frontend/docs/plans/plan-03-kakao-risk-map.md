# 03_kakao risk map 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/kakao-risk-map` |
| 작업 범위 | `/frontend` 내부 |
| 작업 목적 | 임시 SVG 지도에서 Kakao Maps SDK 기반 위험도 지도로 전환 |
| 사용자 확인 필요 | `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 환경변수 추가 여부 |

이번 작업은 기존 대시보드의 지도 컴포넌트 props 흐름을 유지하면서, 실제 API의 위도/경도 값을 Kakao Maps 마커로 표시하는 데 집중한다.

```text
GET /api/drains 위도/경도
→ lib/api/adapters.ts UI 데이터 변환
→ components/risk-map.tsx
→ Kakao Maps SDK 지도 / 위험도별 마커 / 클릭 선택
→ SDK 또는 키 문제 시 fallback
```

## 2. 할 일

| 구분 | 작업 |
|---|---|
| Kakao SDK | 브라우저에서 Kakao Maps JavaScript SDK를 동적으로 로딩 |
| 환경변수 | `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`를 사용해 SDK appkey 주입 |
| 데이터 | `DrainFacility`에 `latitude`, `longitude`를 포함하고 adapter에서 API 좌표 유지 |
| 지도 | 실제 Kakao 지도 생성, 시설 좌표 기준 중심점 계산, selectedId 변경 시 중심 이동 |
| 마커 | 위험도별 색상 마커 표시: 위험 red, 주의 amber, 정상 green, 판단불가 slate |
| 클릭 | Kakao 마커 클릭 시 기존 `onSelect(id)` 흐름으로 목록/상세 패널과 연동 |
| fallback | SDK 로딩 실패, app key 없음, 좌표 없음, Kakao 객체 없음 상황에서 기존 임시 지도 또는 placeholder 표시 |
| 이미지 | 잘못된 이미지 URL 로딩 실패 시 깨진 이미지 대신 placeholder로 대체 |
| 검증 | `npm run lint`, `npm run build` 실행 |

## 3. 제외할 일

| 제외 항목 | 이유 |
|---|---|
| 상세 페이지 대규모 수정 | 사용자 요청 제외 범위 |
| WebSocket | 사용자 요청 제외 범위 |
| 새 지도 패키지 설치 | Kakao SDK는 스크립트 로딩으로 처리 가능 |
| API 연동 방식 변경 | 기존 `loadDashboardData` 흐름 유지 |
| 라우팅 구조 변경 | 지도 컴포넌트 내부와 데이터 타입만 수정 |

## 4. 사용자 확인 항목

| 항목 | 추천 방향 | 이유 |
|---|---|---|
| `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 추가 | 추가 진행 | Kakao Maps SDK가 실제 지도를 표시하려면 JavaScript 키가 필요하다. 키가 없으면 fallback UI를 표시한다. |

## 5. 남은 리스크

| 리스크 | 대응 |
|---|---|
| 로컬에 Kakao JavaScript 키가 없음 | `.env.local`에 키를 넣기 전까지 fallback UI 표시 |
| Kakao 도메인 등록 누락 | SDK 로딩 또는 지도 인증 실패 시 fallback UI 표시 |
| API 좌표가 잘못됨 | 좌표 유효성 검사 후 유효한 좌표만 마커 표시 |
| 외부 이미지 URL 실패 | `onError`에서 placeholder 경로로 교체 |

