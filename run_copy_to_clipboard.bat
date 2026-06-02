@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
)

".venv\Scripts\python.exe" -m pip install -e . >nul

set "OUTPUT_FILE=%TEMP%\aimstletter_digest.txt"
".venv\Scripts\aimstletter.exe" --dry-run > "%OUTPUT_FILE%"

type "%OUTPUT_FILE%" | clip

echo Digest copied to clipboard.
echo Paste it into Slack and send.
echo.
echo Opening the test Slack channel...
start "" "https://sk-ai-talent-lab.slack.com/archives/D09TPCPTDFT"
pause
