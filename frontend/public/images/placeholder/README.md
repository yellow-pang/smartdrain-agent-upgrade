# 지능형 도시 침수 관리 대시보드 Placeholder 이미지 사용 가이드

이 폴더는 `지능형 도시 침수 관리 및 모니터링 시스템` 프론트엔드에서 API, 지도, CCTV, 실시간 센서 데이터가 아직 연결되지 않았거나 일시적으로 불러오지 못하는 경우 사용할 placeholder 이미지 모음입니다.

중요 원칙:
- 이미지는 일러스트/빈 상태 시각화 용도로 사용합니다.
- `연결 확인 중`, `다시 시도`, `데이터 없음` 같은 문구와 버튼은 이미지 안에 넣지 말고 React 컴포넌트로 별도 표시하는 것을 권장합니다.
- 상태 문구는 Badge, StatusChip, Alert, Button 등 shadcn/ui 컴포넌트로 처리합니다.
- 색상은 메인 UI의 상태 색상 규칙을 따릅니다.
  - 정상/일반: emerald 또는 green
  - 주의: amber 또는 orange
  - 위험: red
  - 판단불가/대기/비활성: gray 또는 slate

## 파일 목록 및 용도

| 파일명 | 권장 사용 위치 | 용도 | 권장 비율 |
|---|---|---|---|
| `01_placeholder_cctv_feed_unavailable.png` | CCTV 카드, CCTV 스냅샷 영역 | CCTV 피드, 최근 스냅샷, 이미지 URL이 아직 없거나 로딩 중일 때 표시 | 4:3 |
| `02_placeholder_map_unavailable.png` | 메인 지도 카드, 상세 위치 지도 카드 | Kakao/Naver 지도 API가 아직 연결되지 않았거나 위치 데이터가 없을 때 표시 | 4:3 |
| `03_placeholder_realtime_chart_unavailable.png` | 센서 데이터 추세 카드 | WebSocket 또는 실시간 센서 데이터가 아직 연결되지 않았을 때 차트 영역에 표시 | 16:9 |
| `04_placeholder_facility_detail_unavailable.png` | 우측 상세 정보 패널, 시설 정보 카드 | 시설이 선택되지 않았거나 상세 데이터를 불러오는 중일 때 표시 | 4:3 |
| `05_placeholder_thumbnail_unavailable.png` | CCTV 썸네일 리스트, 이미지 캐러셀 썸네일 | 특정 썸네일 이미지가 없거나 깨졌을 때 표시 | 1:1 |

## 컴포넌트 적용 예시

```tsx
<EmptyState
  image="/images/placeholder/01_placeholder_cctv_feed_unavailable.png"
  title="CCTV 피드 대기 중"
  description="최근 스냅샷을 불러오는 중입니다."
  statusLabel="연결 확인 중"
/>
```

```tsx
<EmptyState
  image="/images/placeholder/03_placeholder_realtime_chart_unavailable.png"
  title="실시간 센서 데이터 준비 중"
  description="서버 연결 후 차트가 자동으로 갱신됩니다."
  statusLabel="실시간 연결 대기"
/>
```

## 에이전트 작업 지시 예시

프론트엔드에서 각 카드의 데이터 로딩/대기/오류 상태에 따라 위 placeholder 이미지를 사용해주세요. 이미지 자체에 문구가 없으므로 제목, 설명, 상태 배지, 다시 시도 버튼은 React 컴포넌트로 따로 구현해주세요.

권장 처리 방식:
1. 최초 로딩: Skeleton UI 또는 Spinner 표시
2. 일정 시간 이상 데이터 없음: placeholder 이미지 + 안내 문구 + 상태 Badge 표시
3. 연결 실패: placeholder 이미지 + 오류 문구 + `다시 시도` Button 표시
4. 연결 성공: 실제 CCTV, 지도, 차트, 상세 데이터 표시
