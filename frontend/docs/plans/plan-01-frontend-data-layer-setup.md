# 01_frontend data layer setup 계획

## 1. 작업 개요

| 항목      | 내용                                                                           |
| --------- | ------------------------------------------------------------------------------ |
| 브랜치    | `feature/frontend-data-layer-setup`                                            |
| 작업 목적 | 실제 백엔드 API가 확정되기 전 frontend 데이터 계층의 기준을 먼저 세운다.       |
| MVP 기준  | 2026-06-21까지 mock 기반으로도 화면과 데이터 흐름을 설명 가능한 상태로 만든다. |
| 확인일    | 2026-06-22                                                                     |
| 작업 범위 | `/frontend` 내부                                                               |

이번 브랜치에서는 화면 UI를 크게 바꾸기보다, 현재 mock 데이터에 직접 의존하는 구조를 실제 API 연동이 쉬운 구조로 나누는 데 집중한다.

분석 책임은 백엔드에 둔다. 백엔드는 센서 데이터와 빗물받이 이미지 기반 YOLO 분석 결과를 XGBoost에 전달해 최종 위험도를 판단하고, 프론트엔드는 FastAPI가 내려주는 최종 결과를 화면에 표시한다.

---

## 2. 이번 브랜치에서 할 일

| 구분                | 작업                                          | 설명                                                                        |
| ------------------- | --------------------------------------------- | --------------------------------------------------------------------------- |
| API 타입 초안       | MVP 화면에 필요한 DTO 타입 정의               | 백엔드가 내려주는 빗물받이 목록, 상세, 센서, YOLO 결과, XGBoost 최종 판단, 위험 이력 타입을 임시로 정리한다. |
| mock/API 분리       | mock data와 API 후보 타입 분리                | mock은 화면 검증용, API 타입은 백엔드 연동 후보로 구분한다.                 |
| adapter             | API 후보 타입을 UI 표시 타입으로 변환         | 화면 컴포넌트가 API 응답 구조를 직접 알지 않도록 한다.                      |
| axios client 껍데기 | axios instance와 API 함수 구조 준비           | axios 설치는 완료되었고, 실제 endpoint가 확정되기 전까지 함수 이름과 반환 타입 중심으로 둔다. |
| 위험도 코드 정리    | `good / caution / danger / unknown` 기준 정리 | 문서 기준 위험도 코드와 현재 UI 상태 코드를 맞추는 방향으로 정리한다.       |

---

## 3. 작업하지 않을 것

이번 브랜치에서는 다음 작업을 하지 않는다.

| 제외 항목                 | 이유                                                  |
| ------------------------- | ----------------------------------------------------- |
| 실제 백엔드 endpoint 확정 | 백엔드 API 명세가 아직 확정되지 않았다.               |
| WebSocket 실제 연결       | 서버 이벤트 형식이 확정된 뒤 진행하는 것이 안전하다.  |
| Kakao Maps 실제 연동      | 이 브랜치는 데이터 계층 준비가 목적이다.              |
| 화면 전체 디자인 변경     | 데이터 구조 작업과 UI polish를 섞지 않는다.           |
| 상태 관리 라이브러리 도입 | 현재 범위에서는 React state와 helper 함수로 충분하다. |

---

## 4. 추천 파일 구조

현재 구조를 크게 흔들지 않고 `lib/api`를 추가하는 방향을 추천한다.

```text
frontend/lib/mock-data.ts
frontend/lib/api/types.ts
frontend/lib/api/client.ts
frontend/lib/api/drains.ts
frontend/lib/api/adapters.ts
frontend/lib/risk.ts
```

| 파일                  | 역할                                                                      |
| --------------------- | ------------------------------------------------------------------------- |
| `lib/api/types.ts`    | 백엔드 응답 후보 DTO와 공통 응답 타입을 둔다.                             |
| `lib/api/client.ts`   | axios instance를 둔다.                                                    |
| `lib/api/drains.ts`   | 빗물받이 목록, 상세 조회 함수 껍데기를 둔다.                              |
| `lib/api/adapters.ts` | API DTO 또는 mock DTO를 UI 표시 타입으로 변환한다.                        |
| `lib/risk.ts`         | 위험도 코드, 라벨, 색상 메타, 정렬 우선순위 같은 공통 위험도 로직을 둔다. |
| `lib/mock-data.ts`    | 화면 검증용 mock 데이터만 유지한다.                                       |

`lib/risk.ts`는 위험도 코드가 여러 컴포넌트에 흩어지는 것을 막기 위한 후보이다. 실제 수정 시 기존 `STATUS_META`, `RISK_RANK` 사용처를 확인하고 무리하게 큰 리팩터링은 하지 않는다.

---

## 5. 타입 설계 방향

### 5.1 위험도 코드

문서 기준 위험도 코드를 우선한다.

```ts
export type RiskLevel = "good" | "caution" | "danger" | "unknown";
```

기존 frontend mock은 `normal / warning / danger / unknown`을 사용했다. 이번 작업에서는 설계 문서에 맞춰 `good / caution / danger / unknown`으로 전체 변경한다.

| 적용 항목 | 기준 |
|---|---|
| 타입 | `RiskLevel = "good" \| "caution" \| "danger" \| "unknown"` |
| mock data | 기존 `normal`은 `good`, 기존 `warning`은 `caution`으로 변경 |
| UI 표시 | `good`은 `양호`, `caution`은 `주의`로 표시 |
| adapter | 백엔드 DTO와 UI 타입 모두 같은 위험도 코드를 사용 |

MVP 이후 백엔드와 맞추기 쉽도록 전체를 문서 기준으로 변경한다.

### 5.2 공통 응답 타입 초안

백엔드 공통 응답 형식이 아직 없으므로 확정 타입이 아니라 임시 타입으로 둔다.

```ts
export type ApiResponse<T> = {
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

목록 응답 후보는 다음 형태를 참고한다.

```ts
export type ApiListResponse<T> = ApiResponse<{
  items: T[];
  totalCount: number;
}>;
```

### 5.3 DTO 후보

MVP 화면 기준 최소 DTO만 먼저 둔다.

```ts
export type DrainListItemDto = {
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
```

상세 화면에 필요한 YOLO, XGBoost, 센서, 위험 이력 타입은 같은 파일에서 후보 타입으로 정리한다. 백엔드 명세가 확정되면 이 타입은 반드시 재검토한다.

---

## 6. axios client 방향

axios를 사용할 예정이므로 `fetch` helper는 만들지 않는다.

```ts
import axios from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  timeout: 10000,
});
```

주의할 점은 다음과 같다.

| 항목        | 기준                                                                                               |
| ----------- | -------------------------------------------------------------------------------------------------- |
| axios 설치  | 설치 완료. `package.json`과 lockfile 기준으로 axios를 사용할 수 있다.                              |
| 환경변수    | `NEXT_PUBLIC_API_BASE_URL` 이름을 후보로 둔다. 확정 전에는 문서와 코드 주석에서 후보임을 표시한다. |
| interceptor | 공통 응답 형식이 없으므로 처음에는 과하게 만들지 않는다.                                           |
| 인증 토큰   | MVP 범위에서는 인증이 제외되어 있으므로 토큰 로직은 넣지 않는다.                                   |
| 에러 처리   | 일단 axios error를 화면용 에러 상태로 바꾸는 helper 후보만 둔다.                                   |

---

## 7. adapter 방향

화면 컴포넌트는 API 응답 DTO를 직접 사용하지 않도록 한다.

```text
API DTO 또는 mock data
→ adapter
→ UI 표시용 타입
→ component props
```

adapter에서 처리할 내용은 다음과 같다.

| 변환 항목   | 설명                                                              |
| ----------- | ----------------------------------------------------------------- |
| 위험도 코드 | `good / caution / danger / unknown`으로 통일                      |
| 주소 필드   | `roadAddress`, `fullAddress`를 현재 UI가 쓰는 이름으로 변환       |
| 센서 단위   | `waterLevelCm`, `flowVelocityMps`를 화면 표시 단위로 변환         |
| 지도 좌표   | 실제 API의 위도/경도와 기존 mock 지도 좌표를 분리                 |
| 없는 값     | 이미지 없음, 분석 없음, 센서 없음 상태를 UI가 처리할 수 있게 유지 |

---

## 8. 작업 순서

| 순서 | 작업                       | 확인할 내용                                                  |
| ---- | -------------------------- | ------------------------------------------------------------ |
| 1    | 현재 mock data 사용처 확인 | `DRAINS`, `STATUS_META`, `RISK_RANK`, `RiskStatus` 참조 위치 |
| 2    | 위험도 코드 기준 결정      | 문서 기준으로 변경할지 adapter 변환으로 둘지                 |
| 3    | API 타입 파일 추가         | 임시 타입임을 주석 또는 문서로 명확히 표시                   |
| 4    | axios client 파일 추가     | 설치된 axios를 기준으로 instance와 API 함수 껍데기 작성       |
| 5    | adapter 파일 추가          | mock/API 후보 데이터를 UI 타입으로 변환                      |
| 6    | 기존 화면 연결 범위 결정   | 한 번에 전체 교체하지 않고 대시보드부터 적용                 |
| 7    | lint/build 검증            | `npm run lint`, `npm run build`                              |
| 8    | step 또는 PR 문서 작성     | 변경 흐름, 검증 결과, 남은 리스크 기록                       |

---

## 9. 사용자 확인 필요 목록

작업 전에 다음 항목은 사용자의 확인이 필요하다.

| 확인 항목                         | 추천                                              | 확인이 필요한 이유                                                                    |
| --------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------- |
| axios 설치 진행 여부              | 확인 완료                                         | 사용자가 설치를 완료했으므로 이번 브랜치에서는 axios 기준으로 진행한다. |
| 위험도 코드 변경 범위             | 확인 완료                                         | 설계 문서 기준에 따라 `good / caution / danger / unknown`으로 전체 변경한다. |
| API base URL 환경변수 이름        | `NEXT_PUBLIC_API_BASE_URL`                        | 환경변수 추가 또는 이름 변경은 사용자 확인 대상이다.                                  |
| 실제 endpoint 후보 코드 반영 범위 | 함수 껍데기만 작성                                | 백엔드 명세가 없으므로 endpoint를 확정처럼 박아두면 수정 비용이 커진다.               |
| mock data 구조 변경 허용 범위     | 필요한 범위만 변경                                | mock data 구조를 크게 바꾸면 현재 화면 전체에 영향을 줄 수 있다.                      |
| adapter 적용 범위                 | 대시보드와 상세 페이지 모두 적용                  | MVP 확인 전 데이터 흐름을 통일하려면 적용 범위를 정해야 한다.                         |
| 타입 검증 설정 변경 여부          | 이번 브랜치에서는 보류                            | `ignoreBuildErrors` 해제는 영향이 클 수 있어 별도 작업으로 분리하는 편이 안전하다.    |

확인 전에는 환경변수 파일 추가와 mock data 대규모 교체는 진행하지 않는다. axios 설치와 위험도 코드 기준은 확인되었으므로 코드 수정 범위에 포함한다.

---

## 10. 검증 기준

작업 후 다음 명령어를 실행한다.

```bash
npm run lint
npm run build
```

검증 결과는 step 문서 또는 PR 문서에 다음 형식으로 남긴다.

| 명령어          | 기대 결과  | 비고                                                            |
| --------------- | ---------- | --------------------------------------------------------------- |
| `npm run lint`  | error 없음 | 기존 `<img>` warning이 남을 수 있음                             |
| `npm run build` | 성공       | 현재 TypeScript validation은 `ignoreBuildErrors: true`로 건너뜀 |

---

## 11. 남은 리스크

| 리스크                 | 영향                                 | 대응                                             |
| ---------------------- | ------------------------------------ | ------------------------------------------------ |
| 백엔드 API 명세 미확정 | DTO와 endpoint 후보가 바뀔 수 있음   | adapter와 임시 타입으로 변경 범위 축소           |
| 공통 응답 형식 미확정  | axios 응답 처리 방식이 바뀔 수 있음  | interceptor를 최소화하고 반환 타입 중심으로 작성 |
| axios 미설치           | 해당 없음 | 설치 완료 상태를 기준으로 진행한다. |
| 위험도 코드 변경 영향  | 여러 컴포넌트와 mock data 수정 필요  | 사용처를 먼저 확인하고 작은 단위로 변경          |
| 타입 검증 비활성화     | 타입 오류를 빌드에서 놓칠 수 있음    | 별도 브랜치 또는 후속 작업으로 해제 검토         |

---

## 12. 추천 커밋 메시지

제목:

```text
docs: 프론트엔드 데이터 계층 작업 계획 추가
```

내용:

```text
- feature/frontend-data-layer-setup 브랜치의 작업 범위를 정리한다.
- API 타입 초안, mock/API 분리, adapter, axios client 준비 방향을 문서화한다.
- 작업 전 사용자 확인이 필요한 항목을 별도로 정리한다.
```
