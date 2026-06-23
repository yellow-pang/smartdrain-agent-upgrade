## PR 제목

[chore] Docker Compose 개발 환경과 same-origin 실행 기준 정비

## 작업 내용

- backend scheduler 설정 다섯 개를 root Compose 환경변수로 전달하도록 정리했습니다.
- AI service가 YOLO 모델 mount가 없거나, 일반 파일이 아니거나, 비어 있을 때 명확한 오류 로그와 함께 종료하도록 보강했습니다.
- 개발 Compose에서 AI 샘플 이미지 경로를 read-only로 명시 mount했습니다.
- Cloudflare Tunnel → Nginx → frontend/backend 구조에서 REST·WebSocket이 same-origin으로 동작하는 기준을 README와 `.env.example`에 기록했습니다.
- 현재 frontend API helper가 이미 `/api/*` 경로를 가지므로 Compose API base URL은 빈 값으로 유지했습니다. `/api`를 base URL로 지정하지 않습니다.

## 변경 흐름

```text
Browser HTTPS
  → Cloudflare Tunnel
  → 127.0.0.1:8099 Nginx
       ├─ /       → frontend
       ├─ /api/*  → backend
       └─ /ws/*   → backend
```

- REST: same-origin `/api/*`
- WebSocket: HTTPS에서 same-origin `wss://<현재-host>/ws/drains/status`
- CORS: 위 same-origin 요청에는 적용되지 않으며, backend 직접 호출 origin만 `COMPOSE_CORS_ORIGINS`에 JSON 배열로 관리

## 주요 변경 파일

| 구분 | 파일 |
| --- | --- |
| Compose 모델 검사 | `docker-compose.yml` |
| 개발 asset mount | `docker-compose.dev.yml` |
| 환경변수 안내 | `.env.example` |
| 실행·Tunnel 안내 | `README.md` |
| 계획·결과 기록 | `frontend/docs/plans/plan-22-*`, `frontend/docs/steps/step-22-*` |

## 검증 결과

- `docker compose --env-file .env.example -f docker-compose.yml -f docker-compose.dev.yml config --quiet` 통과
- backend `Settings`의 HTTPS CORS JSON 배열 → `list[str]` 파싱 확인
- `npm.cmd --prefix frontend run lint` 통과 (오류 0건, 기존 `<img>` warning 1건)
- REST API helper와 WebSocket URL 생성 로직을 소스 기준으로 확인
- Nginx `/api/`의 `proxy_pass http://backend:8000`가 `/api` 접두어를 보존하고, `/ws/`에 Upgrade 헤더가 설정된 것을 확인
- `git diff --check` 통과
- 컨테이너 build·기동, Tunnel 외부 HTTPS, seed, AI callback, HMR smoke test는 실행 환경에서 미완료

## 리뷰 포인트

- Jenkins/VM root `.env`의 모델 경로와 `127.0.0.1` bind 포트는 해당 실행 환경 값으로 유지되는지 확인합니다.
- Cloudflare Tunnel의 서비스 주소가 Nginx bind 포트와 일치하는지 확인합니다.
- 외부 도메인 접속 시 frontend가 backend의 `localhost:8000` 또는 내부 IP를 직접 요청하지 않는지 브라우저 Network 탭에서 확인합니다.
- AI 모델 경로가 파일이 아닌 디렉터리나 빈 파일일 때 AI service가 즉시 실패하는지 확인합니다.
