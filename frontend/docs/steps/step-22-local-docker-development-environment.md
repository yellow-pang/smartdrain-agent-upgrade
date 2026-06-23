# 22 로컬 Docker Compose 개발 환경 정비 결과

## 작업 결과

로컬 Docker Compose 개발 환경이 backend scheduler 설정을 root `.env`로부터 일관되게 전달하고, YOLO 모델이 없는 상태에서 AI service가 정상처럼 실행되지 않도록 정비했다.

```text
root .env
  ├─ COMPOSE_ANALYSIS_* → backend scheduler 설정
  └─ SMARTDRAIN_YOLO_MODEL_PATH → ai-service 모델 파일 검사

개발 Compose
  └─ mock_data/ai_image_samples → AI container (read-only)

Cloudflare Tunnel
  └─ Nginx → frontend, /api/*, /ws/* (same-origin)
```

## 변경 전과 변경 후

| 구분 | 변경 전 | 변경 후 |
| --- | --- | --- |
| scheduler 설정 | 활성화 여부와 AI timeout만 Compose에서 제어 | 활성화 여부, 실행 주기, 초기 대기, 센서 최대 경과 시간, job timeout을 모두 `COMPOSE_ANALYSIS_*`로 전달 |
| YOLO 모델 누락 | `best.pt` mount 또는 분석 시점에 실패 원인이 늦게 드러날 수 있음 | AI container entrypoint가 파일 없음·디렉터리·0바이트를 오류 로그로 알리고 종료 |
| mock 이미지 | 개발 root source mount에 간접적으로 포함 | AI service에 개발용 sample image 경로를 read-only로 명시 mount |
| 실행 안내 | 모델 파일·scheduler 변수의 개발 기준이 빠른 시작 문서에 없음 | root README에 모델 설정, 사전 확인, 실패 로그, scheduler 변수와 역할을 기록 |
| Tunnel CORS 판단 | 외부 HTTPS 도메인에서의 REST·WebSocket 주소가 문서에 분산됨 | Nginx same-origin 경로와 Cloudflare Tunnel의 내부 포트 역할을 root README에 명시 |

## 변경 파일

| 경로 | 내용 |
| --- | --- |
| `docker-compose.yml` | backend의 scheduler 환경변수 5개와 AI 모델 사전검사 entrypoint 추가; 모델이 일반 파일인지도 확인 |
| `docker-compose.dev.yml` | AI service의 mock image 폴더 read-only mount 추가 |
| `.env.example` | `COMPOSE_ANALYSIS_*` 예시, YOLO 모델 파일 경로, CORS JSON 배열 안내 추가 |
| `README.md` | 로컬 모델 준비·검사·실패 로그·scheduler·Cloudflare Tunnel same-origin 기준 안내 추가 |
| `frontend/docs/plans/plan-22-local-docker-development-environment.md` | 승인된 모델 누락 정책을 반영 |

## 검증 결과

| 검증 | 결과 | 비고 |
| --- | --- | --- |
| 로컬 `.env`의 YOLO 모델 파일 존재 여부 | 통과 | 파일 존재만 확인했으며 경로와 파일 내용은 출력하지 않았다. |
| `docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet` | 통과 | 개발 Compose 병합 문법과 새 entrypoint·환경변수 치환을 확인했다. |
| REST same-origin 경로 점검 | 통과 | API helper가 이미 `/api/*` 경로를 가지므로 Compose base URL의 빈 값에서 Nginx로 요청한다. |
| WebSocket same-origin 경로 점검 | 통과 | HTTPS 페이지에서는 현재 host의 `wss://…/ws/drains/status`를 생성하고, Nginx는 Upgrade 헤더를 전달한다. |
| CORS JSON 배열 파싱 | 통과 | backend `Settings`가 `COMPOSE_CORS_ORIGINS`에서 전달되는 HTTPS JSON 배열을 `list[str]`로 해석한다. |
| frontend lint | 통과 | 오류 0건. 기존 `<img>` 최적화 warning 1건은 유지된다. |
| `git diff --check` | 통과 | 공백 오류가 없다. |
| 개발 Compose `up --build -d` | 미완료 | 이미지 빌드·기동 명령이 실행 제한 시간(약 2분)을 초과했다. 이후 상태·로그 조회는 현재 실행 환경의 추가 권한 한도로 수행하지 못했다. |

## 남은 확인 항목

실행 가능한 Docker 환경에서 아래를 순서대로 확인한다.

1. `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`
2. `docker compose -f docker-compose.yml -f docker-compose.dev.yml ps`
3. `docker compose -f docker-compose.yml -f docker-compose.dev.yml logs --tail 80 backend ai-service frontend nginx migrate`
4. `http://localhost:8080/`, `http://localhost:8080/api/dashboard/summary`, `http://localhost:8080/docs`, `ws://localhost:8080/ws/drains/status` 확인
5. `COMPOSE_ANALYSIS_SCHEDULER_ENABLED=true`으로 재기동한 뒤 backend log에 scheduler 시작 로그가 남는지 확인
6. 별도 test 환경에서 빈 모델 파일을 지정해 AI service의 모델 누락 오류 로그와 종료를 확인
7. Cloudflare Tunnel 외부 HTTPS 도메인에서 `/api/dashboard/summary`와 `wss://<domain>/ws/drains/status` 연결을 확인

## 주의 사항

- `SMARTDRAIN_YOLO_MODEL_PATH`와 `NGINX_HTTP_PORT`는 실행 환경별 root `.env` 값이다. Jenkins/VM용 값을 로컬 PC 기준으로 바꾸지 않는다.
- `SMARTDRAIN_YOLO_MODEL_PATH`는 Docker가 접근 가능한 실제 일반 파일 경로여야 한다.
- 모델 없이 대시보드·DB만 확인하려면 `COMPOSE_AI_SERVER_ENABLED=false`를 사용한다. 이때 AI container는 모델 누락 오류를 남기고 종료하므로 scheduler를 켜지 않는다.
- `docker compose down -v`는 PostgreSQL volume을 삭제하므로 데이터 초기화가 필요할 때만 실행한다.
