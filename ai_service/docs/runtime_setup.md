# AI Service Runtime Setup

## Python Version

Use Python 3.12 for the AI service runtime.

The current project venv may be broken if it points to a removed Python install. Recreate it from the repository root.

## Recreate Venv

PowerShell:

```powershell
cd C:\dev_work\team_pro_01\smartdrain
deactivate
Remove-Item -Recurse -Force .\venv
py -3.12 -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\ai_service\requirements.txt
```

If Python 3.12 is not installed:

```powershell
winget install -e --id Python.Python.3.12
```

After installation, close and reopen PowerShell, then verify:

```powershell
py -3.12 --version
```

## Verify

Run syntax compilation:

```powershell
python -m compileall ai_service
```

Run tests:

```powershell
python -m pytest ai_service
```

## Run Server

```powershell
python -m uvicorn ai_service.http.app:app --host 0.0.0.0 --port 9000 --reload
```

## Request Smoke Test

The backend request sends `drain_id`, not `image_path`. The AI service resolves the mock image source internally through `ai_service/image_source`.

```json
{
  "request_id": "REQ_20260618_001",
  "drain_id": 2,
  "sensor_data": {
    "measured_at": "2026-06-18T08:36:13+09:00",
    "water_level_cm": 98.13,
    "flow_velocity_mps": 0.4512,
    "quality_status": "valid"
  }
}
```

Endpoint:

```text
POST http://localhost:9000/ai/analysis/run
```

Expected immediate response:

```json
{
  "accepted": true,
  "request_id": "REQ_20260618_001",
  "job_id": "AI_JOB_REQ_20260618_001",
  "status": "processing"
}
```

Callbacks are sent asynchronously to the backend configured by `BACKEND_BASE_URL`.

The current mock image source registry supports drain IDs `1` through `5`. Each entry contains a future `source_url` placeholder and a current `local_path` for YOLO.

## Local Model Smoke Test

Use this command when you want to check image source resolution and local model inference without sending backend callbacks:

```powershell
python -m ai_service.scripts.smoke_analysis --drain-id 2
```

Requirements:

- Python 3.12 venv is active.
- `python -m pip install -r .\ai_service\requirements.txt` has completed.
- The resolved `local_path` image file exists, for example `ai_service/samples/drain_2.jpg`.

If the image file does not exist, the script prints the resolved source and exits without running YOLO.

## Sample Image Check

The mock image source registry expects these files:

```text
ai_service/samples/drain_1.jpg
ai_service/samples/drain_2.jpg
ai_service/samples/drain_3.jpg
ai_service/samples/drain_4.jpg
ai_service/samples/drain_5.jpg
```

Check whether the files exist:

```powershell
python -m ai_service.scripts.check_samples
```

This command does not load YOLO and does not send backend callbacks. It only checks the local files referenced by `ai_service/image_source`.
