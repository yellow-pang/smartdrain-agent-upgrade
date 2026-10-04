# PR 01. Realtime Dashboard Manual Auto Mode

## PR 제목

feat: 실시간 대시보드 수동/자동 모드 병행 지원

## 변경 목적

실시간 대시보드에서 기존 수동 분석 흐름을 유지하면서, 실행 중 자동 시뮬레이터를 시작/중지할 수 있는 기반을 추가한다.

## 주요 변경

| 영역 | 내용 |
| --- | --- |
| Backend | realtime simulator start/stop/status API와 런타임 loop 추가 |
| Frontend | 대시보드 자동 모드 제어 UI, 상태 조회 query, API client 추가 |
| 문서 | 수동/자동 모드 사용법과 검증 기록 정리 |

## PR 02와의 관계

이 PR은 자동 모드를 켜고 끄는 제어 기반을 만드는 작업이다. 실제 시연에서 `양호`, `주의`, `위험`, `판단불가` 상태별 센서/이미지/분석 결과가 안정적으로 DB에 저장되는 흐름은 `PR 02. 상태별 시나리오 기반 실시간 시뮬레이터 보강`에서 완성한다.

따라서 PR 01은 PR 02와 함께 검토하는 것을 전제로 한다.

## 검증 결과

| 항목 | 결과 |
| --- | --- |
| Frontend lint | 통과. 기존 `<img>` 관련 경고 유지 |
| Frontend build | 통과 |
| Backend import/compile | 로컬 의존성 및 `__pycache__` 권한 문제로 제한 |

## 관련 문서

- `docs/plans/plan-01-realtime-dashboard-manual-auto-mode.md`
- `docs/steps/step-01-realtime-dashboard-manual-auto-mode.md`
- `docs/pr/pr-02-scenario-based-realtime-simulator.md`
