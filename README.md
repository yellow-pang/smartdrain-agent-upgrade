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
