# 31 프론트엔드 URL 입력 경계 보강 결과

## 작업 목표

시설 ID와 CCTV 이미지 URL처럼 API·WebSocket·사용자 경로에서 유입될 수 있는 값을 화면과 요청 경로에 사용할 때 안전한 형식으로 제한했다. 백엔드 인증·권한·서버 입력 검증은 프론트엔드 범위를 넘어가므로 이번 변경에는 포함하지 않았다.

## 변경 내용

| 대상 | 변경 | 효과 |
| --- | --- | --- |
| API 시설 ID 경로 | 모든 상세·센서·위험 이력·분석 API 경로에서 `encodeURIComponent(id)` 사용 | 공백, 슬래시, 예약 문자가 URL path 의미를 바꾸지 않게 한다. |
| 상세 페이지 링크 | `getDrainDetailHref()` 공통 helper로 시설 ID를 인코딩 | 알림·대시보드 요약·상세 패널의 링크가 같은 안전한 경로 생성 규칙을 사용한다. |
| 외부 이미지 URL | `FallbackImage`가 앱 내부·상대 경로, 명시적인 `http:`/`https:`, `blob:`, 안전한 이미지 `data:` URL을 허용 | protocol-relative URL(`//...`), 실행 스킴, SVG를 포함한 허용하지 않은 data URL은 placeholder로 대체한다. |

## 적용 파일

| 파일 | 변경 내용 |
| --- | --- |
| `lib/drain-route.ts` | 인코딩된 상세 시설 경로 생성 helper 추가 |
| `lib/api/drains.ts` | 시설 ID를 포함하는 API path 인코딩 |
| `components/fallback-image.tsx` | 이미지 URL protocol allowlist와 fallback 처리 추가 |
| `components/app-header.tsx` | 긴급 알림 상세 링크에 공통 helper 적용 |
| `components/dashboard/mobile-drain-inline-summary.tsx` | 모바일 상세 링크에 공통 helper 적용 |
| `components/drain-summary-panel.tsx` | 상세 패널 링크에 공통 helper 적용 |

## 유지한 동작

- 기존 `https` CCTV/샘플 이미지, 앱 내부·상대 경로, 브라우저에서 생성한 `blob:` URL, PNG/JPEG/WebP/GIF/AVIF base64 이미지는 표시된다.
- 이미지 로드 실패 시 기존처럼 fallback 이미지를 표시한다.
- 기존 시설 ID의 대시보드·알림·상세 패널 이동 경로는 같은 페이지를 가리킨다.
- API endpoint, query parameter, WebSocket 계약은 변경하지 않았다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건. `FallbackImage`의 `<img>` 관련 Next.js 성능 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공. `/` 정적 생성 및 `/drains/[id]` 동적 route 확인 |

## 남은 확인 사항

1. 실제 API에서 공백·예약 문자가 포함된 시설 ID를 사용한다면, 백엔드가 URL-decoding된 ID를 정상 처리하는지 통합 환경에서 확인한다.
2. 실제 CCTV 연동은 고도화 범위다. S3 등 외부 저장소는 브라우저에서 접근 가능한 `https` URL(공개 또는 만료 시간 있는 presigned URL)로 제공되는지 통합 단계에서 확인한다.
3. 프로젝트 로컬 이미지는 브라우저가 source tree 임의 경로를 직접 읽을 수 없으므로 `frontend/public/` 아래에 두거나 서버가 URL로 제공한다.
4. API/웹소켓 payload의 런타임 스키마 검증은 백엔드 계약 확정과 함께 별도 단계로 검토한다.
