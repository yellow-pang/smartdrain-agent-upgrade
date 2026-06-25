# 로컬 목업 CCTV 이미지

이 폴더는 `ai_service/image_source`가 사용하는 로컬 목업 CCTV 이미지를 보관한다.

이미지 파일은 `ai_service/` 밖에 둔다. `ai_service/`는 런타임 코드, 모델 연동 코드, 문서 중심으로 유지하고 목업 데이터는 분리하기 위함이다.

## 현재 용도

현재 실제 CCTV API나 외부 이미지 저장소가 없으므로, AI 서버는 `drain_id`를 기준으로 이 폴더의 로컬 이미지를 찾는다.
또한 backend realtime simulator는 상태별 시연 이미지를 `scenarios/` 아래에서 찾는다.

기본 경로:

```text
mock_data/ai_image_samples
```

AI 서버에서는 아래 환경변수로 경로를 바꿀 수 있다.

```text
IMAGE_SOURCE_BASE_DIR=mock_data/ai_image_samples
```

## 파일 규칙

목업 provider는 `drain_id` 1부터 5까지를 지원한다.

```text
drain_1.jpg
drain_2.jpg
drain_3.jpg
drain_4.jpg
drain_5.jpg
```

현재 의도된 상태:

| drain_id | 파일 | 상태 |
| ---: | --- | --- |
| 1 | `drain_1.jpg` | 정상 분석 샘플 |
| 2 | `drain_2.jpg` | 정상 분석 샘플 |
| 3 | `drain_3.jpg` | 정상 분석 샘플 |
| 4 | `drain_4.jpg` | 정상 분석 샘플 |
| 5 | `drain_5.jpg` | 판단불가/저신뢰도 샘플 |

`drain_5.jpg`는 판단불가 또는 저신뢰도 상황을 확인하기 위한 케이스다.

## 상태별 시나리오 이미지

backend realtime simulator는 외부 AI Service 없이 시연용 센서/분석 결과를 DB에 직접 저장할 때 아래 경로의 이미지를 사용한다.

```text
mock_data/ai_image_samples/scenarios/good/
mock_data/ai_image_samples/scenarios/caution/
mock_data/ai_image_samples/scenarios/danger/
mock_data/ai_image_samples/scenarios/unknown/
```

상태 매핑:

| 폴더 | 화면 상태 | DB/API 값 |
| --- | --- | --- |
| `good` | 양호 | `good` |
| `caution` | 주의 | `caution` |
| `danger` | 위험 | `danger` |
| `unknown` | 판단불가 | `unknown` |

지원 확장자는 `.jpg`, `.jpeg`, `.png`, `.webp`다. 폴더가 비어 있으면 `image_url`은 비워 두고 센서/분석 결과만 저장한다.

## 점검 명령

저장소 루트에서 실행한다.

```powershell
python -m ai_service.scripts.check_samples
```

`check_samples`는 필수 샘플 이미지가 없으면 실패를 반환한다.

## 주의사항

- 실제 CCTV 이미지는 팀에서 명시적으로 결정하기 전까지 커밋하지 않는다.
- 운영용 외부 저장소가 확정되면 이 폴더 대신 `image_source` provider를 교체한다.
- YOLO 코드는 외부 URL을 직접 다루지 않고 최종 로컬 파일 경로만 받는다.
