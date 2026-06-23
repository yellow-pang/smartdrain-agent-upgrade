# 33 CCTV 이미지 URL 허용 정책 조정 결과

## 작업 배경

실제 CCTV·S3 연동은 고도화 범위이며 현재 MVP에서 구현하지 않는다. 따라서 프론트엔드 이미지 fallback 정책은 실행 가능한 위험 스킴을 차단하되, 로컬 개발 자산과 향후 저장소 연동에 필요한 일반적인 이미지 URL 형식은 수용하도록 조정했다.

## 허용 범위

| 형식 | 허용 여부 | 용도 |
| --- | --- | --- |
| 앱 내부 절대 경로(`/...`) | 허용 | `frontend/public/`로 제공되는 정적 자산 |
| 상대 경로 | 허용 | 현재 페이지 기준으로 제공되는 개발 자산 |
| `http:` / `https:` | 허용 | 개발 서버, CDN, S3 공개 또는 presigned URL |
| `blob:` | 허용 | 브라우저에서 생성한 미리보기 이미지 |
| PNG/JPEG/WebP/GIF/AVIF base64 `data:` URL | 허용 | 제한된 로컬/임시 이미지 데이터 |
| `javascript:`, SVG를 포함한 그 외 `data:` 등 | 차단 | placeholder 이미지로 대체 |

## 구현

`FallbackImage`가 URL scheme과 이미지 data URL 형식을 확인한다. 허용하지 않은 값, 형식 오류 URL, 이미지 로딩 실패는 기존과 같이 placeholder로 대체한다.

프로젝트 source tree의 임의 폴더는 브라우저가 직접 읽지 못한다. 로컬 파일을 사용하려면 `frontend/public/` 아래에 두어 `/파일경로`로 참조하거나, 개발/백엔드 서버가 URL로 제공해야 한다.

## 검증 결과

| 명령어 | 결과 | 비고 |
| --- | --- | --- |
| `pnpm.cmd lint` | 통과 | 오류 0건, 기존 `<img>` 성능 경고 1건 유지 |
| `pnpm.cmd build` | 통과 | Next.js production build 성공 |

## 고도화 시 확인 사항

실제 CCTV 또는 S3 연동 시 공개 URL 또는 만료 시간이 있는 presigned `https` URL 정책, 접근 권한, 이미지 보존 기간, CDN 설정을 백엔드/인프라와 함께 확정한다.
