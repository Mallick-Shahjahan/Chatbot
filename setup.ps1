# setup.ps1 - automates venv and installs requirements (PowerShell)
$ErrorActionPreference = "Stop"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found on PATH. Please install Python 3.11+ and re-run."
    exit 1
}
python -m venv venv
.
env\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Write-Host "Setup complete. Run: streamlit run chatbot.py"