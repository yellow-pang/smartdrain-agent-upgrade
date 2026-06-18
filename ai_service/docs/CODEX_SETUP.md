# Codex setup

- 저장소 루트의 `AGENTS.md`는 전체 AI 서비스 경계를 설명한다.
- `xgboost/AGENTS.override.md`는 XGBoost 작업 규칙을 더 구체적으로 적용한다.
- `yolo/AGENTS.override.md`는 YOLO 영역을 기본 읽기 전용으로 제한한다.
- `.codex/config.toml`은 승인 요청과 workspace-write sandbox를 사용하는 보수적 프로젝트 설정이다.

Codex는 프로젝트를 신뢰한 경우에만 프로젝트 `.codex/config.toml`을 읽는다. 작업 시작 위치는 저장소 루트 또는 `xgboost/`를 권장한다.

검증 예시:

```bash
codex --ask-for-approval never "현재 활성화된 AGENTS 지침을 요약해줘"
codex --cd xgboost --ask-for-approval never "수정 가능한 범위를 알려줘"
```
