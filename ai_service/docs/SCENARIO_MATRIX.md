# XGBoost scenario matrix

이 문서는 목업 데이터에 포함된 주요 경우의 수와 기대 해석을 정리한다.

| ID | 시나리오 | 핵심 패턴 | 기대 위험 | 기대 상태 코드 |
|---:|---|---|---|---|
| 1 | 정상 배수 | YOLO 낮음, 수위 안정, 유속 정상 | good | `NORMAL_DRAINAGE` |
| 2 | 상부만 막힘·배수 정상 | YOLO 높음, 수위 낮음, 유속 빠름 | caution | `SURFACE_OBSTRUCTION_LIKELY` |
| 3 | 건조 상태 상부 이물질 | YOLO 높음, 수위 낮음, 유속 낮음, 변화 없음 | caution | `DRY_SURFACE_OBSTRUCTION` |
| 4 | 상부·내부 복합 막힘 | YOLO 높음, 수위 상승, 유속 감소 | danger | `COMBINED_OBSTRUCTION` |
| 5 | 심각한 완전 막힘 | YOLO 매우 높음, 수위 매우 높음, 유속 거의 0 | danger | `SEVERE_OBSTRUCTION` |
| 6 | YOLO 정상이나 내부·하류 막힘 | YOLO 낮음, 수위 상승, 유속 감소 | danger | `INTERNAL_OR_DOWNSTREAM_OBSTRUCTION_SUSPECTED` |
| 7 | 과도한 유입 | YOLO 낮음, 수위 상승, 유속 빠름 | caution | `HYDRAULIC_OVERLOAD` |
| 8 | 과도한 유입 + 상부 막힘 | YOLO 높음, 수위 상승, 유속 빠름 | caution | `HIGH_INFLOW_WITH_SURFACE_OBSTRUCTION` |
| 9 | 용량 근접 안정 상태 | 높은 수위, 안정적 변화, 유속 빠름 | caution | `NEAR_CAPACITY_STABLE` |
| 10 | 위험 상태 회복 중 | 수위 하락, 유속 회복 | good | `RECOVERING` |
| 11 | 진행성 막힘 | YOLO 막힘 증가, 수위 상승, 유속 감소 | danger | `PROGRESSIVE_OBSTRUCTION` |
| 12 | 간헐적 막힘 | YOLO 이력 변동, 수위·유속 변동 | caution | `INTERMITTENT_OBSTRUCTION` |
| 13 | YOLO 오탐 의심 | YOLO 막힘 높지만 confidence 낮고 센서 정상 | unknown | `LOW_CONFIDENCE_VISION` |
| 14 | 수위 센서 순간 spike | 최신 수위만 비정상적으로 튐 | caution/degraded | `WATER_LEVEL_SPIKE` |
| 15 | 유속 센서 stuck | 유속 고정, 수위 변화 존재 | good/degraded | `FLOW_SENSOR_STUCK` |
| 16 | 센서 데이터 지연 | 최신 valid 센서가 오래됨 | unknown | `STALE_SENSOR_DATA` |
| 17 | 유효 센서 데이터 없음 | valid 센서 없음 | unknown | `NO_VALID_SENSOR_DATA` |
| 18 | YOLO 정상·센서 숨은 위험 | YOLO 낮음, 수위 높음, 유속 낮음 | danger | `SENSOR_DETECTED_HIDDEN_RISK` |

## 설계 의도

`risk_level`은 XGBoost 확률 모델의 위험 단계이고, `state_code`는 YOLO와 센서 조합을 해석한 상태 유형이다. 따라서 같은 `risk_level=caution`이라도 의미가 다르다.

예:

```text
SURFACE_OBSTRUCTION_LIKELY
= 상부에는 막힘 징후가 있지만 배수 기능은 유지되는 상태

HYDRAULIC_OVERLOAD
= 막힘보다는 유입량이 많아 배수 용량에 근접한 상태

FLOW_SENSOR_STUCK
= 위험 판단보다 센서 신뢰성 확인이 먼저 필요한 상태
```

이 구조는 백엔드·프론트엔드가 단순 위험 단계뿐 아니라 상황별 메시지를 구성할 수 있게 하기 위한 것이다.
