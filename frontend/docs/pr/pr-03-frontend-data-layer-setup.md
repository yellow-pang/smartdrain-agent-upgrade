## PR 제목

[feat] # 프론트엔드 데이터 계층 초안 추가

## 작업 내용

- 프론트엔드 데이터 계층 준비 작업을 추가했습니다.
  - 백엔드 API 명세 확정 전에도 프론트엔드가 데이터 흐름을 정리할 수 있도록 API 타입 초안을 추가했습니다.
  - axios 기반 API client 껍데기를 추가했습니다.
  - 빗물받이 목록, 상세, 센서 이력, 위험 이력 조회 함수 구조를 준비했습니다.
  - API DTO를 현재 UI 표시 타입으로 변환하는 adapter 함수를 추가했습니다.
- 위험도 코드를 설계 문서 기준으로 정리했습니다.
  - 기존 `normal / warning / danger / unknown` 기준을 `good / caution / danger / unknown`으로 변경했습니다.
  - `good`은 화면에서 `양호`, `caution`은 `주의`로 표시되도록 정리했습니다.
  - 위험도 라벨, 색상, 정렬 우선순위를 `lib/risk.ts`로 분리했습니다.
- 백엔드 분석 책임과 프론트 표시 책임을 문서에 반영했습니다.
  - 백엔드는 센서 데이터와 YOLO 분석 결과를 XGBoost에 전달해 최종 위험도를 판단합니다.
  - 프론트엔드는 FastAPI가 내려주는 최종 결과를 API 또는 WebSocket으로 받아 표시합니다.
- 작업 계획 문서와 작업 완료 문서를 작성했습니다.
  - 데이터 계층 작업 계획
  - 실제 변경 내용과 검증 결과 기록

## 주요 변경 파일

- `frontend/lib/risk.ts`
  - `RiskLevel` 타입 추가
  - 위험도별 라벨, 색상, 정렬 우선순위 추가
- `frontend/lib/api/types.ts`
  - 공통 응답 타입 초안 추가
  - 빗물받이 목록/상세 DTO 추가
  - 센서, YOLO, XGBoost, 위험 이력 DTO 추가
  - WebSocket 위험도 변경 이벤트 DTO 추가
- `frontend/lib/api/client.ts`
  - axios instance 추가
- `frontend/lib/api/drains.ts`
  - 빗물받이 목록, 상세, 센서 이력, 위험 이력 조회 함수 추가
- `frontend/lib/api/adapters.ts`
  - API DTO를 현재 UI 표시용 `DrainFacility` 형태로 변환하는 함수 추가
- `frontend/lib/mock-data.ts`
  - mock 위험도 상태값을 `good / caution / danger / unknown` 기준으로 변경
- `frontend/components/risk-map.tsx`
  - 지도 범례를 `위험 / 주의 / 양호 / 판단불가` 기준으로 변경
- `frontend/components/sensor-trend-chart.tsx`
  - 상태 배지 타입을 `caution` 기준으로 변경
- `frontend/docs/00_mvp_remaining_frontend_plan.md`
  - axios 설치 완료, 백엔드 분석 책임, 위험도 코드 정리 방향 반영
- `frontend/docs/plans/plan-01-frontend-data-layer-setup.md`
  - 데이터 계층 작업 계획과 사용자 확인 사항 정리
- `frontend/docs/steps/step-01-frontend-data-layer-setup.md`
  - 실제 작업 내용, 검증 결과, 남은 리스크 기록

## 스크린샷 / 테스트 결과

- 화면 디자인 변경이 아니라 데이터 계층 준비 작업이므로 별도 스크린샷은 없습니다.
- ESLint 검증을 진행했습니다.
  - 실행 명령어: `npm run lint`
  - 결과: 성공
  - 참고: 기존 `<img>` 사용 관련 warning 3건은 유지됩니다.
- production build 검증을 진행했습니다.
  - 실행 명령어: `npm run build`
  - 결과: 성공
  - 참고: 현재 `next.config.mjs` 설정상 TypeScript validation은 건너뜁니다.
- TypeScript 타입 검증을 별도로 진행했습니다.
  - 실행 명령어: `.\node_modules\.bin\tsc.cmd --noEmit`
  - 결과: 성공
  - 참고: `npm exec` 방식은 인자 전달 문제로 TypeScript 도움말만 출력되어 로컬 bin 직접 실행으로 확인했습니다.

## 비고

- 실제 백엔드 API 명세가 아직 확정되지 않았으므로 endpoint와 응답 wrapper는 임시 후보입니다.
- API 함수와 adapter는 준비했지만, 현재 화면은 아직 mock 데이터를 사용합니다.
- Kakao Maps 연동 시 adapter의 임시 mock 지도 좌표 `x`, `y` 처리 방식은 위도/경도 기반으로 다시 정리해야 합니다.
- `next.config.mjs`의 `typescript.ignoreBuildErrors: true`는 이번 PR에서 변경하지 않았습니다.
