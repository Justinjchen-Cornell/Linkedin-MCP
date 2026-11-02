Set-Location $PSScriptRoot\..
uv sync
Start-Job { Start-Sleep -Seconds 2; Start-Process "http://127.0.0.1:8765" } | Out-Null
uv run uvicorn app.main:app --host 127.0.0.1 --port 8765
