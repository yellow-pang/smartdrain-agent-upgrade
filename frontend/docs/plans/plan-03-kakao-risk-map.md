# 03_kakao risk map 계획

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/kakao-risk-map` |
| 작업 범위 | `/frontend` 내부 |
| 작업 목적 | 임시 SVG 지도에서 Kakao Maps SDK 기반 위험도 지도로 전환 |
| 사용자 확인 완료 | `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 환경변수 추가, `react-kakao-maps-sdk` 설치 |

이번 작업은 기존 대시보드의 지도 컴포넌트 props 흐름을 유지하면서, 실제 API의 위도/경도 값을 Kakao Maps 마커로 표시하는 데 집중한다.

초기 MVP에서는 마커 수가 적지만 실제 서비스에서는 하수구와 카메라 위치가 크게 늘어날 수 있다. 그래서 단순 script 직접 제어보다 React 컴포넌트 방식과 클러스터링 확장이 쉬운 `react-kakao-maps-sdk`를 사용한다.

```text
GET /api/drains 위도/경도
→ lib/api/adapters.ts UI 데이터 변환
→ components/risk-map.tsx
→ react-kakao-maps-sdk Map / MarkerClusterer / MapMarker
→ Kakao Maps 지도 / 위험도별 마커 / 클릭 선택
→ SDK 또는 키 문제 시 fallback
```

## 2. 설치 방식 선택 비교

| 방식 | 장점 | 단점 | 현재 프로젝트 판단 |
|---|---|---|---|
| 직접 SDK 로드 | Kakao 공식 Web API 기본 방식과 가깝고 새 패키지가 필요 없다. 원본 API를 직접 제어할 수 있다. | `window.kakao.maps` 직접 접근, marker cleanup, overlay, clusterer 제어 코드를 직접 관리해야 한다. 지도 기능이 커질수록 컴포넌트가 길어진다. | 단순 MVP 지도만 있으면 가능하지만, 대량 마커와 유지보수를 고려하면 부담이 커진다. |
| `react-kakao-maps-sdk` | `Map`, `MapMarker`, `MarkerClusterer`, `CustomOverlayMap` 등 React 컴포넌트로 지도 UI를 구성할 수 있다. 마커/클러스터/오버레이 확장에 유리하다. | 새 의존성이 추가되고, Kakao 공식 패키지가 아닌 커뮤니티 wrapper라 버전 호환성 검증이 필요하다. | SmartDrain은 하수구와 카메라 마커가 많아질 가능성이 높으므로 이 방식을 선택한다. |

추천 선택은 `react-kakao-maps-sdk`이다. MVP 단계의 구현량은 조금 늘지만, 실제 서비스에서 밀집 마커와 클러스터링이 필요해질 가능성이 높기 때문이다.

## 3. 할 일

| 구분 | 작업 |
|---|---|
| 의존성 | `react-kakao-maps-sdk`, `kakao.maps.d.ts` 설치 |
| Kakao SDK | `useKakaoLoader`로 Kakao Maps JavaScript SDK와 `clusterer` 라이브러리 로딩 |
| 환경변수 | `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`를 사용해 SDK appkey 주입 |
| 데이터 | `DrainFacility`에 `latitude`, `longitude`를 포함하고 adapter에서 API 좌표 유지 |
| 지도 | `Map` 컴포넌트 생성, 시설 좌표 기준 중심점 계산, selectedId 변경 시 중심 이동 |
| 마커 | 위험도별 색상 마커 표시: 위험 red, 주의 amber, 정상 green, 판단불가 slate |
| 클러스터 | `MarkerClusterer`로 많은 시설 마커를 묶어 표시할 수 있는 구조 적용 |
| 클릭 | `MapMarker` 클릭 시 기존 `onSelect(id)` 흐름으로 목록/상세 패널과 연동 |
| fallback | SDK 로딩 실패, app key 없음, 좌표 없음, Kakao 객체 없음 상황에서 기존 임시 지도 또는 placeholder 표시 |
| 이미지 | 잘못된 이미지 URL 로딩 실패 시 깨진 이미지 대신 placeholder로 대체 |
| 검증 | `npm run lint`, `npm run build` 실행 |

## 4. 제외할 일

| 제외 항목 | 이유 |
|---|---|
| 상세 페이지 대규모 수정 | 사용자 요청 제외 범위 |
| WebSocket | 사용자 요청 제외 범위 |
| API 연동 방식 변경 | 기존 `loadDashboardData` 흐름 유지 |
| 라우팅 구조 변경 | 지도 컴포넌트 내부와 데이터 타입만 수정 |

## 5. 사용자 확인 항목

| 항목 | 추천 방향 | 이유 |
|---|---|---|
| `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 추가 | 추가 진행 | Kakao Maps SDK가 실제 지도를 표시하려면 JavaScript 키가 필요하다. 키가 없으면 fallback UI를 표시한다. |
| `react-kakao-maps-sdk` 설치 | 설치 진행 | 대량 마커, 클러스터링, 오버레이 유지보수를 React 컴포넌트 방식으로 처리하기 위함이다. |

## 6. 남은 리스크

| 리스크 | 대응 |
|---|---|
| 로컬에 Kakao JavaScript 키가 없음 | `.env.local`에 키를 넣기 전까지 fallback UI 표시 |
| Kakao 도메인 등록 누락 | SDK 로딩 또는 지도 인증 실패 시 fallback UI 표시 |
| API 좌표가 잘못됨 | 좌표 유효성 검사 후 유효한 좌표만 마커 표시 |
| wrapper 버전 호환성 | `npm run lint`, `npm run build`로 Next 16 / React 19 조합 검증 |
| 외부 이미지 URL 실패 | `onError`에서 placeholder 경로로 교체 |
