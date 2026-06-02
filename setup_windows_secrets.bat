@echo off
setlocal
cd /d "%~dp0"

echo This creates secrets.json in this folder.
echo The file is ignored by git and will not be committed.
echo.

set /p AZURE_KEY=Paste Azure OpenAI API key: 
set /p SLACK_URL=Paste Slack webhook URL, or press Enter to skip: 

> secrets.json echo {
>> secrets.json echo   "slack_webhook_url": "%SLACK_URL%",
>> secrets.json echo   "azure_openai_endpoint": "https://skcc-atl-master-openai-01.openai.azure.com/",
>> secrets.json echo   "azure_openai_api_key": "%AZURE_KEY%",
>> secrets.json echo   "azure_openai_deployment": "gpt-5-mini",
>> secrets.json echo   "digest_channel_label": "AI마스터"
>> secrets.json echo }

echo.
echo Created secrets.json.
echo Run run_dry_run.bat to preview or run_post_to_slack.bat to post.
pause
