# 00_MVP 기준 프론트엔드 남은 작업 정리

## 1. 문서 목적

이 문서는 2026-06-17 현재 SmartDrain frontend가 MVP 기준으로 어디까지 되어 있고, 앞으로 날짜별로 무엇을 해야 하는지 정리하기 위한 문서이다.

현재 frontend는 Next.js 기반 화면 뼈대와 mock 데이터 기반 대시보드가 구현되어 있다. 다만 MVP 성공 기준에 포함된 실제 API 연동, Kakao Maps 연동, WebSocket 실시간 갱신은 아직 남아 있다.

백엔드 API 명세와 공통 응답 형식은 아직 확정되지 않았다. 따라서 frontend는 실제 API가 나오기 전까지 화면과 데이터 형태를 분리하고, 임시 타입, axios client, adapter 구조를 먼저 준비하는 방향으로 진행한다.

MVP 구현 마감 기준은 2026-06-21이며, 2026-06-22에는 구현 상태를 확인할 예정이다. 따라서 2026-06-21까지는 실제 백엔드가 늦어지더라도 mock adapter 기반으로 대시보드, 상세 화면, 지도, 실시간 갱신 흐름을 설명 가능한 상태로 만들어야 한다.

분석 로직은 프론트엔드가 직접 수행하지 않는다. 백엔드가 센서 데이터와 빗물받이 이미지 기반 YOLO 결과를 XGBoost에 입력해 최종 위험도와 판단 결과를 만들고, 프론트엔드는 그 결과를 API 또는 WebSocket으로 받아 표시한다.

---

## 2. 현재 상태 요약

| 구분           | 현재 상태       | 판단                                |
| -------------- | --------------- | ----------------------------------- |
| 메인 대시보드  | 구현됨          | mock 데이터 기준 화면 확인 가능     |
| 위험 시설 목록 | 구현됨          | 정렬과 선택 UI 있음                 |
| 상세 요약 패널 | 구현됨          | mock 데이터 기준 표시               |
| 상세 페이지    | 구현됨          | 일부 값이 하드코딩되어 있음         |
| 센서 차트      | 구현됨          | mock 생성 데이터 기준 표시          |
| CCTV 이미지    | 구현됨          | 정적 이미지 기준 표시               |
| 지도           | 임시 지도 구현  | Kakao Maps API 미연동               |
| API 연동       | 미구현          | 백엔드 명세 확정 후 연결 필요       |
| WebSocket      | 미구현          | 이벤트 형식 확정 후 연결 필요       |
| 타입 검증      | 빌드에서 건너뜀 | `ignoreBuildErrors: true` 해제 필요 |
| 이미지 최적화  | 경고 있음       | `<img>`를 `next/image`로 전환 검토  |

---

## 3. MVP 기준 남은 핵심 작업

### 3.1 API 연동 준비

백엔드 코드가 아직 작성 중이므로 frontend에서 실제 endpoint를 확정하면 안 된다.

대신 다음 작업을 먼저 진행한다.

| 작업                      | 내용                                                                   | 우선순위 |
| ------------------------- | ---------------------------------------------------------------------- | -------- |
| API 타입 초안 작성        | 백엔드가 내려주는 빗물받이, 센서, YOLO 결과, XGBoost 최종 판단, 위험 이력 타입을 frontend 기준으로 정리 | 필수     |
| mock data와 API 타입 분리 | `mock-data.ts`의 화면용 구조와 실제 API 응답 후보 구조를 분리          | 필수     |
| adapter 함수 준비         | API 응답 후보를 현재 UI에서 쓰는 형태로 변환하는 함수 작성             | 필수     |
| axios client 껍데기 준비  | 실제 endpoint 없이 axios instance, 함수 이름, 반환 타입을 먼저 설계    | 권장     |
| 로딩/에러 상태 준비       | API가 실패하거나 비어 있을 때 보여줄 UI 상태 정리                      | 필수     |

추천 파일 구조는 다음과 같다.

```text
frontend/lib/mock-data.ts
frontend/lib/api/types.ts
frontend/lib/api/client.ts
frontend/lib/api/drains.ts
frontend/lib/api/adapters.ts
```

단, 실제 파일 생성은 백엔드 API 방향이 어느 정도 보이면 진행한다.

axios 설치는 완료되었으므로 API client는 다음 기준으로 준비한다.

```ts
import axios from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 10000,
});
```

백엔드 공통 응답 형식이 확정되기 전까지는 interceptor를 과하게 작성하지 않는다. 우선 `apiClient.get<ApiResponse<T>>()`처럼 반환 타입만 맞추고, 에러 메시지 정리와 토큰 처리 같은 공통 로직은 백엔드 응답 형식이 정해진 뒤 추가한다.

### 3.2 Kakao Maps API 연동

현재 `RiskMap`은 임시 SVG 기반 지도이다. MVP 문서에서는 Kakao Maps API 기반 지도 표시가 필수이다.

해야 할 작업은 다음과 같다.

| 작업                | 내용                                                | 우선순위 |
| ------------------- | --------------------------------------------------- | -------- |
| 환경변수 결정       | Kakao JavaScript 키 이름 정리                       | 필수     |
| SDK 로딩 방식 결정  | Next.js App Router에서 script 로딩 방식 정리        | 필수     |
| 실제 좌표 사용      | mock의 `x`, `y` 대신 위도/경도 기반 마커 표시       | 필수     |
| 마커 색상 표시      | 위험도별 마커 색상을 Kakao 지도 위에 표시           | 필수     |
| 마커 클릭 처리      | 클릭 시 선택 시설 변경, 상세 패널 갱신              | 필수     |
| 지도 로딩 실패 처리 | API key 누락 또는 SDK 로딩 실패 시 fallback UI 표시 | 권장     |

백엔드에서 빗물받이 위치를 내려줄 때 필요한 최소 필드는 다음과 같다.

```ts
type DrainLocation = {
  id: string;
  latitude: number;
  longitude: number;
  roadAddress: string;
  riskLevel: RiskLevel;
};
```

### 3.3 WebSocket 실시간 갱신

MVP 기준으로 위험도 변경 이벤트를 화면에 반영해야 한다.

해야 할 작업은 다음과 같다.

| 작업                  | 내용                                                         | 우선순위 |
| --------------------- | ------------------------------------------------------------ | -------- |
| 이벤트 타입 초안 작성 | 위험도 변경 이벤트의 최소 필드 정의                          | 필수     |
| 연결 상태 표시        | 연결됨, 끊김, 재연결 중 상태를 header 또는 대시보드에 표시   | 필수     |
| 대시보드 반영         | 지도 마커, 위험 시설 목록, 상세 요약 패널 갱신               | 필수     |
| 상세 페이지 반영      | 현재 보고 있는 시설의 상태가 바뀌면 상세 카드 갱신           | 필수     |
| 재연결 처리           | 연결이 끊겼을 때 일정 시간 후 재연결 시도                    | 권장     |
| fallback 처리         | WebSocket 실패 시 REST API 재조회 버튼 또는 자동 재조회 제공 | 권장     |

임시 이벤트 형태는 다음과 같이 잡을 수 있다.

```ts
type RiskChangedEvent = {
  eventType: "risk_changed";
  drainId: string;
  riskLevel: RiskLevel;
  riskScore: number;
  waterLevelCm?: number;
  flowVelocityMps?: number;
  obstructionRatio?: number;
  updatedAt: string;
};
```

### 3.4 상세 페이지 데이터 정리

현재 상세 페이지에는 일부 고정 문구와 날짜가 남아 있다.

해야 할 작업은 다음과 같다.

| 작업                    | 내용                                                                 | 우선순위 |
| ----------------------- | -------------------------------------------------------------------- | -------- |
| 하드코딩 제거           | 주소, 최근 업데이트 시간, 위험 이력을 선택 시설 데이터 기반으로 표시 | 필수     |
| CCTV 이미지 데이터 연결 | 시설별 최신 이미지 URL 또는 sample image 경로 사용                   | 필수     |
| YOLO 결과 표시 강화     | 막힘 비율, confidence score, yolo status를 분리 표시                 | 필수     |
| XGBoost 결과 표시 강화  | risk score, risk level, final decision을 분리 표시                   | 필수     |
| 상세 API 오류 처리      | 상세 정보를 불러오지 못한 경우 안내 UI 표시                          | 필수     |
| 데이터 없음 처리        | 이미지 없음, 센서 없음, 분석 결과 없음 상태 표시                     | 필수     |

### 3.5 상태 코드 정리

문서 기준 위험도 내부 코드는 `good / caution / danger / unknown`이다. 기존 frontend mock은 `normal / warning / danger / unknown`을 사용했지만, 이번 데이터 계층 정리에서 `good / caution / danger / unknown`으로 맞춘다.

백엔드와 맞추기 전 frontend에서 다음 중 하나를 선택해야 한다.

| 선택지             | 장점               | 단점                     | 추천      |
| ------------------ | ------------------ | ------------------------ | --------- |
| 문서 기준으로 변경 | 백엔드/문서와 일치 | 기존 mock 수정 필요      | 추천      |
| 현재 코드 유지     | 수정량 적음        | 백엔드 연동 시 변환 필요 | 비추천    |
| adapter에서만 변환 | UI 영향 작음       | 코드값이 이중으로 존재   | 임시 가능 |

추천 방향은 `good / caution / danger / unknown`으로 통일하는 것이다.

---

## 4. API 명세 미확정 상황에서의 frontend 대응

백엔드 API 명세가 아직 확정되지 않은 상태에서는 frontend가 endpoint, 응답 필드명, 상태 코드를 임의로 확정하면 나중에 수정 비용이 커질 수 있다.

따라서 다음 원칙으로 진행한다.

1. 화면 컴포넌트는 API 응답을 직접 의존하지 않는다.
2. API 응답 후보 타입과 UI 표시용 타입을 분리한다.
3. API 응답을 UI 타입으로 바꾸는 adapter 함수를 둔다.
4. 공통 응답 형식은 임시 초안으로만 사용하고, 백엔드 확정 후 수정한다.
5. endpoint 경로는 문서에 후보로만 적고 코드에 과하게 박아두지 않는다.
6. HTTP 요청은 axios 기준으로 준비하되, 백엔드 명세가 나오기 전에는 client와 함수 껍데기만 만든다.

### 4.1 임시 공통 응답 형식 초안

백엔드와 합의 전까지 frontend에서 참고할 수 있는 임시 형태이다.

```ts
type ApiResponse<T> = {
  success: boolean;
  data: T | null;
  message?: string;
  error?: {
    code: string;
    message: string;
    detail?: unknown;
  };
  timestamp?: string;
};
```

목록 응답은 다음 형태를 후보로 둔다.

```ts
type ApiListResponse<T> = ApiResponse<{
  items: T[];
  totalCount: number;
}>;
```

페이지네이션이 필요해지면 다음 형태를 추가할 수 있다.

```ts
type ApiPageResponse<T> = ApiResponse<{
  items: T[];
  page: number;
  size: number;
  totalCount: number;
  totalPages: number;
}>;
```

### 4.2 임시 API 타입 초안

MVP 화면에서 필요한 최소 타입이다.

```ts
type RiskLevel = "good" | "caution" | "danger" | "unknown";

type DrainListItemDto = {
  id: string;
  roadAddress: string;
  fullAddress?: string;
  latitude: number;
  longitude: number;
  riskLevel: RiskLevel;
  riskScore: number;
  obstructionRatio: number;
  waterLevelCm: number;
  flowVelocityMps: number;
  updatedAt: string;
};

type DrainDetailDto = DrainListItemDto & {
  imageUrl?: string;
  yoloResult?: YoloResultDto;
  xgboostResult?: XgboostResultDto;
  sensorSummary?: SensorSummaryDto;
  riskHistory?: RiskHistoryDto[];
};

type YoloResultDto = {
  obstructionRatio: number;
  confidenceScore: number;
  yoloStatus: string;
  analyzedAt: string;
};

type XgboostResultDto = {
  riskScore: number;
  riskLevel: RiskLevel;
  finalDecision: string;
  predictedAt: string;
};

type SensorSummaryDto = {
  waterLevelCm: number;
  flowVelocityMps: number;
  measuredAt: string;
};

type SensorHistoryDto = {
  measuredAt: string;
  waterLevelCm: number;
  flowVelocityMps: number;
};

type RiskHistoryDto = {
  changedAt: string;
  riskLevel: RiskLevel;
  riskScore: number;
};
```

### 4.3 임시 endpoint 후보

아래 endpoint는 확정이 아니라 frontend 작업 기준을 맞추기 위한 후보이다.

| 목적                | Method | 후보 경로                          | 비고                         |
| ------------------- | ------ | ---------------------------------- | ---------------------------- |
| 빗물받이 목록 조회  | GET    | `/api/drains`                      | 대시보드 지도, 목록에서 사용 |
| 빗물받이 상세 조회  | GET    | `/api/drains/{id}`                 | 상세 페이지에서 사용         |
| 센서 이력 조회      | GET    | `/api/drains/{id}/sensors`         | 차트에서 사용                |
| 위험 이력 조회      | GET    | `/api/drains/{id}/risk-history`    | 상세 위험 이력에서 사용      |
| 최신 분석 결과 조회 | GET    | `/api/drains/{id}/analysis/latest` | YOLO, XGBoost 결과 표시      |
| WebSocket 연결      | WS     | `/ws/risk-events`                  | 위험도 변경 이벤트 수신      |

### 4.4 axios 함수 구조 초안

실제 endpoint가 확정되기 전까지는 아래와 같은 형태를 기준으로 잡는다.

```ts
export async function getDrains() {
  const response =
    await apiClient.get<ApiListResponse<DrainListItemDto>>("/api/drains");
  return response.data;
}

export async function getDrainDetail(id: string) {
  const response = await apiClient.get<ApiResponse<DrainDetailDto>>(
    `/api/drains/${id}`,
  );
  return response.data;
}
```

이 함수들은 화면 컴포넌트에서 직접 호출하기보다, 필요하면 hook 또는 loader 역할 함수에서 호출한다. 화면 컴포넌트는 `DrainFacility` 같은 UI 표시용 타입을 받고, API 응답을 화면 타입으로 바꾸는 책임은 adapter에 둔다.

---

## 5. 날짜 기준 작업 계획

프로젝트 기준 전체 일정은 2026-06-15부터 2026-07-01까지이고, 발표일은 2026-07-02이다. 다만 frontend MVP는 2026-06-21까지 구현 가능한 상태로 만들고, 2026-06-22에 확인하는 것을 기준으로 한다.

### 5.1 2026-06-17 현재

| 상태 | 내용                                    |
| ---- | --------------------------------------- |
| 완료 | Next.js 프로젝트 생성                   |
| 완료 | 메인 대시보드 UI                        |
| 완료 | 상세 페이지 UI                          |
| 완료 | mock 데이터 기반 지도, 목록, 차트, 카드 |
| 남음 | 실제 API 연동                           |
| 남음 | Kakao Maps API 연동                     |
| 남음 | WebSocket 실시간 갱신                   |
| 남음 | 상세 페이지 하드코딩 제거               |
| 남음 | 타입 검증 활성화                        |

### 5.2 2026-06-18: API 연동 준비와 데이터 구조 정리

| 작업                        | 상세 내용                                                   | 완료 기준                     |
| --------------------------- | ----------------------------------------------------------- | ----------------------------- |
| 위험도 코드 정리            | `good / caution / danger / unknown` 기준으로 타입과 mock 데이터 정리 | 설계 문서와 코드 기준 일치 |
| API 타입 초안 작성          | DTO 타입, 공통 응답 타입, 이벤트 타입 초안 작성             | 타입 파일 또는 문서 기준 준비 |
| axios client 구조 정리      | `apiClient`, API 함수 파일, adapter 파일 역할 정리          | axios 기준 연동 방향 확정     |
| mock adapter 설계           | mock 데이터를 API 응답처럼 변환하거나 UI 타입으로 변환      | UI가 데이터 출처와 분리됨     |
| 상세 페이지 하드코딩 목록화 | 고정 주소, 고정 시간, 고정 이력을 모두 확인                 | 제거 대상 정리                |
| 로딩/에러 UI 방향 정리      | 목록 없음, 상세 없음, 이미지 없음, API 오류 표시 방식 결정  | 화면별 fallback 기준 작성     |

백엔드 명세가 아직 없다면 이 단계에서는 실제 API 호출을 완성하려고 하지 않는다. axios instance, 함수 이름, 반환 타입, adapter만 먼저 잡는다.

### 5.3 2026-06-19: 상세 화면과 차트 데이터 정리

| 작업                   | 상세 내용                                     | 완료 기준                |
| ---------------------- | --------------------------------------------- | ------------------------ |
| 상세 데이터 연결       | 선택한 시설별 이미지, 센서, 분석 결과 표시    | 하드코딩 제거            |
| 센서 차트 입력 분리    | 24시간, 7일 데이터 입력을 props 기반으로 변경 | API 데이터로 교체 가능   |
| YOLO 결과 카드 정리    | 막힘 비율, confidence score, yolo status 표시 | AI 결과 설명 가능        |
| XGBoost 결과 카드 정리 | 위험 점수, 등급, 최종 판단 표시               | 최종 위험 판단 설명 가능 |
| 데이터 없음 UI         | 이미지 없음, 센서 없음, 분석 없음 표시        | 예외 상황 시연 가능      |

### 5.4 2026-06-20: Kakao Maps 연동

| 작업                 | 상세 내용                                  | 완료 기준                         |
| -------------------- | ------------------------------------------ | --------------------------------- |
| Kakao SDK 로딩       | Next.js에서 Kakao Maps JavaScript SDK 로딩 | 개발 환경에서 지도 표시           |
| 좌표 기반 마커 표시  | 위도/경도 기반으로 빗물받이 위치 표시      | mock 좌표가 실제 지도 좌표로 표시 |
| 위험도별 마커 스타일 | 상태별 색상 구분                           | 양호, 주의, 위험, 판단불가 구분   |
| 마커 선택 연동       | 마커 클릭 시 목록, 상세 패널 갱신          | 기존 선택 흐름 유지               |
| SDK 실패 처리        | key 누락 또는 로딩 실패 시 안내 표시       | 빈 화면 방지                      |

Kakao API key가 늦어지면 임시 지도 유지, 실제 좌표 타입만 먼저 반영한다.

### 5.5 2026-06-21: MVP 마감 전 통합

| 작업                      | 상세 내용                                                         | 완료 기준                      |
| ------------------------- | ----------------------------------------------------------------- | ------------------------------ |
| axios/mock 전환 기준 확인 | 실제 API가 없으면 mock adapter로 화면 유지                        | 백엔드 지연에도 화면 시연 가능 |
| WebSocket 흐름 준비       | 실제 서버가 없으면 mock 이벤트 또는 timer 이벤트로 상태 변경 시연 | 실시간 갱신 흐름 설명 가능     |
| 대시보드 통합 확인        | 지도, 목록, 상세 요약 패널 선택 흐름 확인                         | 기본 사용자 흐름 성공          |
| 상세 페이지 통합 확인     | 이미지, 센서 차트, YOLO, XGBoost, 위험 이력 확인                  | 상세 화면 설명 가능            |
| 빌드와 린트 확인          | `npm run build`, `npm run lint` 실행                              | MVP 확인 전 기본 검증 완료     |

2026-06-21까지는 실제 API가 완성되지 않아도 MVP 화면과 데이터 흐름을 확인할 수 있어야 한다. 실제 백엔드 연동이 불가능한 항목은 문서와 코드에서 mock fallback임을 명확히 남긴다.

### 5.6 2026-06-22: MVP 확인

| 작업                       | 상세 내용                                              | 완료 기준                      |
| -------------------------- | ------------------------------------------------------ | ------------------------------ |
| MVP 화면 확인              | 대시보드, 상세 페이지, 지도, 차트, 위험 상태 표시 확인 | 확인자에게 주요 흐름 설명 가능 |
| 백엔드 연동 가능 여부 확인 | API 명세, 공통 응답 형식, endpoint 확정 여부 확인      | axios 실제 연결 범위 결정      |
| 남은 리스크 정리           | API 미확정, WebSocket 미연동, Kakao key 이슈 등을 구분 | 이후 작업 우선순위 재정리      |
| 발표용 보완점 도출         | 화면 polish, 시연 데이터, fallback 필요 여부 정리      | 6월 23일 이후 개선 범위 확정   |

### 5.7 2026-06-23 ~ 2026-06-28: 확인 후 보완과 통합 개선

MVP 확인 이후에는 실제 백엔드 진행 상황에 맞춰 axios 연동 범위를 넓힌다.

| 작업                | 상세 내용                                        | 완료 기준                           |
| ------------------- | ------------------------------------------------ | ----------------------------------- |
| 실제 API 연결       | 확정된 endpoint부터 axios 함수 연결              | mock 의존 범위 축소                 |
| WebSocket 실제 연동 | 서버가 준비되면 실제 이벤트 연결                 | mock 이벤트 제거 또는 fallback 처리 |
| 반응형 점검         | 모바일, 태블릿, 데스크톱에서 겹침 확인           | 주요 화면 레이아웃 안정             |
| 상태 색상 점검      | 양호, 주의, 위험, 판단불가 색상 일관성 확인      | 화면별 색상 통일                    |
| 시연 데이터 구성    | 양호, 주의, 위험, 판단불가 케이스 준비           | 발표 시나리오 가능                  |
| 오류 상태 시연 준비 | API 오류, 이미지 없음, 센서 없음, WebSocket 끊김 | 백업 설명 가능                      |
| 이미지 최적화 검토  | `<img>` 경고를 `next/image`로 전환할지 결정      | lint 경고 제거 또는 사유 기록       |

### 5.8 2026-06-29 ~ 2026-07-01: 테스트와 발표 준비

| 작업               | 상세 내용                              | 완료 기준             |
| ------------------ | -------------------------------------- | --------------------- |
| production build   | `npm run build` 성공 확인              | 배포 가능 상태        |
| lint 확인          | `npm run lint` error 없음 확인         | 코드 품질 기준 통과   |
| 통합 테스트        | 대시보드에서 상세 페이지까지 흐름 확인 | 기본 사용자 흐름 성공 |
| 실시간 갱신 테스트 | 위험도 변경 이벤트 반영 확인           | MVP 실시간 기준 충족  |
| 발표 캡처 준비     | 화면 캡처, 시연 순서, 예외 백업 준비   | 발표 자료에 사용 가능 |

### 5.9 2026-07-02: 발표일

| 작업         | 상세 내용                                                            |
| ------------ | -------------------------------------------------------------------- |
| 시연 전 점검 | 개발 서버, 백엔드 서버, API key, mock fallback 확인                  |
| 기본 시연    | 지도에서 위험 시설 선택, 상세 페이지 이동, 분석 결과 설명            |
| 실시간 시연  | WebSocket 또는 mock 이벤트로 위험도 변경 반영                        |
| 한계 설명    | 실제 CCTV, 실제 센서, 대응 요청, 알림, LLM 요약은 고도화 범위로 설명 |

---

## 6. 화면별 남은 작업 체크리스트

### 6.1 메인 대시보드

- [ ] mock 데이터 의존 제거 또는 adapter 뒤로 숨기기
- [ ] Kakao 지도 표시
- [ ] 위도/경도 기반 마커 표시
- [ ] 위험도별 마커 색상 통일
- [ ] 위험도 필터 필요 여부 결정
- [ ] 새로고침 버튼 또는 재조회 흐름 추가
- [ ] API 오류 상태 표시
- [ ] WebSocket 연결 상태 표시

### 6.2 위험 시설 목록

- [ ] API 데이터 기반 목록 표시
- [ ] 위험도순, 최신순, 시설 ID순 정렬 유지
- [ ] 위험 또는 주의 시설 우선 표시 기준 확정
- [ ] 목록이 비어 있을 때 안내 UI 표시
- [ ] 최근 업데이트 지연 표시 기준 확정

### 6.3 상세 요약 패널

- [ ] 선택 시설 데이터 기반으로 모든 값 표시
- [ ] 이미지 없음 상태 처리
- [ ] 상세 페이지 이동 버튼 유지
- [ ] WebSocket 이벤트 수신 시 선택 시설 상태 갱신

### 6.4 상세 페이지

- [ ] 주소 하드코딩 제거
- [ ] 업데이트 시간 하드코딩 제거
- [ ] 시설별 위험 이력 표시
- [ ] 시설별 센서 차트 표시
- [ ] 시설별 CCTV 이미지 표시
- [ ] YOLO 결과 분리 표시
- [ ] XGBoost 결과 분리 표시
- [ ] 상세 API 오류 UI 표시
- [ ] 없는 ID 접근 시 처리 확인

### 6.5 공통

- [ ] 위험도 코드값 정리
- [ ] 공통 응답 타입 초안 작성
- [ ] axios client 구조 결정
- [ ] loading, error, empty 상태 기준 정리
- [ ] TypeScript 빌드 검증 활성화
- [ ] lint 경고 처리 또는 사유 기록

---

## 7. 검증 기준

작업 단계마다 다음 명령어를 기준으로 확인한다.

```bash
npm run lint
npm run build
```

현재 확인된 상태는 다음과 같다.

| 명령어          | 현재 결과  | 남은 이슈                                                  |
| --------------- | ---------- | ---------------------------------------------------------- |
| `npm run build` | 성공       | TypeScript validation은 `ignoreBuildErrors: true`로 건너뜀 |
| `npm run lint`  | error 없음 | `<img>` 사용 경고 3건                                      |

최종 MVP 전에는 다음 상태가 되어야 한다.

- `npm run build` 성공
- TypeScript build error 무시 설정 해제
- `npm run lint` error 없음
- 가능하면 lint warning도 제거
- 대시보드, 상세 페이지, WebSocket 흐름 수동 확인 완료

---

## 8. 우선순위 결론

가장 먼저 해야 할 일은 API 명세를 기다리면서도 frontend가 멈추지 않도록 데이터 구조를 분리하는 것이다.

추천 순서는 다음과 같다.

1. API 타입 초안과 adapter 구조 준비
2. axios client와 API 함수 껍데기 준비
3. 위험도 코드값을 문서 기준으로 정리
4. 상세 페이지 하드코딩 제거
5. Kakao Maps 연동
6. WebSocket 또는 mock 이벤트 흐름 준비
7. 로딩, 에러, 빈 데이터 상태 정리
8. 2026-06-21 MVP 마감 전 빌드와 린트 확인
9. 2026-06-22 확인 결과에 따라 실제 API 연동 범위 조정

백엔드 명세가 늦어지는 동안에는 실제 endpoint 호출 대신 mock adapter와 임시 타입으로 UI를 완성하고, 백엔드가 나오면 adapter와 axios API 함수만 교체하는 방향이 가장 안전하다.
