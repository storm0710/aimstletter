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

if "%SLACK_WEBHOOK_URL%"=="" (
  echo SLACK_WEBHOOK_URL environment variable is required for actual Slack posting.
  echo Set it once with:
  echo   setx SLACK_WEBHOOK_URL "https://hooks.slack.com/services/..."
  pause
  exit /b 2
)

if "%AZURE_OPENAI_API_KEY%"=="" (
  echo AZURE_OPENAI_API_KEY environment variable is not set.
  echo The digest will use the rule-based summary instead of AI rewrite.
)

".venv\Scripts\aimstletter.exe"
pause
