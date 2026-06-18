$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements\dev.txt
& .\.venv\Scripts\python.exe -m pip install -e .

Write-Host "Virtual environment created. Activate it with: .\.venv\Scripts\Activate.ps1"
Write-Host "Then run: python scripts\verify_setup.py"
