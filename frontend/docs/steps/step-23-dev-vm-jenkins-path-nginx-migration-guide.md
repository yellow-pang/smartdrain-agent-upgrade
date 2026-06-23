# 23 개발 VM Jenkins 경로·Nginx 전환 실행 가이드

## 1. 목적과 적용 범위

이 문서는 실제 개발 VM에 접속 가능한 담당자가 MobaXterm SSH 터미널에서 실행하는 전환 절차다. 현재 Windows 작업 환경에서는 VM Docker 상태를 확인하거나 컨테이너를 중지하지 않는다.

이번 전환은 다음을 함께 처리한다.

- Jenkins bootstrap clone, 실제 Jenkins workspace, YOLO 모델 경로를 `/home/yp/apps/...` 기준으로 통일한다.
- Jenkins container와 VM host에서 workspace 절대 경로를 같게 해 Docker socket의 상대 bind mount 오류를 없앤다.
- Nginx가 workspace의 `nginx/default.conf`를 read-only로 mount하는지 Pipeline에서 검증한다.
- 기존 `smartdrain-dev` 컨테이너와 확인된 SmartDrain 고아 경로를 안전하게 정리한다.

Nginx 라우팅 설정, 데이터베이스 volume, Jenkins home volume, YOLO 모델 파일은 삭제 대상이 아니다.

## 2. 전환 후 기준 경로

| 구분 | VM 경로 |
| --- | --- |
| Jenkins bootstrap clone | `/home/yp/apps/opt/smartdrain` |
| Jenkins 실제 checkout·배포 workspace | `/home/yp/apps/apps/smart-drain` |
| YOLO 모델 | `/home/yp/apps/opt/smartdrain-data/models/best.pt` |
| Jenkins container 내부 workspace | `/home/yp/apps/apps/smart-drain` |
| Nginx 설정 source | `/home/yp/apps/apps/smart-drain/nginx/default.conf` |
| Nginx 설정 target | `/etc/nginx/conf.d/default.conf` (read-only) |

## 3. 사전 주의 사항

- 아래 명령은 **SmartDrain 개발 VM**에서만 실행한다.
- `docker compose down -v`, `docker volume prune`, `docker system prune --volumes`는 실행하지 않는다. PostgreSQL 데이터와 Jenkins 설정이 사라질 수 있다.
- `docker system prune -a`도 다른 프로젝트 image를 지울 수 있다. 디스크가 꼭 필요하고 다른 프로젝트에 영향이 없음을 확인한 경우에만 별도 판단으로 실행한다.
- `/apps`, `/deploy`는 다른 서비스가 쓸 수 있다. 목록·소유자·Docker mount 확인 전에는 삭제하지 않는다.
- Jenkins Job의 SCM Branch Specifier는 `*/dev`, Pipeline script path는 `Jenkinsfile`, Secret File credential ID는 `smartdrain-dev-env-file`이어야 한다.

## 4. 1단계: 현재 Docker·디스크 상태 기록

MobaXterm에서 VM에 접속한 뒤, 먼저 현재 상태를 보존한다. 이 출력은 정리 대상 판단과 장애 복구에 사용한다.

```bash
docker ps -a
docker system df -v
docker ps -a --filter 'label=com.docker.compose.project=smartdrain-dev'
docker volume ls
```

SmartDrain 컨테이너와 mount를 확인한다. 아래 출력에서 `/deploy` 또는 `/apps`가 mount source로 사용 중인지 확인한다.

```bash
for container in $(docker ps -aq --filter 'label=com.docker.compose.project=smartdrain-dev'); do
  docker inspect --format '{{.Name}} {{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}' "$container"
done
```

위 `docker ps -aq --filter` 결과가 비어 있으면 현재 SmartDrain Compose project가 실행 중이지 않은 상태다. 이 경우 다음 단계의 `down`은 생략할 수 있다.

## 5. 2단계: 기존 SmartDrain 실행 중지

현재 SmartDrain 개발 Compose project만 중지·제거한다. `-v`를 붙이지 않는다.

```bash
cd /home/yp/apps/opt/smartdrain
docker compose -p smartdrain-dev down --remove-orphans
docker compose -p smartdrain-dev ps
```

이 명령은 `smartdrain-dev`의 컨테이너와 네트워크만 제거한다. named volume의 PostgreSQL 데이터와 Jenkins home volume은 유지한다. 다른 Compose project 또는 이름이 다른 컨테이너가 남아 있으면 앞 단계에서 기록한 목록을 보고 별도로 판단한다.

이미지 용량을 조금 줄이려면, 먼저 dangling image만 제거할 수 있다.

```bash
docker image prune -f
docker builder prune -f
docker system df
```

AI image까지 포함한 모든 미사용 image 정리는 다른 프로젝트의 재빌드 시간을 늘릴 수 있으므로, 팀에서 VM 전체 정리를 합의한 경우에만 실행한다.

```bash
# 다른 프로젝트에서 사용하지 않는 image임을 확인한 경우에만 실행
docker image prune -a
```

## 6. 3단계: 고아 경로 확인 및 안전한 정리

먼저 경로가 존재하는지와 내용을 확인한다. 출력에 SmartDrain 외 파일이 있거나 소유자가 불명확하면 여기서 중단하고 경로를 삭제하지 않는다.

```bash
sudo ls -ld /apps /deploy 2>/dev/null || true
sudo find /apps /deploy -maxdepth 3 -printf '%M %u:%g %p\n' 2>/dev/null || true
docker ps -a --format '{{.ID}} {{.Names}}' | while read -r id name; do
  docker inspect --format "$name {{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}" "$id"
done
```

`/apps` 또는 `/deploy`가 SmartDrain이 잘못 만든 빈 경로 또는 Nginx 설정 고아본만 포함하고, 어느 컨테이너도 mount하지 않는 것이 확인된 경우에만 담당자가 대화형 삭제를 진행한다.

```bash
# 내용을 한 번 더 보여 주고 y/n을 묻는다. 확인되지 않은 경로에는 실행하지 않는다.
sudo rm -ri /apps
sudo rm -ri /deploy
```

삭제 후에는 존재 여부를 다시 확인한다.

```bash
sudo ls -ld /apps /deploy 2>/dev/null || true
```

## 7. 4단계: 새 경로 준비과 모델 확인

```bash
mkdir -p /home/yp/apps/opt
mkdir -p /home/yp/apps/apps/smart-drain
mkdir -p /home/yp/apps/opt/smartdrain-data/models

test -d /home/yp/apps/opt/smartdrain
test -d /home/yp/apps/apps/smart-drain
test -s /home/yp/apps/opt/smartdrain-data/models/best.pt
```

bootstrap clone이 아직 없으면 `dev` branch를 clone한다. 이미 clone이 있으면 해당 branch와 최신 상태를 먼저 확인한다.

```bash
git clone -b dev https://github.com/<owner>/<repository>.git /home/yp/apps/opt/smartdrain
# 이미 clone이 있는 경우
git -C /home/yp/apps/opt/smartdrain status --short --branch
git -C /home/yp/apps/opt/smartdrain pull --ff-only origin dev
```

위 두 명령은 동시에 실행하지 않는다. clone 디렉터리가 이미 있으면 `git clone`은 건너뛴다.

Jenkins Secret File `smartdrain-dev-env-file`에는 아래 값이 있어야 한다. `.env` 전체나 DB 비밀번호를 Jenkins console에 출력하지 않는다.

```dotenv
COMPOSE_PROJECT_NAME=smartdrain-dev
SMARTDRAIN_YOLO_MODEL_PATH=/home/yp/apps/opt/smartdrain-data/models/best.pt
```

## 8. 5단계: Jenkins 컨테이너 재생성

새 `jenkins/docker-compose.jenkins.yml`의 동일 절대 경로 mount를 반영하려면 Jenkins container를 재생성해야 한다. `down -v`는 사용하지 않는다.

```bash
cd /home/yp/apps/opt/smartdrain/jenkins
docker compose -f docker-compose.jenkins.yml up -d --build --force-recreate
docker compose -f docker-compose.jenkins.yml ps
docker inspect smartdrain-jenkins --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} {{end}}'
```

마지막 명령의 출력에는 아래 mount가 있어야 한다.

```text
/home/yp/apps/apps/smart-drain -> /home/yp/apps/apps/smart-drain
```

`smartdrain-jenkins-home` named volume은 유지되므로 기존 Job·Credential·plugin 설정이 남아 있다. Jenkins UI는 `http://<VM-IP>:8082`에서 확인한다.

## 9. 6단계: Jenkins Job 실행과 Nginx 검증

Jenkins UI에서 SmartDrain Job을 열어 설정을 확인한다.

1. Definition: `Pipeline script from SCM`
2. Script Path: `Jenkinsfile`
3. Branch Specifier: `*/dev`
4. Secret File credential ID: `smartdrain-dev-env-file`

`Build Now`를 실행한다. Console log에서 다음 단계가 모두 통과해야 한다.

```text
Checkout pipeline scripts
Prepare environment
Preflight
Validate
Deploy
Smoke test
```

이번 변경으로 Preflight는 workspace의 `nginx/default.conf` 존재를 확인한다. Validate는 Compose가 아래 source·target·read-only mount를 구성하는지 확인한다.

```text
/home/yp/apps/apps/smart-drain/nginx/default.conf
→ /etc/nginx/conf.d/default.conf
→ read-only
```

Deploy 단계는 Docker daemon이 실제 Nginx container에 연결한 mount가 위 source인지 다시 검사한다. Smoke test는 Jenkins container의 loopback 포트가 아니라 Nginx container 내부에서 `/`와 `/api/dashboard/summary`를 호출하므로, VM host port와 Jenkins container network가 분리된 환경에서도 동작한다.

## 10. 7단계: 배포 후 확인

Jenkins build가 성공한 뒤 VM에서 확인한다.

```bash
cd /home/yp/apps/apps/smart-drain
docker compose -p smartdrain-dev ps
nginx_id=$(docker compose -p smartdrain-dev ps -q nginx)
docker inspect --format '{{range .Mounts}}{{if eq .Destination "/etc/nginx/conf.d/default.conf"}}{{.Source}} -> {{.Destination}} rw={{.RW}}{{end}}{{end}}' "$nginx_id"
```

기대 출력은 다음과 같다.

```text
/home/yp/apps/apps/smart-drain/nginx/default.conf -> /etc/nginx/conf.d/default.conf rw=false
```

마지막으로 실제 VM 공개 포트와 Nginx 응답을 수동 확인한다. 포트 값은 Secret File의 `NGINX_HTTP_PORT`를 사용한다.

```bash
curl --fail --silent --show-error http://127.0.0.1:<NGINX_HTTP_PORT>/
curl --fail --silent --show-error http://127.0.0.1:<NGINX_HTTP_PORT>/api/dashboard/summary
```

새 배포 뒤 root `/apps` 또는 `/deploy`가 다시 생기지 않아야 한다.

```bash
sudo ls -ld /apps /deploy 2>/dev/null || true
```

## 11. 실패 시 복구·점검 순서

| 증상 | 우선 확인 |
| --- | --- |
| Jenkins가 workspace에 checkout하지 못함 | `/home/yp/apps/apps/smart-drain`의 소유권·상위 `/home/yp` execute 권한, Jenkins container mount 출력 |
| Validate의 Nginx source 검사 실패 | `nginx/default.conf`가 checkout 되었는지, `pwd`와 `DEPLOY_DIR`가 `/home/yp/apps/apps/smart-drain`인지 |
| YOLO 모델 검사 실패 | Secret File의 절대 경로, `best.pt` 존재·읽기 권한 |
| Nginx mount 검사 실패 | `docker inspect` 결과의 source path, Jenkins container의 동일 경로 mount, root `/deploy` 재생성 여부 |
| Smoke test 실패 | `docker compose -p smartdrain-dev logs --tail=100 nginx backend ai-service`, Nginx·backend health 상태 |
| 디스크 부족 | `docker system df -v`로 대상 확인 후 dangling image/cache부터 정리. 데이터 volume과 Jenkins home은 유지 |

실패한 경우 `docker compose -p smartdrain-dev logs --tail=100 nginx backend ai-service` 결과와 Jenkins Console log의 실패 stage를 함께 남긴다. `down -v`나 광범위한 prune으로 원인을 지우지 않는다.

## 12. 저장소 변경 검증 결과

| 검증 | 결과 |
| --- | --- |
| Jenkins workspace path | Jenkinsfile과 Jenkins Compose mount를 `/home/yp/apps/apps/smart-drain`으로 통일 |
| Nginx preflight | workspace `nginx/default.conf` 존재 확인 추가 |
| Nginx validate/deploy | Compose 설정과 실제 Docker mount source·read-only 확인 추가 |
| Smoke test | Jenkins container loopback 대신 Nginx container 내부 요청으로 변경 |
| 실제 VM 실행 | 미실행 — VM 접근 가능한 담당자가 본 문서 순서로 진행 |
