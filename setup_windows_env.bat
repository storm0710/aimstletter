@echo off
setlocal

echo This stores settings in your Windows user environment.
echo For the file-based setup, use setup_windows_secrets.bat instead.
echo.

setx AZURE_OPENAI_ENDPOINT "https://skcc-atl-master-openai-01.openai.azure.com/"
setx AZURE_OPENAI_DEPLOYMENT "gpt-5-mini"
setx DIGEST_CHANNEL_LABEL "AI마스터"

set /p AZURE_KEY=Paste Azure OpenAI API key: 
if not "%AZURE_KEY%"=="" (
  setx AZURE_OPENAI_API_KEY "%AZURE_KEY%"
)

echo.
set /p SLACK_URL=Paste Slack webhook URL, or press Enter to skip: 
if not "%SLACK_URL%"=="" (
  setx SLACK_WEBHOOK_URL "%SLACK_URL%"
)

echo.
echo Done. Reopen your terminal, then run:
echo   run_dry_run.bat
echo or:
echo   run_post_to_slack.bat
pause
