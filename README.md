# SmartDrain

## Docker 실행

운영 방식의 단일 진입점 구성은 Nginx만 PC의 80 포트를 사용합니다. 브라우저에서는 `http://localhost`로 접속하고, backend·AI·PostgreSQL 포트는 외부에 열지 않습니다.

```powershell
docker compose up --build -d
docker compose ps
```

`migrate` 서비스는 DB migration을 한 번 실행하고 종료합니다. 정상 기동 후 개발용 목 데이터가 필요할 때만 아래 명령을 실행합니다.

```powershell
docker compose --profile seed run --rm seed
```

개발 모드에서는 운영 기본 설정 위에 Hot Reload와 개발용 Swagger를 추가합니다. 접속 주소는 `http://localhost:8080`입니다.

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

개발 환경에서만 FastAPI 문서는 `http://localhost:8080/docs`로 확인할 수 있습니다. 운영 Compose에서는 Nginx가 `/docs`, `/openapi.json`, `/redoc` 요청을 차단합니다.

종료와 로그 확인 명령은 다음과 같습니다.

```powershell
docker compose down
docker compose logs -f nginx backend ai-service
```

`docker compose down -v`는 PostgreSQL volume까지 삭제하므로, 데이터를 초기화할 때만 사용합니다.

## 환경변수와 배포 설정 분리

환경변수는 실행 주체별로 분리한다. 실제 `.env` 파일은 Git과 Docker build context에 포함되지 않는다.

| 파일 | 책임 | 사용하는 환경 |
| --- | --- | --- |
| `/.env` | Compose project/port/DB 연결 문자열 등 배포 입력값 | Docker Compose, Jenkins 개발 VM |
| `/backend/.env` | Docker 없이 FastAPI를 로컬 실행할 때의 backend 설정 | backend 로컬 개발 |
| `/ai_service/.env` | Docker 없이 AI 서비스를 로컬 실행할 때의 callback 설정 | AI 로컬 개발 |
| `/frontend/.env.local` | Next.js 로컬 실행용 공개 API URL·Kakao JavaScript 키 | frontend 로컬 개발 |

각 서비스의 예시 파일을 복사해 사용한다.

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item ai_service\.env.example ai_service\.env
Copy-Item frontend\.env.example frontend\.env.local
```

운영 비밀값(데이터베이스 비밀번호, 배포 접근 키)은 `.env` 파일이나 GitHub 저장소에 저장하지 않는다. AWS에서는 Secrets Manager 또는 ECS task definition의 secret 참조를 사용하고, GitHub Actions에서는 Secrets에 저장해 배포 단계에서만 주입한다.

Vercel에는 frontend에서 실제 사용하는 공개 변수만 등록한다.

- `NEXT_PUBLIC_API_BASE_URL`: API가 별도 도메인이라면 해당 HTTPS URL, Nginx와 같은 origin이면 `/api`
- `NEXT_PUBLIC_KAKAO_MAP_APP_KEY`: 브라우저에서 사용하는 JavaScript 키이며, Kakao Developers의 허용 도메인도 Vercel 도메인으로 추가

`NEXT_PUBLIC_*` 값은 브라우저 번들에 포함되므로 비밀번호·AWS 키·DB URL 같은 비밀값을 넣으면 안 된다.
