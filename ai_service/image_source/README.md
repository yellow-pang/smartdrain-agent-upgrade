# Image Source

`ai_service/image_source` resolves the image that YOLO should analyze.

The backend does not need to send `image_path`. The AI service receives `drain_id`, resolves an image source internally, and passes the resulting local image path to `ai_service/yolo`.

## Current Local Mock Flow

Real CCTV/storage integration is not connected yet. For now, `mock_provider.py` maps five drain IDs to mock source metadata. The backend integration normally sends the database integer ID, but direct AI calls may also pass `DR-001` style drain codes.

```text
drain_id: 1..5
equivalent codes: DR-001..DR-005
```

Each mock entry has:

- `source_url`: future CCTV/storage URL placeholder
- `local_path`: local image path read by YOLO during the mock phase

Example:

```python
{
    "source_url": "mock://storage/drain-1-latest.jpg",
    "local_path": "mock_data/ai_image_samples/drain_1.jpg",
}
```

`source_url` is intentionally kept even though it is not fetched yet. When CCTV/storage is ready, this value will become a real external URL or storage key.

`local_path` is what `ai_service/yolo/analyzer.py` currently receives. Mock image files live outside `ai_service` so the service directory stays focused on runtime code.

Default mock image directory:

```text
mock_data/ai_image_samples
```

Override it with:

```text
IMAGE_SOURCE_BASE_DIR=mock_data/ai_image_samples
```

Relative paths are resolved from the repository root.

## Required Local Sample Files

Real YOLO smoke tests need image files at the mock `local_path` locations.

Required file names:

```text
mock_data/ai_image_samples/drain_1.jpg
mock_data/ai_image_samples/drain_2.jpg
mock_data/ai_image_samples/drain_3.jpg
mock_data/ai_image_samples/drain_4.jpg
mock_data/ai_image_samples/drain_5.jpg
```

`drain_5.jpg` is intentionally absent in the current mock data. It represents an image acquisition failure case for CCTV/storage integration testing.

Check local file availability:

```powershell
python -m ai_service.scripts.check_samples
```

`check_samples` treats the missing `drain_5.jpg` as expected and fails only when other required sample images are missing.

## Later Real GET Flow

When external image retrieval is connected, keep `analysis` and `yolo` stable and replace the provider implementation:

```text
analysis.service
→ image_source.service.resolve_image_source_by_drain_id(drain_id)
→ cctv_provider or storage_provider
→ ai_service/http HTTP client performs GET
→ image bytes saved to local temp path
→ YOLO receives local_path
```

Low-level HTTP request mechanics should live in `ai_service/http`; drain-specific image resolution should stay in `ai_service/image_source`.

## Error Policy

If a `drain_id` has no configured mock source, `ValueError` is raised.

Current policy:

- Treat this as an unregistered drain ID or CCTV/storage image source configuration problem.
- Do not change the YOLO/XGBoost callback payload shape.
- HTTP request handling checks source availability before accepting the job and maps request-time failures to `400 Bad Request`.
- If a background task still fails later, it logs the failure and does not send callbacks for the failed job.

Future improvement:

- Return `422` instead of `400` if the backend contract later wants to distinguish invalid payload shape from missing CCTV/storage source.
- Or introduce an explicit backend-facing failure callback if the backend contract adds one later.
