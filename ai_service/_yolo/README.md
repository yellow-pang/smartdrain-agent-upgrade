# Fake YOLO Stub

`ai_service/_yolo` is not a real YOLO implementation.

It provides a deterministic fake YOLO predictor so the backend-AI server connection flow can be tested before image processing, CCTV API integration, and real YOLO inference are available.

## Contract

The fake predictor returns:

- `obstruction_ratio`
- `confidence_score`
- `yolo_status`

Allowed `yolo_status` values:

- `good`
- `dirty`
- `blocked`
- `unknown`

## Mock Data

The current MVP mock drain IDs are `1`, `2`, `3`, and `4`.

The values are copied from the first four samples in `yolo_results_json.json` and then fixed in code. The predictor does not read that external JSON file at runtime.

| drain_id | obstruction_ratio | confidence_score | yolo_status |
| -------: | ----------------: | ---------------: | ----------- |
| 1        | 0.0227            | 0.676            | good        |
| 2        | 0.057             | 0.9404           | good        |
| 3        | 0.002             | 0.9371           | good        |
| 4        | 0.061             | 0.8504           | good        |

Unknown drain IDs return:

{
    "obstruction_ratio": 0.0,
    "confidence_score": 0.0,
    "yolo_status": "unknown",
}

## Future Replacement

When real YOLO is ready, replace `FakeYoloPredictor` while preserving the output contract used by the analysis orchestration layer.

