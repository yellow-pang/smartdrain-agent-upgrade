# Step 00. Docs Structure Reorganization

## 변경 목적

루트 `docs/` 아래에 과거 MVP 산출물과 앞으로 작성할 개인 고도화 작업 이력이 섞이지 않도록 문서를 목적별로 재배치했다.

## 변경 내용

| 구분 | 변경 |
| --- | --- |
| MVP 산출물 | `docs/legacy-mvp/`로 이동 |
| MVP 이미지 | `docs/legacy-mvp/image/`로 이동 |
| 현재 참조 문서 | `docs/reference/`로 이동 |
| 검증·운영 문서 | `docs/verification/`로 이동 |
| 신규 작업 이력 | `docs/plans/`, `docs/steps/`, `docs/pr/` 생성 |
| 인덱스 | `docs/README.md` 추가 |

## 세부 이동 기준

- `docs/legacy-mvp/`: `01_프로젝트정의서.md`부터 `10_역할분담_일정_발표목차.md`
- `docs/reference/`: `11_API명세서.md`, `13_백엔드_AI_서버_비동기_분석_API_정리.md`, `15_AI_모델_아티팩트_관리_명세.md`
- `docs/verification/`: `12_프론트엔드_백엔드_API연동_테스트_문서.md`, `14_구현현황_및_검증결과.md`, `16_테스트_전략_및_E2E_검증.md`, `17_배포_운영_런북.md`

## 링크 정리

- root `README.md`의 주요 문서 링크를 새 경로 기준으로 갱신했다.
- `frontend/README.md`의 구현 현황과 테스트 전략 링크를 `docs/verification/` 기준으로 갱신했다.
- 기존 frontend 작업 문서에서 참조하던 루트 docs 경로를 `legacy-mvp`, `reference`, `verification` 기준으로 갱신했다.
- 이동 중 잘못 바뀐 `frontend/docs/images` 경로는 실제 위치 기준으로 복구했다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| Markdown 상대 링크 검사 | 통과, 누락 링크 없음 |
| 예전 루트 docs 번호 경로 검색 | 통과, 충돌 참조 없음 |
| Compose 설정 검사 | 통과 |

검증 명령:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
```

## 후속 작업

- 앞으로 새 작업 계획은 `docs/plans/`에 작성한다.
- 작업 완료 기록은 `docs/steps/`에 작성한다.
- PR 설명이나 리뷰용 요약은 `docs/pr/`에 작성한다.
