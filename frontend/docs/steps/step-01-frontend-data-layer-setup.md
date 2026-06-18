# 01_frontend data layer setup 작업 기록

## 1. 작업 개요

| 항목 | 내용 |
|---|---|
| 브랜치 | `feature/frontend-data-layer-setup` |
| 작업 범위 | `/frontend` 내부 |
| 작업 목적 | 백엔드 API 명세 확정 전 데이터 계층의 타입, axios client, adapter 기준을 준비 |

이번 작업에서는 프론트엔드가 분석을 직접 수행하지 않는다는 전제를 명확히 했다. 백엔드는 센서 데이터와 YOLO 분석 결과를 XGBoost에 전달해 최종 위험도를 판단하고, 프론트엔드는 그 결과를 API 또는 WebSocket으로 받아 표시한다.

---

## 2. 변경 내용

| 구분 | 변경 내용 |
|---|---|
| 위험도 코드 | 기존 `normal / warning / danger / unknown`을 설계 문서 기준 `good / caution / danger / unknown`으로 정리 |
| 공통 위험도 로직 | `lib/risk.ts`에 위험도 타입, 라벨, 색상, 정렬 우선순위 추가 |
| mock data | mock 배수 시설과 위험 이력의 상태 코드를 `good / caution` 기준으로 변경 |
| API 타입 | `lib/api/types.ts`에 공통 응답, 빗물받이, 센서, YOLO, XGBoost, 위험 이력, WebSocket 이벤트 DTO 초안 추가 |
| axios client | `lib/api/client.ts`에 `apiClient` instance 추가 |
| API 함수 | `lib/api/drains.ts`에 빗물받이 목록, 상세, 센서 이력, 위험 이력 조회 함수 껍데기 추가 |
| adapter | `lib/api/adapters.ts`에 API DTO를 현재 UI 표시 타입으로 변환하는 함수 추가 |
| 문서 | plan 문서와 MVP 남은 작업 문서에 백엔드 분석 책임, axios 설치 완료, 위험도 코드 확정 내용을 반영 |

---

## 3. 데이터 흐름

```text
FastAPI 응답 DTO
→ adapter
→ UI 표시용 타입
→ 대시보드 / 상세 페이지 컴포넌트
```

현재 실제 API endpoint는 확정 전이므로 화면은 기존 mock 데이터를 계속 사용한다. 다만 API가 준비되면 `lib/api/drains.ts`의 axios 함수와 `lib/api/adapters.ts`의 변환 함수를 연결해 mock 의존도를 줄일 수 있다.

---

## 4. 검증 결과

| 명령어 | 결과 | 비고 |
|---|---|---|
| `npm run lint` | 성공 | 기존 `<img>` 최적화 warning 3건 유지 |
| `npm run build` | 성공 | Next 설정상 TypeScript validation은 건너뜀 |
| `.\node_modules\.bin\tsc.cmd --noEmit` | 성공 | 타입 검증 통과 |

`npm exec` 방식의 tsc 실행은 인자가 제대로 전달되지 않아 TypeScript 도움말만 출력되었다. 최종 타입 검증은 로컬 bin 직접 실행으로 확인했다.

---

## 5. 남은 리스크

| 리스크 | 설명 | 후속 대응 |
|---|---|---|
| 백엔드 API 명세 미확정 | endpoint, 응답 wrapper, 필드명이 바뀔 수 있음 | 백엔드 명세 확정 후 `lib/api/types.ts`, `lib/api/drains.ts`, adapter 재검토 |
| 지도 좌표 변환 임시 처리 | adapter에서 mock map 좌표 `x`, `y`를 임시 중앙값으로 둠 | Kakao Maps 연동 시 위도/경도를 직접 사용하도록 변경 |
| 화면 연결 미완료 | API 함수와 adapter는 준비했지만 화면은 아직 mock 데이터를 사용 | 다음 작업에서 대시보드부터 adapter 기반 데이터 흐름 적용 |
| 이미지 최적화 warning | `<img>` 사용 warning 3건 유지 | 별도 이미지 최적화 작업에서 `next/image` 전환 검토 |
| 타입 검증 설정 | `next.config.mjs`의 `ignoreBuildErrors: true` 유지 | 후속 브랜치에서 해제 여부 검토 |

---

## 6. 추천 커밋 메시지

제목:

```text
feat: 프론트엔드 데이터 계층 초안 추가
```

내용:

```text
- 위험도 코드를 good/caution/danger/unknown 기준으로 정리한다.
- API DTO, axios client, drains API 함수, adapter 초안을 추가한다.
- 백엔드 분석 결과를 프론트에서 표시하는 데이터 흐름을 문서화한다.
```
