## PR 제목

[feat] # 카카오 지도 기반 위험도 지도 연동

## 작업 내용

- 임시 SVG 지도 UI를 Kakao Maps 기반 지도 구조로 전환했습니다.
    - `react-kakao-maps-sdk`와 `kakao.maps.d.ts`를 추가했습니다.
    - `RiskMap`에서 `Map`, `MapMarker`, `CustomOverlayMap`, `MarkerClusterer`, `useKakaoLoader`를 사용하도록 구성했습니다.
    - API/mock 데이터의 `latitude`, `longitude`를 지도 마커 위치로 사용합니다.
- 실제 서비스 확장성을 고려해 클러스터링 구조를 적용했습니다.
    - 하수구와 카메라 마커가 많아질 가능성을 고려해 `MarkerClusterer`를 기본 적용했습니다.
    - 축소 시 밀집 마커를 묶어 표시할 수 있게 구성했습니다.
- 위험도별 마커와 선택 흐름을 연결했습니다.
    - 위험 `red`, 주의 `amber`, 정상 `green`, 판단불가 `slate` 계열 색상을 유지했습니다.
    - 마커 클릭 시 기존 `selectedId`, 목록, 상세 패널 흐름과 연결됩니다.
    - 선택된 시설은 라벨 오버레이로 위치를 강조합니다.
- fallback과 이미지 깨짐 방지 로직을 추가했습니다.
    - Kakao app key 없음, SDK 로딩 실패, 좌표 없음 상황에서는 기존 임시 지도 fallback을 표시합니다.
    - 잘못된 이미지 URL이 들어와도 깨진 이미지 대신 placeholder를 표시하는 `FallbackImage`를 추가했습니다.
- 선택지 비교와 설계 판단을 문서화했습니다.
    - 직접 SDK 로딩 방식과 `react-kakao-maps-sdk` 방식의 장단점을 `step-04`에 기록했습니다.
    - 기존 점 마커와 핀 형태 마커의 차이, 와이어프레임 변경 영향, 팀 회의 필요 항목을 기록했습니다.

## 주요 변경 파일

- `frontend/components/risk-map.tsx`
    - Kakao 지도 렌더링, 위험도별 마커, 마커 클릭, 선택 라벨, 클러스터링, fallback 처리
- `frontend/components/fallback-image.tsx`
    - 이미지 로딩 실패 시 placeholder로 대체
- `frontend/components/cctv-snapshot-card.tsx`
    - CCTV 메인 이미지와 썸네일에 이미지 fallback 적용
- `frontend/components/drain-summary-panel.tsx`
    - 시설 이미지에 이미지 fallback 적용
- `frontend/lib/mock-data.ts`
    - mock 시설 데이터에 위도/경도 추가
- `frontend/lib/api/adapters.ts`
    - API DTO의 위도/경도를 UI 데이터로 유지
- `frontend/lib/api/mock-responses.ts`
    - mock API 응답에서 시설 위도/경도 사용
- `frontend/.env.example`
    - `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 예시 추가
- `frontend/package.json`, `frontend/pnpm-lock.yaml`
    - `react-kakao-maps-sdk`, `kakao.maps.d.ts` 의존성 추가
- `frontend/docs/plans/plan-03-kakao-risk-map.md`
    - 설치 방식 선택 비교와 작업 계획 기록
- `frontend/docs/steps/step-04-kakao-risk-map.md`
    - SDK 연동 방법, 클러스터링 기준, 마커 형태 선택지, 팀 회의 필요 항목 기록

## 스크린샷 / 테스트 결과

| 구분 | 테스트 항목 | 결과 | 비고 |
|---|---|---|---|
| Lint | `npm run lint` | 통과 | `FallbackImage`의 native `<img>` 최적화 warning 1건 유지 |
| Build | `npm run build` | 통과 | Next.js production build 성공 |
| Kakao SDK | 실제 브라우저 지도 표시 | 확인 필요 | `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`와 Kakao Developers 도메인 등록 필요 |
| Fallback | app key 없음/좌표 없음/SDK 실패 | 코드 반영 | 임시 지도 fallback 표시 |
| 이미지 | 잘못된 이미지 URL | 코드 반영 | placeholder 이미지로 대체 |

## 리뷰 포인트

- 기존 와이어프레임은 점 형태 마커였지만, 이번 구현은 핀 형태 마커를 사용합니다.
    - 핀 형태는 클릭 가능한 시설 위치임이 명확합니다.
    - 점 형태는 밀집 관제 화면에서 더 가볍게 보일 수 있습니다.
    - 팀 회의에서 지도 마커 표준을 확정해야 합니다.
- 실제 서비스에서는 하수구와 카메라 마커가 많아질 가능성이 높습니다.
    - 현재는 `MarkerClusterer`를 기본 적용했습니다.
    - 실제 데이터 밀집도에 따라 `minClusterSize`, `gridSize`, `minLevel` 조정이 필요할 수 있습니다.
- 클러스터 색상 정책은 후속 논의가 필요합니다.
    - 현재 클러스터는 개수 중심 스타일입니다.
    - 클러스터 안에 위험/주의/정상 시설이 섞였을 때 대표 위험도 색상을 어떻게 표시할지 정책이 필요합니다.

## 비고

- WebSocket 연동과 상세 페이지 대규모 수정은 이번 범위에서 제외했습니다.
- Kakao Maps JavaScript 키는 공개 키 성격이지만, 실제 값은 `.env.local`에서 관리하고 `.env.example`에는 예시만 둡니다.
- 실제 지도 표시 확인을 위해 Kakao Developers Web 플랫폼에 로컬/배포 도메인을 등록해야 합니다.
- 팀 회의 전까지 마커 형태는 핀 형태를 임시 기준으로 두며, 필요 시 점 형태 또는 줌 레벨별 혼합 방식으로 조정할 수 있습니다.

