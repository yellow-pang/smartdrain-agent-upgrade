## PR 제목

[feat] SmartDrain 메타데이터 및 대시보드 최신 CCTV 이미지 연동 준비

## 작업 내용

- SmartDrain 서비스 목적에 맞게 전역 제목, 설명, 키워드, 앱 아이콘을 정비했습니다.
- Open Graph와 Twitter 공유 카드에 프로젝트 대표 이미지를 연결하고, `metadataBase`를 `https://smartdrain.healthq.store/`로 설정했습니다.
- 대시보드 시설 목록 DTO의 optional 필드 `latestImageUrl`, `latestImageCapturedAt`을 화면 모델에 반영했습니다.
- 선택 시설 패널이 `latestImageUrl`을 표시하고, `YOLO_RESULT_UPDATED` 이벤트 수신 시 목록 cache의 최신 이미지를 즉시 갱신하도록 했습니다.
- 이미지가 없는 경우 기존 placeholder fallback을 유지합니다.

## 프론트·백엔드 계약 확인

프론트에서 사용하는 목록 필드는 백엔드 커밋 `119b744b`의 `GET /api/drains` 응답과 일치합니다.

| 필드 | 프론트 사용처 | 백엔드 제공 기준 |
| --- | --- | --- |
| `latestImageUrl` | 대시보드 선택 시설의 초기 CCTV 이미지 | 가장 최근 YOLO 분석 결과의 이미지 URL, 없으면 `null` |
| `latestImageCapturedAt` | 최신 이미지 촬영 시각 보존 | 가장 최근 YOLO 결과의 `capturedAt`, 없으면 `null` |
| `YOLO_RESULT_UPDATED.payload.imageUrl` | 새 분석 결과의 실시간 이미지 갱신 | YOLO 분석 결과 저장 후 WebSocket 이벤트로 전달 |

최신 YOLO 결과는 `capturedAt` 우선, 동률 또는 누락 시 생성 시각을 보조 기준으로 정렬합니다.

## 변경 흐름

```text
GET /api/drains
  → latestImageUrl
  → 대시보드 선택 시설 패널 초기 이미지

YOLO_RESULT_UPDATED
  → imageUrl
  → React Query 시설 목록 cache 갱신
  → 선택 시설 패널 이미지 즉시 갱신
```

## 주요 변경 파일

| 구분 | 파일 |
| --- | --- |
| 전역 메타데이터 | `frontend/app/layout.tsx` |
| 목록 API DTO·화면 모델 | `frontend/lib/api/types.ts`, `frontend/lib/api/adapters.ts`, `frontend/lib/mock-data.ts` |
| 실시간 이미지 반영 | `frontend/components/realtime-drain-sync.tsx`, `frontend/components/dashboard/dashboard-main-content.tsx` |
| 이미지 자산 | `frontend/public/images/metaimage/smartdrain-icon.png`, `frontend/public/images/metaimage/smartdrain-og-image.png` |
| 작업 기록 | `frontend/docs/plans/plan-23-dashboard-metadata-image-chart.md`, `frontend/docs/steps/step-36-dashboard-latest-cctv-image-contract.md` |

## 검증 결과

- `npm.cmd run lint` 통과 — 오류 0건, 기존 `FallbackImage`의 `<img>` 성능 경고 1건 유지
- `npm.cmd run build` 통과 — Next.js production build 성공, `/`와 `/drains/[id]` route 생성 확인
- `git diff --check` 통과

## 병합 및 통합 확인 순서

1. 백엔드 PR(커밋 `119b744b`, `GET /api/drains` 최신 YOLO 이미지 필드 추가)을 대상 브랜치에 병합합니다.
2. 이 프론트 PR을 같은 대상 브랜치에 병합합니다.
3. 실제 `GET /api/drains` 응답에서 `latestImageUrl`, `latestImageCapturedAt`이 반환되는지 확인합니다.
4. 대시보드에서 시설을 선택해 초기 이미지가 표시되는지 확인합니다.
5. 새 YOLO 분석 후 `YOLO_RESULT_UPDATED` 이벤트로 이미지가 새로고침 없이 바뀌는지 확인합니다.

## 리뷰 포인트

- 백엔드의 최신 이미지 정렬 기준이 `capturedAt` 우선인지 확인합니다.
- 이미지 URL은 frontend의 `FallbackImage` 허용 정책에 맞는 앱 내부 경로 또는 `http(s)` URL인지 확인합니다.
- 실제 WebSocket payload에 `imageUrl`, `capturedAt`, `analyzedAt`, `updatedAt`이 모두 포함되는지 확인합니다.

## 이번 PR에서 제외한 작업

- 상세 센서 차트의 수위·유속 이중 Y축 및 단일 측정값 안내
- 기존 placeholder·이미지 파일의 미사용 여부 점검 및 삭제

두 항목은 `plan-23`의 남은 범위로 다음 작업에서 진행합니다.
