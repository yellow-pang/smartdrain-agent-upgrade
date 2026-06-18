# Temporary YOLO PoC area

이 폴더는 기존 PoC에서 가져온 `best.pt`를 임시 입력 생산자로 사용하기 위한 영역입니다. YOLO 모델 자체는 다른 팀원 담당이며 현재 XGBoost 개발 범위가 아닙니다.

## 모델 정보

기존 PoC 분석 기준으로 현재 모델은 이미지 전체를 다음 클래스 중 하나로 분류하는 Ultralytics classification 모델입니다.

```text
dry_blocked
dry_normal
rain_blocked
rain_normal
```

`adapter.py`는 blocked 계열 클래스 확률을 합산하여 `obstruction_ratio`로 변환합니다. XGBoost는 이 코드나 모델 파일을 직접 호출하지 않고 JSONL 또는 향후 DB에 저장된 표준 결과만 읽습니다.

## 선택 실행

```bash
python -m pip install -r requirements/yolo-poc.txt
python yolo/cli.py --image path/to/image.jpg --drain-id 101
```

기본 출력 위치:

```text
mock_data/fixtures/yolo_result_data.jsonl
```

새 YOLO로 교체할 때는 새 모델의 출력값을 같은 데이터 계약으로 변환하는 어댑터를 YOLO 담당 영역에서 제공해야 합니다.
