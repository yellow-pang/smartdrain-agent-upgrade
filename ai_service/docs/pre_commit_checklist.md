# AI Service Pre-Commit Checklist

Use this checklist before committing the `ai_service` integration changes.

Do not commit from this checklist step unless explicitly requested.

## Contract Check

- [ ] Backend request body contains:
  - `request_id`
  - `drain_id`
  - `sensor_data`
- [ ] `request_id` is a non-empty string.
- [ ] `drain_id` is either an integer ID or a `DR-###` drain code.
- [ ] Backend request body does not use `image_path`.
- [ ] `sensor_data` contains:
  - `measured_at`
  - `water_level_cm`
  - `flow_velocity_mps`
  - `quality_status`
- [ ] `measured_at` is an ISO datetime string with both date and time.
- [ ] `water_level_cm` and `flow_velocity_mps` are finite numeric values.
- [ ] `quality_status` is currently `valid`.
- [ ] HTTP callback payload shape is unchanged:
  - YOLO callback: `request_id`, `job_id`, `yolo_result`
  - XGBoost callback: `request_id`, `job_id`, `xgboost_result`
- [ ] YOLO `unknown` result uses `obstruction_ratio=-1.0` and `confidence_score=-1.0`.
- [ ] YOLO non-`unknown` result numeric fields stay within `0.0` through `1.0`.

## Image Source Check

- [ ] `ai_service/image_source` resolves images by `drain_id`.
- [ ] Mock provider supports `drain_id` values `1` through `5`, including equivalent codes like `DR-001`.
- [ ] Unknown `drain_id` is treated as an unregistered drain or CCTV/storage image source configuration problem.
- [ ] Unknown `drain_id` is rejected before background callback processing.
- [ ] `source_url` remains a future CCTV/storage placeholder.
- [ ] `local_path` remains the current YOLO-readable local image path.

## Sample Image Check

Required local files for real YOLO smoke tests:

```text
mock_data/ai_image_samples/drain_1.jpg
mock_data/ai_image_samples/drain_2.jpg
mock_data/ai_image_samples/drain_3.jpg
mock_data/ai_image_samples/drain_4.jpg
mock_data/ai_image_samples/drain_5.jpg
```

- [ ] `drain_1.jpg` through `drain_4.jpg` are present if running real YOLO smoke.
- [ ] `drain_5.jpg` remains intentionally missing for the image acquisition failure case.
- [ ] Missing sample image files are acceptable when only checking code/docs.
- [ ] No real CCTV images are committed unless sanitized fixtures are explicitly approved.

## Model Path Check

- [ ] YOLO model path exists:

```text
ai_service/model/best.pt
```

- [ ] XGBoost model path exists:

```text
ai_service/model/sewer_xgboost_model.json
```

- [ ] Production YOLO code path:

```text
ai_service/yolo/analyzer.py
```

- [ ] Production XGBoost code path:

```text
ai_service/xgboost/model_predictor.py
```

## Environment Check

- [ ] Python 3.12 venv is active.
- [ ] Requirements are installed:

```powershell
python -m pip install -r .\ai_service\requirements.txt
```

- [ ] The current shell can import runtime dependencies if running real model smoke:
  - `fastapi`
  - `uvicorn`
  - `numpy`
  - `opencv-python`
  - `ultralytics`
  - `pandas`
  - `xgboost`
  - `pytest`

## Verification Commands

Syntax compile:

```powershell
python -m compileall ai_service
```

Unit tests:

```powershell
python -m pytest ai_service
```

Sample file check:

```powershell
python -m ai_service.scripts.check_samples
```

No-callback analysis smoke:

```powershell
python -m ai_service.scripts.smoke_analysis --drain-id 2
```

## Expected Command Outcomes

- `compileall` should pass.
- `pytest` should pass only after `pytest` and runtime dependencies are installed.
- `check_samples` returns `0` when `drain_1.jpg` through `drain_4.jpg` exist and only `drain_5.jpg` is missing as expected.
- `check_samples` returns non-zero if required sample images other than `drain_5.jpg` are missing.
- `smoke_analysis` returns:
  - `0` when local image exists and analysis completes
  - `1` when `drain_id` cannot resolve
  - `2` when local sample image is missing

## Commit Readiness

- [ ] No code outside `ai_service` was modified for this integration.
- [ ] No generated `__pycache__` files remain.
- [ ] No accidental real CCTV images are staged.
- [ ] The final diff is reviewed before committing.
