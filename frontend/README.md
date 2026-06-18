# SmartDrain Frontend

SmartDrain frontend는 도시 빗물받이와 배수구의 위험 상태를 확인하는 Next.js App Router 기반 대시보드입니다.

현재 `feat/drain-data-ui` 브랜치는 MVP API 명세 기준으로 메인 대시보드와 상세 화면의 하드코딩을 줄이고, API/mock adapter 데이터 흐름을 연결한 상태입니다.

## 로컬 실행

```bash
npm install
npm run dev
```

개발 서버가 뜨면 브라우저에서 아래 화면을 확인합니다.

```text
http://localhost:3000
http://localhost:3000/drains/DR-004
```

## 검증 명령어

```bash
npm run lint
npm run build
.\node_modules\.bin\tsc.cmd --noEmit
```

현재 확인된 기준은 다음과 같습니다.

| 명령어 | 기대 결과 | 비고 |
|---|---|---|
| `npm run lint` | 성공 | `<img>` 최적화 warning 3건은 남아 있음 |
| `npm run build` | 성공 | Next 설정상 build에서는 TypeScript validation을 건너뜀 |
| `.\node_modules\.bin\tsc.cmd --noEmit` | 성공 | 타입 검증용 |

## API 연결 방식

데이터 로딩 흐름은 다음 기준입니다.

```text
실제 REST API 응답
→ 실패 또는 base URL 없음
→ API 명세형 mock 응답
→ adapter
→ 화면용 데이터
```

실제 백엔드 API를 붙여서 테스트하려면 환경변수에 API base URL을 지정합니다.

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

환경변수가 없거나 API 호출에 실패하면 `lib/api/mock-responses.ts`가 fallback 판단에 필요한 최소 데이터를 만들지만, 통합 테스트 화면에서는 mock 숫자와 mock 목록 row를 실제 데이터처럼 표시하지 않습니다. 이 경우 연결 대기, 연결 실패, placeholder 상태 UI를 표시합니다.

통합 테스트에서 실제 API 데이터 수신 여부를 구분하기 위해 fallback 상태의 주요 시각 영역은 placeholder 이미지를 표시합니다.

| 영역 | fallback 표시 | API 수신 시 기대 표시 |
|---|---|---|
| 대시보드 현황 | ErrorState + 다시 시도 버튼 | 전체/위험/주의/양호/판단불가 개수 |
| 메인 지도 | 지도 placeholder + `mock fallback` 배지 | 위험도 지도와 마커 |
| 위험 시설 목록 | 목록 전용 ErrorState + 다시 시도 버튼 | 정렬 가능한 실제 시설 목록 |
| 상세 위치 지도 | 위치 지도 placeholder + `mock fallback` 배지 | 선택 시설 위치 지도 |
| CCTV | CCTV placeholder 이미지 | API `imageUrl` 또는 분석 이미지 |
| 센서 차트 | 실시간 차트 placeholder + `mock fallback` 배지 | 수위/유량 라인 차트 |
| 상세 수치/이력/분석 | 연결 대기 상태 카드 | 실제 상세 수치, 위험 이력, 분석 결과 |

placeholder 이미지 위치는 다음과 같습니다.

```text
public/images/placeholder
```

## 주요 화면 점검

### 메인 대시보드

- 백엔드 API가 연결되지 않은 상태에서는 대시보드 현황에 mock 숫자가 아니라 연결 실패 상태와 다시 시도 버튼이 표시되는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 대시보드 현황 카드에 전체/위험/주의/양호/판단불가 개수가 표시되는지 확인합니다.
- 위험도 지도 마커와 범례 개수가 데이터 기준으로 맞는지 확인합니다.
- 백엔드 API가 연결되지 않은 상태에서는 지도 영역에 placeholder와 `mock fallback` 배지가 보이는지 확인합니다.
- 백엔드 API가 연결되지 않은 상태에서는 위험 시설 목록이 mock rows가 아니라 연결 실패 상태와 다시 시도 버튼을 표시하는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 지도 영역이 placeholder가 아니라 실제 마커 UI로 바뀌는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 위험 시설 목록이 실제 API 목록 row로 바뀌는지 확인합니다.
- 위험 시설 목록 선택 시 우측 상세 패널이 같은 시설 정보로 바뀌는지 확인합니다.
- 상세 정보 페이지 이동 버튼이 `/drains/{id}`로 이동하는지 확인합니다.

### 상세 페이지

- 백엔드 API가 연결되지 않은 상태에서는 상세 위치 지도, 센서 차트, 시설 정보, 현재 위험 상태, 분석 결과, 위험 이력이 fallback 상태 UI로 보이는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 주소, 최근 업데이트, 상태, 막힘 정도, 수위, 유량이 선택한 시설 기준으로 표시되는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 센서 데이터 차트가 API sensor history 기준으로 렌더링되는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 CCTV 캡처 시간과 이미지가 분석 데이터 기준으로 표시되는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 YOLO 막힘 상태, YOLO 신뢰도, XGBoost 위험 점수, 최종 판단이 표시되는지 확인합니다.
- 백엔드 API가 연결된 상태에서는 과거 위험 이력이 상세 데이터 기준으로 표시되는지 확인합니다.

## 이번 브랜치 제외 범위

- Kakao Maps 실제 SDK 연결
- WebSocket 실제 연결
- 새 상태 관리 라이브러리 도입
- 이미지 컴포넌트 `next/image` 전환

## 관련 문서

- `docs/plans/plan-02-drain-data-ui.md`
- `docs/steps/step-02-drain-data-ui.md`
- `docs/pr/pr-05-drain-data-ui.md`
- `docs/api-spec/2026-06-18_mvp_api_spec_v1.md`
