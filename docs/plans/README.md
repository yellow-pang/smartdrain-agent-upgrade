# Plans

앞으로 진행할 작업 계획 문서를 보관합니다.

권장 파일명:

```text
plan-XX-short-topic.md
```

계획 문서에는 작업 목적, 변경 범위, 영향받는 파일, 검증 방법, 남은 위험을 간단히 기록합니다.

## 주요 계획

- [SmartDrain GitHub Actions CI/CD 구현 계획](plan-04-github-actions-cicd.md): `dev → main` 검증, ARM 이미지 게시, 기존 Mac PostgreSQL을 유지하는 자동배포 계획. 공개 CI·이미지 게시와 Compose image 변수는 구현되었으며, 비공개 Mac 배포는 준비가 필요합니다.
- [공개 소스와 비공개 배포 이미지 운영](plan-06-private-image-deployment.md): 2026-10-04 조사한 비공개 전환 대안의 기록입니다. **검토 후 미채택** 상태이며, 공개 이미지 배포 유지와 [보안 기초 점검](../steps/step-06-public-image-security-review.md)으로 방향을 결정했습니다.
