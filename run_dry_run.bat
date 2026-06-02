@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
)

".venv\Scripts\python.exe" -m pip install -e . >nul

set "AZURE_OPENAI_ENDPOINT=https://skcc-atl-master-openai-01.openai.azure.com/"
set "AZURE_OPENAI_DEPLOYMENT=gpt-5-mini"
set "DIGEST_CHANNEL_LABEL=AI마스터"

if "%AZURE_OPENAI_API_KEY%"=="" (
  echo AZURE_OPENAI_API_KEY environment variable is not set.
  echo Set it once with:
  echo   setx AZURE_OPENAI_API_KEY "YOUR_KEY"
  echo.
  echo Running dry-run without AI rewrite.
)

".venv\Scripts\aimstletter.exe" --dry-run
pause
