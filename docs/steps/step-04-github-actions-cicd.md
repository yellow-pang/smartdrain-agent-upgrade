# SmartDrain GitHub Actions CI/CD 실행 기록

## 0. Source of Truth

- Plan: [plan-04-github-actions-cicd.md](../plans/plan-04-github-actions-cicd.md)
- 이전 실행 근거: [Mac 이전 기록](step-03-mac-mini-orbstack-migration-implementation-record.md)
- branch: `chore/github-actions-cicd`
- 구현 기준 HEAD: `d9854ac` — 계획 문서 커밋
- 마지막 갱신: 2026-09-27 21:20 KST
- 사용자 승인: 계획 문서 커밋 후 계획에 따른 구현 진행 요청.

## 1. Current State

- Phase 0 보존 자료·운영 경로 준비 완료 / Phase 1 로컬 구현·검증 완료.
- Gate 0: DB backup 복구, 모델 복사·읽기 검증 완료. 비공개 repo/runner/권한 설정은 미실행.
- Gate 1: 로컬 상당 검증 `PASSED`, **hosted CI는 미실행이므로 Gate 전체는 미통과**.
- Phase 2의 public release workflow 코드는 작성·정적 검증했으며 ARM build/publish 실행은 `NOT_STARTED`.
- Gate 2–5: 미통과. Mac receiver/runner는 아직 구현·등록하지 않았다.
- 운영 컨테이너·Cloudflare·운영 DB schema는 변경하지 않았다. 준비 파일과 복귀용 tag·backup만 추가했다.
- 현재 Git HEAD는 `d9854ac`. 원격 작업 branch에도 같은 계획 commit이 있음을 재개 시 확인했다. 구현 코드는 아직 미커밋이다.

## 2. Next Action

사용자 확인 후 검증된 구현 변경을 커밋·작업 branch에 push하고 dev 대상 PR의 hosted CI를 실행한다. 아직 main 병합·배포는 하지 않는다. 루트 AGENTS의 명시 요청 규칙에 따라 이 원격 실행 범위를 질문한 상태다.

## 3. Completed Tasks / 확인 근거

| 작업 | 결과 | 근거 |
| --- | --- | --- |
| 계획 커밋 | 완료 | `d9854ac`, 문서 두 파일만 커밋 |
| 운영 상태 조회 | 정상 | SmartDrain 5개 서비스 healthy, nginx loopback 8099 |
| DB 기준 확인 | 완료 | project `smartdrain-mac`, volume `smartdrain-mac_postgres_data`, revision `20260623_0003` |
| GitHub 현황 | 기존 계획과 동일 | repo 전용 runner/variables 없음. 조회 목록에 재사용 가능한 전용 운영 repo 없음 |
| AI dependency 기록 | 완료 | torch 2.14.0, ultralytics 8.4.156, opencv-python 5.0.0.93, xgboost 3.4.1, numpy 2.5.3, scikit-learn 1.9.1 |
| pnpm 기준 확인 | 완료 | 기존 성공 build history `17obkxptguopwzn70tucoexli`에서 12.5.1 확인, packageManager 고정 |
| Compose 입력 검증 | 완료 | local/dev/digest 설정, backend/migrate/seed 동일 image, volume·loopback·readonly mount 확인 |
| AI 경량 CI | 완료 | 새 Python 3.12.14 venv에 기존 명세의 4개 dependency만 설치, 전체 131 passed(기존 115+새 smoke 16) |
| 실제 AI smoke | 완료 | 기존 ARM image를 재build하지 않고 새 script만 readonly mount, network none, 승인 hash/분류 일치 |
| Frontend CI 상당 검증 | 완료 | Node22 임시 container, pnpm12.5.1 frozen install/lint/build 성공, Next 타입 검사 포함 |
| Backend CI 상당 검증 | 완료 | 새 venv와 tmpfs PG16, 실제 CI의 migration/head/빈 DB summary 검사 성공 |
| workflow 정적 검증 | 완료 | 두 YAML 파싱, shell 16개 `bash -n`, inline Python AST, 외부 action SHA 확인 |
| partial rerun 검증 | 완료 | 같은 run/SHA의 build attempts 1/2/1 허용, 다른 commit digest 거부 |
| 운영 root 준비 | 완료 | `/Users/tro/apps/smartdrain`에 기존 .env·모델 복사, 실제 값 출력 없음, 모델 hash 및 AI 사용자 읽기 통과 |
| 첫 전환 복귀 자료 | 완료 | 원래 Compose/nginx/image ID 보존, 이전 앱 image에 `smartdrain-cicd-previous-<service>:d9854ac` tag 추가. layer 복제 없음 |
| DB backup 복구 | 완료 | `backups/pre-cicd-d9854ac.dump`를 별도 임시 DB에 복구, revision `20260623_0003`, drain 5개 확인 |

## 4. Gate Results

Gate 0–5는 Current State를 따른다. Mac의 Linux/arm64 로컬 검증은 hosted Ubuntu 검증을 대신하지 않는다. 현재 image를 이용한 smoke가 새 GHCR image 추론 Gate를 대신하지도 않는다.

## 5. Actual Changes

| 파일 | 실제 변경 | 목적 |
| --- | --- | --- |
| `docker-compose.yml`, `.env.example` | image 선택 변수 3개 추가, 기존 build 유지 | 로컬 build와 GHCR digest 선택을 같은 Compose에서 지원 |
| `frontend/package.json` | pnpm12.5.1 고정 | 기존 성공 버전으로 CI/Docker 일치, lockfile 불변 |
| `ai_service/scripts/smoke_analysis.py` | reference CLI 모드 및 실패 종료 | 모델 hash·실추론·callback payload 판정, production 로직 불변 |
| `ai_service/analysis/tests/test_smoke_analysis.py` | 16개 reference 회귀 case | sentinel false success, artifact/ID/status/분류/입력/예외 검사 |
| `.github/workflows/ci.yml` | PR/reusable/manual CI | secret·모델 없는 hosted 검사와 안정된 CI gate |
| `.github/workflows/release.yml` | CI 후 ARM 게시·manifest·조건부 dispatch | bootstrap 기본 OFF, 동일 run 부분 재시도 지원 |
| README/검증 가이드/운영 런북/Plan | 실제 구현·활성화 대기 구분 | Jenkins 레거시와 진행 중 Actions 운영 혼동 방지 |

## 6. Commands Already Executed

- `git add` 지정 문서 두 파일 → `git commit`: 계획 문서 커밋 완료.
- `gh repo list`, SmartDrain runner/variable API: 읽기 전용 확인.
- `docker ps`, image 목록, DB mount/project inspect, AI package metadata, `alembic current`: 읽기 전용 확인.
- AI image build, 운영 migration/seed, E2E 데이터 생성, Cloudflare 변경: 실행하지 않음.
- Python3.12 임시 venv: `pip install -c ai_service/requirements.txt pytest fastapi python-dotenv python-multipart`, 전체 pytest 실행 완료. 다시 대형 test image를 만들 필요 없음.
- 기존 AI runtime image + 새 smoke script + best.pt readonly mount, `--network none`, `--verify-reference` 실행 완료. backend callback 없음.
- Node22 임시 container: pinned pnpm install/lint/build 실행 완료.
- 별도 `smartdrain-cicd-check` network, `smartdrain-cicd-db-check` tmpfs DB: CI migration 1회 및 backup restore 확인. 운영 migration 실행과 구분한다.
- 현재 운영 DB `pg_dump -Fc` → 보호된 로컬 backup, 임시 DB `pg_restore` 성공. backup을 자동 덮어쓰거나 삭제하지 않는다.
- 검증 종료 후 전용 임시 DB container와 network를 정리했다. 운영 PostgreSQL volume/image는 삭제하지 않았으며 SmartDrain 5개 서비스가 계속 healthy임을 확인했다.

### 승인된 reference

| 파일 | SHA256 |
| --- | --- |
| `best.pt` (52,067,329 bytes) | `d43cef94671907771f30b3316f2728e82af352db2cf4094644e92f6ffbaf16e2` |
| `drain_2.jpg` | `1a38ce043b8f1ec63e96d11d2837d30790a97b7d0378c6360fde2d1eb524a25a` |
| `sewer_xgboost_model.json` | `5fe6d594597156d233f71a2b9b13f76496acc30d2905846fc21d86cdcaf21385` |

기존 입력 기준 실제 결과: YOLO `good`(ratio 0.2216, confidence 0.9847), XGBoost `unknown/field_check`(score 0.8524). 부동소수점의 exact match를 gate로 사용하지 않는다.

## 7. Measurements

- OrbStack: aarch64, 10CPU, 할당 RAM 8,393,289,728 bytes.
- host 여유: `df -h` 기준 약 130GiB.
- 현재 image 표시: AI 10.5GB, backend 671MB, frontend 305MB. shared layer를 포함하므로 합산 고유 점유량이 아니다.
- Frontend 임시 검증 전체 88.57초(기반 image pull·install·lint/build 포함), pnpm install 출력 62.4초. 실제 hosted 시간은 미측정.
- Backend 격리 검증 전체 10.97초(dependency 설치·migration·API 포함). migration 단독 시간은 미측정.
- AI pytest 131개 실행 0.24초(venv/설치 제외).
- AI 실제 smoke 전체 8.51초(container 시작·model load·추론 포함). model load/추론 각각은 따로 측정하지 않음.
- DB backup 23,915 bytes. 임시 복구 성공, 복구 단독 시간 미측정.
- 새 ARM image build/push, cache 증가량, 운영 startup·배포 시간: 아직 측정하지 않음.

## 8. Decisions / Deviations / 문제 해결 기록

- 네트워크/Docker socket 조회가 기본 sandbox에서 차단되어 승인된 읽기 전용 escalation으로 확인했다. 앱 오류가 아니다.
- 계획의 운영 root `/Users/tro/apps/smartdrain`, 비공개 repo `yellow-pang/mac-mini-deploy`를 준비 기준으로 사용한다. 외부 리소스 생성 완료를 뜻하지 않는다.
- 운영 전환 전 준비와 독립적인 로컬 코드 작성은 병렬 진행한다. backup·hosted 검증 Gate를 통과하지 않은 상태에서 운영 적용은 하지 않는다.
- Compose 검사에서 `seed`가 활성 profile이 아니어서 `KeyError: seed`가 발생했다. 검사에만 `--profile seed`를 명시하고 재검증했다. seed 실행이나 운영 profile 변경은 하지 않았다.
- Backend 임시 검증 첫 시도는 Docker가 만든 workdir 소유권 때문에 코드 복사 단계에서 실패했다. 앱 사용자로 `/tmp` 아래 디렉터리를 만든 후 동일 CI 검증을 실행해 통과했다. 앱·DB 오류가 아니며 첫 시도에서는 migration도 시작하지 않았다.
- release artifact를 attempt 이름으로만 찾으면 실패 job 재시도 때 이전 성공 image를 잃는 문제를 review에서 발견했다. 동일 run/SHA의 artifact를 안정된 이름으로 재사용하고 `build_attempts`와 `manifest_attempt`를 기록하도록 보정했다. receiver도 이 계약을 따라야 한다.
- 원격 branch에서 계획 commit을 확인했으나 이번 구현에서는 아직 push/PR를 실행하지 않았다. 원격 CI 실행 범위를 사용자에게 확인했다.
- Frontend lint의 기존 `<img>` warning 1개와 기존 `pnpm.overrides` 무시 warning을 관찰했다. 기존 성공 pnpm 버전을 유지했으며 dependency/override 정책 변경은 이번 범위에 섞지 않았다.
- pytest의 cache plugin을 readonly 검증에서 끄면서 `cache_dir` warning 1개가 발생했다. 테스트는 모두 통과했으며 실제 CI는 cache plugin을 끄지 않는다.

## 9. Open Issues / Blockers

- hosted CI 실행을 위한 구현 commit/push/dev PR 범위 확인 대기.
- hosted ARM cold build의 14GB runner 적합성, GHCR 게시·pull 미검증.
- 비공개 receiver/권한/runner, 보호 규칙, 실제 release 환경값 등록 미실행.
- 기존 `pnpm.overrides` 설정이 pnpm12에서 무시된다. 잠금 파일로 이번 검증은 통과했으며 설정/의존성 변경 필요성은 별도 검토 대상이다.
- 최초 적용과 callback E2E, 공개/lifecycle 인수는 아직 완료되지 않았다.

## 10. Deferred Work

AI 이미지 최적화, runtime upgrade, 전체 dependency pinning, multi-arch, Jenkins 제거, 자동 rollback, 공용 cache GC, Cloudflare 변경은 이번 구현에 섞지 않는다.

## 11. Context Recovery

`AGENTS → Plan → 이 Steps → Git status/branch/HEAD → 실제 운영 상태`를 확인한다. 완료한 비싼 build/migration/seed/배포를 자동 반복하지 않는다. Phase/Gate 변경, 실패 원인 확정·해결, 비싼 검증 완료, 외부 설정 변경, 세션 종료 시 갱신한다.
