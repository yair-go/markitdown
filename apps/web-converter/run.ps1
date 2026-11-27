# Starts the local Markdown converter and opens it in the browser.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    .\.venv\Scripts\python -m pip install -e "..\..\packages\markitdown[all]" flask
}
Start-Process "http://127.0.0.1:5000"
.\.venv\Scripts\python app.py
