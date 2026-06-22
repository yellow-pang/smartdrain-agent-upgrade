# Sample CCTV Images

This directory is reserved for local mock CCTV images used by `ai_service/image_source`.

Do not commit real CCTV images unless the team explicitly decides to keep sanitized fixtures in the repository.

Place files with these exact names when running real YOLO smoke tests:

```text
drain_1.jpg
drain_2.jpg
drain_3.jpg
drain_4.jpg
drain_5.jpg
```

The mock provider maps `drain_id` values `1` through `5` to these local paths.

Examples:

```text
drain_id=1 -> ai_service/samples/drain_1.jpg
drain_id=2 -> ai_service/samples/drain_2.jpg
```

Check sample availability from the repository root:

```powershell
python -m ai_service.scripts.check_samples
```
