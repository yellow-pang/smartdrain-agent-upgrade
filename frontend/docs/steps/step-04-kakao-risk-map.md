# 04_kakao risk map 작업 기록

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/kakao-risk-map` |
| 작업 범위 | `/frontend` 내부 |
| 작업 목적 | 임시 지도 UI를 Kakao Maps SDK 기반 지도 연동 구조로 변경 |
| 제외 범위 | 상세 페이지 대규모 수정, WebSocket, 새 패키지 설치 |

이번 작업은 기존 대시보드와 상세 위치 카드가 사용하던 `RiskMap` props 흐름을 유지하면서 내부 구현만 Kakao Maps SDK 로딩 방식으로 교체했다.

```text
Drain DTO latitude/longitude
→ adapter에서 DrainFacility 좌표로 유지
→ RiskMap에서 Kakao Maps SDK 로딩
→ Kakao 지도 생성
→ 위험도별 마커 표시
→ 마커 클릭 시 selectedId 갱신
```

## 2. 변경 내용

| 구분 | 변경 내용 |
|---|---|
| Kakao SDK | `components/risk-map.tsx`에서 Kakao Maps JavaScript SDK를 동적으로 로딩 |
| 환경변수 | `.env.example`에 `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 추가 |
| 좌표 데이터 | `DrainFacility`에 `latitude`, `longitude` 추가 |
| adapter | API 응답의 `latitude`, `longitude` 값을 UI 데이터에 유지 |
| mock 데이터 | mock 시설 데이터에도 강남권 위도/경도 값을 추가 |
| 마커 | 위험도별 색상 마커를 SVG data URI로 생성 |
| 클릭 | Kakao marker click event에서 기존 `onSelect(id)` 호출 |
| 선택 표시 | 선택된 마커는 진한 테두리와 Kakao CustomOverlay 라벨로 표시 |
| fallback | app key 없음, SDK 로딩 실패, 좌표 없음 상황에서 기존 임시 지도 표시 |
| 이미지 fallback | 잘못된 이미지 URL 로딩 실패 시 placeholder 이미지로 대체 |

## 3. Kakao Maps SDK 연동 방법

### 3.1 Kakao Developers에서 JavaScript 키 준비

1. Kakao Developers 콘솔에 접속한다.
2. 사용할 애플리케이션을 선택하거나 새 애플리케이션을 만든다.
3. 앱 설정에서 JavaScript 키를 확인한다.
4. 플랫폼 설정에서 Web 플랫폼을 추가한다.
5. 로컬 개발 도메인을 등록한다.

```text
http://localhost:3000
```

배포 환경이 있다면 배포 도메인도 Web 플랫폼에 추가해야 한다.

```text
https://배포도메인
```

도메인이 등록되지 않으면 app key가 맞아도 Kakao 지도 인증이 실패할 수 있다.

### 3.2 frontend 환경변수 설정

`frontend/.env.example`에는 예시 값만 둔다.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_KAKAO_MAP_APP_KEY=your-kakao-javascript-key
```

실제 개발 환경에서는 `frontend/.env.local`에 JavaScript 키를 넣는다.

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_KAKAO_MAP_APP_KEY=발급받은_JavaScript_키
```

`NEXT_PUBLIC_` 접두사가 붙은 값은 브라우저 번들에서 접근할 수 있다. Kakao Maps JavaScript 키는 프론트엔드에서 사용되는 공개 키이므로 이 방식으로 사용한다.

환경변수를 바꾼 뒤에는 Next.js dev server를 재시작해야 한다.

```bash
npm run dev
```

### 3.3 SDK 로딩 흐름

`RiskMap`은 별도 npm 패키지를 설치하지 않고 브라우저에서 Kakao SDK script를 추가한다.

```text
https://dapi.kakao.com/v2/maps/sdk.js?appkey=${NEXT_PUBLIC_KAKAO_MAP_APP_KEY}&autoload=false
```

`autoload=false`를 붙였기 때문에 script 로드 후 `window.kakao.maps.load(callback)`으로 지도 API 초기화 완료 시점을 기다린다.

현재 구현의 주요 흐름은 다음과 같다.

| 단계 | 동작 |
|---|---|
| 1 | `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`가 있는지 확인 |
| 2 | 표시 가능한 `latitude`, `longitude` 좌표가 있는지 확인 |
| 3 | SDK script가 이미 있으면 재사용하고, 없으면 `document.head`에 추가 |
| 4 | SDK가 준비되면 `kakao.maps.Map` 생성 |
| 5 | 각 배수 시설 좌표에 `kakao.maps.Marker` 생성 |
| 6 | marker click event에서 `onSelect(drain.id)` 호출 |
| 7 | 선택된 시설은 `kakao.maps.CustomOverlay`로 라벨 표시 |

### 3.4 fallback 동작

다음 경우에는 화면이 깨지지 않도록 기존 임시 지도 UI를 표시한다.

| 상황 | fallback 메시지 |
|---|---|
| `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 없음 | Kakao Maps JavaScript 키가 없어 임시 지도를 표시 |
| 좌표 없음 또는 잘못된 좌표 | 사용 가능한 위도/경도 좌표가 없어 임시 지도를 표시 |
| SDK 로딩 실패 | Kakao Maps SDK를 불러오지 못해 임시 지도를 표시 |

fallback에서도 기존과 같이 위험도별 점 마커와 선택 라벨은 유지된다.

## 4. 이미지 placeholder 처리 방법

이미지 경로가 잘못되거나 외부 이미지가 로딩되지 않는 경우를 대비해 `components/fallback-image.tsx`를 추가했다.

```text
원본 imageUrl 로딩 시도
→ onError 발생
→ 실패한 src 기록
→ placeholder src로 교체
```

적용 위치는 다음과 같다.

| 파일 | fallback 이미지 |
|---|---|
| `components/cctv-snapshot-card.tsx` 메인 CCTV | `PLACEHOLDER_IMAGES.cctv` |
| `components/cctv-snapshot-card.tsx` 썸네일 | `PLACEHOLDER_IMAGES.thumbnail` |
| `components/drain-summary-panel.tsx` 시설 이미지 | `PLACEHOLDER_IMAGES.facility` |

## 5. 변경 전/후

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 지도 | SVG 기반 임시 도로 배경 | Kakao SDK 지도 우선, 실패 시 임시 지도 fallback |
| 마커 위치 | `x`, `y` 퍼센트 좌표 | API/mock의 위도/경도 좌표 |
| 마커 색상 | Tailwind 점 색상 | 위험도별 SVG marker 색상 |
| 마커 클릭 | 버튼 클릭으로 선택 | Kakao marker click event로 선택 |
| 이미지 오류 | 깨진 이미지 아이콘 노출 가능 | placeholder 이미지로 자동 대체 |

## 6. 검증 결과

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 성공 | `<img>` 최적화 warning 1건 남음 |
| `npm run build` | 성공 | Next.js production build 성공 |

남은 lint warning은 `FallbackImage`가 native `<img>`를 사용하기 때문에 발생한다. 이번 작업은 이미지 깨짐 방지 로직 추가가 목적이라 유지했고, 추후 `next/image` 전환 작업에서 함께 정리할 수 있다.

## 7. 남은 리스크

| 리스크 | 설명 |
|---|---|
| 실제 Kakao 키 필요 | `.env.local`에 `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`가 없으면 임시 지도 fallback이 표시된다. |
| Kakao 도메인 등록 필요 | Kakao Developers Web 플랫폼에 `http://localhost:3000` 또는 배포 도메인을 등록해야 한다. |
| 실제 브라우저 지도 확인 필요 | 빌드 검증은 통과했지만, 외부 SDK는 실제 키와 네트워크 환경에서 최종 확인해야 한다. |
| 이미지 최적화 warning | native `<img>` warning은 남아 있으며 별도 `next/image` 전환 작업으로 분리 가능하다. |

## 8. 추천 커밋 메시지

제목:

```text
feat: 카카오 지도 기반 위험도 지도 연동
```

내용:

```text
- Kakao Maps SDK를 동적으로 로딩해 배수 시설 위도/경도 마커를 표시한다.
- 위험도별 마커 색상, 선택 라벨, 마커 클릭 선택 흐름을 연결한다.
- SDK 키 누락, 좌표 누락, 로딩 실패 시 임시 지도 fallback을 표시한다.
- 이미지 로딩 실패 시 placeholder로 대체하는 공통 컴포넌트를 추가한다.
```

