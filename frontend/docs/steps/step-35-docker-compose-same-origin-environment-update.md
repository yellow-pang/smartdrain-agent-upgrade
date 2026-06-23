# 35 Docker Compose same-origin 실행 기준 보완 결과

## 작업 결과

Jenkins/VM의 Cloudflare Tunnel 환경에서 frontend, REST API, WebSocket이 Nginx 하나를 통해 same-origin으로 연결되는 기준을 문서화하고, AI 모델 mount 사전 검사를 강화했다.

```text
Browser https://smartdrain.healthq.store
  → Cloudflare Tunnel
  → 127.0.0.1:8099 (Nginx)
       ├─ /       → frontend
       ├─ /api/*  → backend
       └─ /ws/*   → backend
```

## 확인 및 변경 내용

| 항목 | 확인 결과 | 반영 내용 |
| --- | --- | --- |
| REST API base URL | API helper가 이미 `/api/*` 전체 경로를 사용 | Compose의 `COMPOSE_FRONTEND_API_BASE_URL`을 빈 값으로 유지하고, `/api` 설정 시 발생하는 `/api/api/...` 중복을 문서화 |
| WebSocket URL | HTTPS 페이지에서 현재 host 기준 URL을 생성 | `wss://<현재-host>/ws/drains/status`를 사용하며 Nginx `/ws/`가 Upgrade 헤더를 전달함을 문서화 |
| CORS | Nginx 경유 REST·WebSocket은 same-origin | backend 직접 호출이 필요한 경우에만 `COMPOSE_CORS_ORIGINS`에 HTTPS origin을 JSON 배열로 설정하도록 `.env.example`에 안내 추가 |
| AI 모델 검사 | 기존 검사는 파일 크기만 확인 | 일반 파일(`-f`)이고 비어 있지 않은 파일(`-s`)인지 모두 확인하도록 Compose entrypoint 보강 |

## 변경 파일

| 경로 | 내용 |
| --- | --- |
| `docker-compose.yml` | YOLO 모델 경로가 일반 파일인지 추가 검사 |
| `.env.example` | same-origin과 CORS JSON 배열의 용도 안내 |
| `README.md` | Cloudflare Tunnel, Nginx internal bind port, REST/WebSocket same-origin 실행 기준 안내 |
| `frontend/docs/plans/plan-22-local-docker-development-environment.md` | 후속 범위를 frontend·Docker/Nginx·root 실행 문서로 한정한 기록 |

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| Compose 병합 | 통과 | `docker compose --env-file .env.example -f docker-compose.yml -f docker-compose.dev.yml config --quiet` |
| CORS JSON 배열 파싱 | 통과 | backend `Settings`가 HTTPS origin JSON 배열을 `list[str]`로 해석 |
| frontend lint | 통과 | 오류 0건, 기존 `<img>` 최적화 warning 1건 유지 |
| `git diff --check` | 통과 | 공백 오류 없음 |

## 남은 확인 항목

1. Jenkins/VM에서 Cloudflare Tunnel 서비스 주소가 `http://127.0.0.1:8099`와 일치하는지 확인한다.
2. 외부 HTTPS 도메인에서 `/api/dashboard/summary` 요청이 같은 origin으로 전송되는지 브라우저 Network 탭에서 확인한다.
3. `wss://<domain>/ws/drains/status` 연결과 이벤트 수신을 확인한다.
4. 모델 경로에 디렉터리 또는 빈 파일을 지정했을 때 AI service가 즉시 실패하는지 확인한다.

## 주의 사항

- root `.env`의 모델 경로와 `NGINX_HTTP_PORT`는 Jenkins/VM 실행 환경값이므로 로컬 PC 기준으로 변경하지 않는다.
- same-origin 요청에는 CORS가 적용되지 않는다. `COMPOSE_CORS_ORIGINS`는 backend 직접 호출 origin만 제한적으로 관리한다.
