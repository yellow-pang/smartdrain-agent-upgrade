# 04_kakao risk map 작업 기록

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feat/kakao-risk-map` |
| 작업 범위 | `/frontend` 내부 |
| 작업 목적 | 임시 지도 UI를 Kakao Maps SDK 기반 지도 연동 구조로 변경 |
| 제외 범위 | 상세 페이지 대규모 수정, WebSocket |

이번 작업은 기존 대시보드와 상세 위치 카드가 사용하던 `RiskMap` props 흐름을 유지하면서 내부 구현을 `react-kakao-maps-sdk` 기반으로 교체했다.

MVP에서는 마커 수가 적지만 실제 서비스에서는 하수구와 카메라 위치가 많이 늘어날 수 있다. 따라서 대량 마커와 클러스터링을 나중에 다시 갈아엎지 않도록 `MarkerClusterer`를 함께 적용했다.

```text
Drain DTO latitude/longitude
→ adapter에서 DrainFacility 좌표로 유지
→ RiskMap에서 useKakaoLoader로 Kakao Maps SDK 로딩
→ react-kakao-maps-sdk Map 생성
→ MarkerClusterer 안에 위험도별 MapMarker 표시
→ 위험도별 마커 표시
→ 마커 클릭 시 selectedId 갱신
```

## 2. 설치 방식 선택 기록

| 방식 | 장점 | 단점 | 판단 |
|---|---|---|---|
| 직접 SDK 로드 | Kakao 공식 Web API의 기본 script 방식과 가깝다. 새 패키지 없이 구현할 수 있다. 원본 API를 직접 제어할 수 있다. | `window.kakao.maps` 직접 접근, marker cleanup, overlay 생성, clusterer 연결을 모두 직접 관리해야 한다. 마커 수와 지도 기능이 늘수록 컴포넌트가 길어지고 실수 가능성이 커진다. | 작은 데모 지도에는 가능하지만 SmartDrain의 실제 서비스 확장에는 부담이 있다. |
| `react-kakao-maps-sdk` | `Map`, `MapMarker`, `MarkerClusterer`, `CustomOverlayMap`을 React 컴포넌트로 조합할 수 있다. 클러스터링과 오버레이가 화면 구조에 드러나 유지보수하기 쉽다. | 커뮤니티 wrapper라 Kakao 공식 패키지는 아니다. 패키지 설치와 lockfile 변경이 필요하고, Next/React 버전 호환성을 검증해야 한다. | 하수구와 카메라 마커가 많아질 가능성이 높으므로 선택했다. |

최종 선택은 `react-kakao-maps-sdk`이다. 지금은 MVP라 직접 SDK 로딩도 가능하지만, 실제 서비스에서는 시설 수가 늘고 지도 기능이 커질 가능성이 높아 React 컴포넌트 기반 구조가 더 낫다고 판단했다.

## 3. 마커 형태 선택 기록

기존 와이어프레임과 임시 지도 UI는 작은 점 형태의 위험도 마커를 사용했다. 이번 Kakao Maps 연동에서는 실제 지도 위의 클릭 가능한 시설 위치라는 의미가 더 잘 드러나도록 핀 형태의 SVG 마커를 적용했다.

| 방식 | 장점 | 단점 | 판단 |
|---|---|---|---|
| 기존 점 마커 | 화면이 가볍고 많은 시설을 한눈에 볼 때 덜 복잡하다. 위험도 색상만 빠르게 읽기 좋다. | 실제 지도 POI, 도로, 건물 정보 위에서는 클릭 가능한 시설이라는 느낌이 약할 수 있다. 선택 상태와 상세 이동 유도도 상대적으로 약하다. | 관제 화면에서 밀집 위험도를 훑는 용도에는 좋지만, 클릭 기반 상세 확인 흐름에는 약하다. |
| 핀 형태 마커 | 지도 서비스에서 익숙한 형태라 위치와 클릭 대상임이 명확하다. 선택 라벨, 상세 패널 연동, 클러스터링과 조합하기 쉽다. | 마커 수가 많으면 화면을 가릴 수 있고, 기존 와이어프레임과 시각적으로 달라진다. | SmartDrain은 시설 클릭과 상세 확인이 중요하므로 MVP에서는 핀 형태를 적용한다. |
| 줌 레벨별 혼합 | 축소 상태에서는 클러스터 또는 점, 확대 상태에서는 핀으로 보여 실제 서비스 확장성에 가장 좋다. | MVP에서 구현과 QA 범위가 늘어난다. | 실제 데이터가 늘어난 뒤 후속 개선 후보로 둔다. |

현재 선택은 **핀 형태 마커 + 클러스터링**이다. 기존 와이어프레임과 달라진 부분이 있으므로, 디자인/기획 관점에서 팀 회의가 필요하다.

팀 회의 확인 항목은 다음과 같다.

| 확인 항목 | 논의 이유 | 추천 방향 |
|---|---|---|
| 기존 와이어프레임의 점 마커를 유지할지 | 화면 밀도와 초기 디자인 의도 확인 필요 | 관제 밀도 표현이 우선이면 점 마커 유지 |
| Kakao 지도 위 핀 마커를 표준으로 볼지 | 실제 지도 서비스 사용성과 클릭 가능성이 좋아짐 | 시설 선택/상세 확인이 중요하면 핀 마커 유지 |
| 줌 레벨별 마커 형태를 나눌지 | 실제 서비스에서 하수구/카메라 마커가 많아질 가능성 높음 | 후속 개선으로 축소 시 클러스터/점, 확대 시 핀 검토 |
| 위험도 색상 기준 | 정상 green, 주의 amber, 위험 red 기준을 지도에서도 유지해야 함 | 기존 상태 색상 체계 유지 |
| 클러스터 스타일 | 클러스터 색상과 숫자 표기가 위험도 의미를 오해하게 만들 수 있음 | 클러스터는 개수 표현 중심, 위험도 대표 색상은 후속 정책 필요 |

이번 PR에서는 팀 회의 전까지 핀 형태를 임시 확정으로 둔다. 단, 마커 생성 로직이 `getMarkerImage` 함수에 모여 있어 점 마커나 줌 레벨별 마커로 바꾸는 후속 수정은 비교적 작게 처리할 수 있다.

## 4. 변경 내용

| 구분 | 변경 내용 |
|---|---|
| 의존성 | `react-kakao-maps-sdk@1.2.1`, `kakao.maps.d.ts@0.1.40` 설치 |
| Kakao SDK | `components/risk-map.tsx`에서 `useKakaoLoader`로 Kakao Maps JavaScript SDK 로딩 |
| 환경변수 | `.env.example`에 `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 추가 |
| 좌표 데이터 | `DrainFacility`에 `latitude`, `longitude` 추가 |
| adapter | API 응답의 `latitude`, `longitude` 값을 UI 데이터에 유지 |
| mock 데이터 | mock 시설 데이터에도 강남권 위도/경도 값을 추가 |
| 마커 | 위험도별 색상 마커를 SVG data URI로 생성 |
| 클러스터링 | `MarkerClusterer`로 축소 시 밀집 마커를 묶어 표시 |
| 클릭 | `MapMarker` 클릭 이벤트에서 기존 `onSelect(id)` 호출 |
| 선택 표시 | 선택된 마커는 진한 테두리와 `CustomOverlayMap` 라벨로 표시 |
| fallback | app key 없음, SDK 로딩 실패, 좌표 없음 상황에서 기존 임시 지도 표시 |
| 이미지 fallback | 잘못된 이미지 URL 로딩 실패 시 placeholder 이미지로 대체 |

## 5. Kakao Maps SDK 연동 방법

### 5.1 Kakao Developers에서 JavaScript 키 준비

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

### 5.2 frontend 환경변수 설정

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

### 5.3 패키지 설치

이 프로젝트는 `pnpm-lock.yaml`을 사용하므로 지도 패키지는 `pnpm add`로 설치했다.

```bash
pnpm add react-kakao-maps-sdk kakao.maps.d.ts
```

설치된 버전은 다음과 같다.

| 패키지 | 버전 | 역할 |
|---|---|---|
| `react-kakao-maps-sdk` | `1.2.1` | Kakao 지도 React 컴포넌트 wrapper |
| `kakao.maps.d.ts` | `0.1.40` | Kakao Maps TypeScript 타입 |

### 5.4 SDK 로딩 흐름

`RiskMap`은 `useKakaoLoader`로 Kakao SDK를 로딩한다.

```text
useKakaoLoader({
    appkey: NEXT_PUBLIC_KAKAO_MAP_APP_KEY,
    libraries: ["clusterer"],
})
```

`libraries: ["clusterer"]`를 함께 지정해 지도 SDK와 클러스터러 라이브러리를 같이 불러온다.

현재 구현의 주요 흐름은 다음과 같다.

| 단계 | 동작 |
|---|---|
| 1 | `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`가 있는지 확인 |
| 2 | 표시 가능한 `latitude`, `longitude` 좌표가 있는지 확인 |
| 3 | `useKakaoLoader`로 Kakao SDK와 clusterer 라이브러리 로딩 |
| 4 | `Map` 컴포넌트에 중심 좌표와 확대 레벨 전달 |
| 5 | `MarkerClusterer` 안에서 각 시설을 `MapMarker`로 표시 |
| 6 | `MapMarker` click event에서 `onSelect(drain.id)` 호출 |
| 7 | 선택된 시설은 `CustomOverlayMap`으로 라벨 표시 |

### 5.5 클러스터링 기준

대량 마커 상황을 고려해 다음 설정을 적용했다.

| 옵션 | 값 | 의도 |
|---|---|---|
| `averageCenter` | `true` | 클러스터 좌표를 포함 마커들의 평균 위치로 표시 |
| `minLevel` | `6` | 일정 수준 이상 축소됐을 때 클러스터링 적용 |
| `minClusterSize` | `8` | 8개 이상 밀집될 때 묶음 표시 |
| `gridSize` | `80` | 화면 픽셀 기준 넓은 격자로 근접 마커 묶기 |
| `calculator` | `[10, 50, 100, 500]` | 마커 수에 따라 클러스터 스타일 단계 구분 |

현재 mock 데이터는 10개 수준이라 클러스터링 효과가 크게 보이지 않을 수 있다. 실제 시설 데이터가 늘어나면 이 설정이 지도 가독성을 유지하는 기본 장치가 된다.

### 5.6 fallback 동작

다음 경우에는 화면이 깨지지 않도록 기존 임시 지도 UI를 표시한다.

| 상황 | fallback 메시지 |
|---|---|
| `NEXT_PUBLIC_KAKAO_MAP_APP_KEY` 없음 | Kakao Maps JavaScript 키가 없어 임시 지도를 표시 |
| 좌표 없음 또는 잘못된 좌표 | 사용 가능한 위도/경도 좌표가 없어 임시 지도를 표시 |
| SDK 로딩 실패 | Kakao Maps SDK를 불러오지 못해 임시 지도를 표시 |

fallback에서도 기존과 같이 위험도별 점 마커와 선택 라벨은 유지된다.

## 6. 이미지 placeholder 처리 방법

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

## 7. 변경 전/후

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 지도 | SVG 기반 임시 도로 배경 | `react-kakao-maps-sdk` 지도 우선, 실패 시 임시 지도 fallback |
| 마커 위치 | `x`, `y` 퍼센트 좌표 | API/mock의 위도/경도 좌표 |
| 마커 형태 | 점 형태 마커 | 핀 형태 SVG marker, 팀 회의 후 확정 필요 |
| 마커 색상 | Tailwind 점 색상 | 위험도별 SVG marker 색상 |
| 마커 클릭 | 버튼 클릭으로 선택 | `MapMarker` click event로 선택 |
| 대량 마커 대응 | 없음 | `MarkerClusterer` 적용 |
| 이미지 오류 | 깨진 이미지 아이콘 노출 가능 | placeholder 이미지로 자동 대체 |

## 8. 검증 결과

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 성공 | `<img>` 최적화 warning 1건 남음 |
| `npm run build` | 성공 | Next.js production build 성공 |

남은 lint warning은 `FallbackImage`가 native `<img>`를 사용하기 때문에 발생한다. 이번 작업은 이미지 깨짐 방지 로직 추가가 목적이라 유지했고, 추후 `next/image` 전환 작업에서 함께 정리할 수 있다.

## 9. 남은 리스크

| 리스크 | 설명 |
|---|---|
| 실제 Kakao 키 필요 | `.env.local`에 `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`가 없으면 임시 지도 fallback이 표시된다. |
| Kakao 도메인 등록 필요 | Kakao Developers Web 플랫폼에 `http://localhost:3000` 또는 배포 도메인을 등록해야 한다. |
| 실제 브라우저 지도 확인 필요 | 빌드 검증은 통과했지만, 외부 SDK는 실제 키와 네트워크 환경에서 최종 확인해야 한다. |
| 클러스터링 UX 조정 | 실제 시설 수와 밀집도에 따라 `minClusterSize`, `gridSize`, `minLevel` 조정이 필요할 수 있다. |
| 와이어프레임과 마커 형태 차이 | 기존 점 형태 와이어프레임과 핀 형태 구현이 달라 팀 회의에서 확정이 필요하다. |
| 클러스터 대표 위험도 정책 | 현재 클러스터는 개수 중심 표시이며, 클러스터 안에 위험 시설이 섞였을 때 대표 색상 정책은 후속 논의가 필요하다. |
| wrapper 의존성 | `react-kakao-maps-sdk`는 커뮤니티 wrapper이므로 Next/React major 업데이트 때 빌드 검증이 필요하다. |
| 이미지 최적화 warning | native `<img>` warning은 남아 있으며 별도 `next/image` 전환 작업으로 분리 가능하다. |

## 10. 추천 커밋 메시지

제목:

```text
feat: 카카오 지도 기반 위험도 지도 연동
```

내용:

```text
- react-kakao-maps-sdk로 배수 시설 위도/경도 마커를 표시한다.
- 위험도별 마커 색상, 선택 라벨, 마커 클릭 선택 흐름을 연결한다.
- 실제 서비스의 대량 마커를 고려해 MarkerClusterer 기반 클러스터링을 적용한다.
- SDK 키 누락, 좌표 누락, 로딩 실패 시 임시 지도 fallback을 표시한다.
- 이미지 로딩 실패 시 placeholder로 대체하는 공통 컴포넌트를 추가한다.
```
