# Starts the local Markdown converter and opens it in the browser.
# Requires uv (https://docs.astral.sh/uv/). uv creates/updates .venv from uv.lock on first run.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
Start-Process "http://127.0.0.1:5000"
uv run app.py
