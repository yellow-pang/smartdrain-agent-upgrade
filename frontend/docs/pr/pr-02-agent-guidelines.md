## PR 제목

[docs] # 프론트엔드 Codex 작업 규칙 및 컨벤션 문서 추가

## 작업 내용

- SmartDrain frontend 작업을 위한 Codex 전용 `AGENTS.md`를 추가했습니다.
    - `/frontend` 내부 작업에만 적용된다는 범위 규칙을 명시했습니다.
    - 사용자가 명시적으로 요청하지 않으면 `/frontend` 밖의 파일을 수정하지 않도록 했습니다.
    - 루트 `../docs/` 개발 문서는 프로젝트 방향성 확인용으로 읽을 수 있지만, 사용자 요청 없이는 수정하지 않도록 했습니다.
    - 작업 전 실제 파일 구조와 `package.json` scripts를 확인하도록 규칙을 추가했습니다.
    - 작은 작업, 중간 작업, 큰 작업을 구분하는 기준을 정리했습니다.
    - 중간 이상 작업은 plan 문서를 작성하거나 갱신하고, 큰 작업은 사용자 승인 후 진행하도록 했습니다.
    - 작업 후 변경 요약, 검증 결과, 남은 리스크, 한글 Conventional Commit 메시지를 제안하도록 했습니다.
- frontend 코드 컨벤션 문서 뼈대를 추가했습니다.
    - 경로: `docs/convention/code-convention.md`
    - 네이밍, 함수, 컴포넌트, TypeScript, Tailwind CSS, shadcn 스타일 UI primitive 사용 기준을 정리할 수 있는 섹션을 추가했습니다.
    - 팀 컨벤션 중 코드 작성에 직접 영향을 주는 내용을 반영했습니다.
        - ESLint 적용
        - Prettier 사용 전제
        - 세미콜론 사용
        - 싱글 쿼트 사용
        - 4칸 들여쓰기
    - mock data와 실제 API 데이터 구분 기준에 RESTful API와 API 응답 형식 참고 내용을 추가했습니다.
    - 상세 규칙은 사용자가 Notion 내용을 옮겨 보완할 수 있도록 TODO를 남겼습니다.
- frontend 문서화 컨벤션 문서 뼈대를 추가했습니다.
    - 경로: `docs/convention/documentation-convention.md`
    - plan, step, PR 문서 작성 기준을 정리했습니다.
    - PR 문서 작성 규칙에 팀 컨벤션의 PR 제목과 PR 내용 형식을 반영했습니다.
    - 변경 전/후 기록, 검증 결과 기록, 한글 문서 작성, 한글 Conventional Commit 메시지 작성 기준을 정리했습니다.

## 주요 변경 기준

### Codex 작업 범위

- `AGENTS.md`는 frontend 디렉터리에만 적용됩니다.
- Codex는 사용자 요청 없이 `/frontend` 밖의 파일을 수정하지 않습니다.
- 루트 개발 문서는 작업 방향성, 요구사항, 아키텍처 확인용으로만 읽습니다.

### 작업 규모 분류

- 작은 수정은 plan 문서 없이 진행할 수 있도록 했습니다.
- 중간 작업은 코드 수정 전 plan 문서를 작성하거나 갱신하도록 했습니다.
- 큰 작업은 반드시 사용자 승인 후 진행하도록 했습니다.

### 문서화 흐름

- 계획 문서: `docs/plans/plan-XX-작업명.md`
- 작업 완료 문서: `docs/steps/step-XX-작업명.md`
- PR 요약 문서: `docs/pr/pr-XX-작업명.md`

## 변경 파일 요약

- `frontend/AGENTS.md`: SmartDrain frontend Codex 작업 규칙 추가
- `frontend/docs/convention/code-convention.md`: frontend 코드 컨벤션 문서 추가
- `frontend/docs/convention/documentation-convention.md`: frontend 문서화 컨벤션 문서 추가

## 스크린샷 / 테스트 결과

- 이번 변경은 문서 추가 작업이므로 화면 스크린샷은 없습니다.
- 변경 파일 확인을 진행했습니다.
    - 확인 명령어: `git diff --name-status feature/frontend..HEAD`
    - 결과: 문서 파일 3개 추가 확인
        - `frontend/AGENTS.md`
        - `frontend/docs/convention/code-convention.md`
        - `frontend/docs/convention/documentation-convention.md`
- 커밋 차이 확인을 진행했습니다.
    - 확인 명령어: `git log --oneline feature/frontend..HEAD`
    - 결과: 문서 규칙 관련 커밋 2개 확인
- `pnpm lint`, `pnpm build`는 실행하지 않았습니다.
    - 사유: 코드 변경이 없는 문서 추가 작업입니다.
    - 참고: 이전 확인 시 현재 실행 환경에서 `pnpm` 명령을 찾지 못해 바로 실행할 수 없었습니다.

## 비고

- `code-convention.md`와 `documentation-convention.md`는 완성형 상세 문서가 아니라, 추후 Notion 내용을 옮겨 보완하기 위한 기준 문서입니다.
- 브랜치, 커밋, PR 규칙은 코드 컨벤션보다 협업/문서화 규칙에 가까우므로 `documentation-convention.md`와 `AGENTS.md` 중심으로 정리했습니다.
- 실제 `git commit`, `git push`, PR 생성은 사용자가 직접 진행합니다.
