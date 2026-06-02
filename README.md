# AIMST Letter

AI마스터 과정 슬랙 방에 매주 AI 동향과 논문을 공유하기 위한 자동 뉴스레터 봇입니다.

## What It Does

- AI 뉴스 RSS와 arXiv AI/LLM 논문 피드를 수집합니다.
- 최근 7일 자료 중 DBA, 네트워크, 서버, 운영 자동화 직군에 가까운 항목 5개와 기타 AI 동향 5개를 나눠 우선순위화합니다.
- Slack Block Kit 메시지로 한국어 digest를 만듭니다.
- `AZURE_OPENAI_API_KEY` 또는 `OPENAI_API_KEY`가 있으면 멘토 톤의 자연스러운 요약을 생성하고, 없으면 규칙 기반 요약으로 동작합니다.
- GitHub Actions로 매주 수요일 오전 9시 KST에 자동 실행할 수 있습니다.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

`secrets.json`에 `slack_webhook_url`을 넣으면 실제 슬랙 전송이 가능합니다. `--dry-run`은 슬랙에 보내지 않고 콘솔에만 출력합니다.

```powershell
Copy-Item secrets.example.json secrets.json
notepad secrets.json
```

`secrets.json`은 `.gitignore`에 들어 있어 커밋되지 않습니다.

```powershell
aimstletter --dry-run
```

실제 전송:

```powershell
aimstletter
```

Windows에서 바로 실행하려면 아래 배치 파일을 사용할 수 있습니다.

```powershell
setup_windows_secrets.bat
run_dry_run.bat
run_post_to_slack.bat
run_copy_to_clipboard.bat
```

Slack webhook, bot token, workflow webhook을 사용할 수 없는 조직에서는 `run_copy_to_clipboard.bat`를 임시 대안으로 사용할 수 있습니다. 이 파일은 digest를 생성한 뒤 클립보드에 복사하고 테스트 Slack 채널을 엽니다. 사용자는 Slack 입력창에 붙여넣고 보내기만 하면 됩니다.

## GitHub Actions Setup

Repository Settings에서 아래 secrets를 등록합니다.

- `SLACK_WEBHOOK_URL`: 슬랙 Incoming Webhook URL
- `AZURE_OPENAI_API_KEY`: 선택 사항

Repository Variables에는 필요하면 아래 값을 등록합니다.

- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT`: Azure OpenAI deployment name, 기본값 `gpt-5-mini`

## Slack Webhook 만들기

Slack 공식 문서 기준으로 Incoming Webhook은 특정 채널에 메시지를 보내는 고유 URL입니다.

1. [Slack API Apps](https://api.slack.com/apps)에 접속합니다.
2. `Create New App`을 누르고 `From scratch`를 선택합니다.
3. 앱 이름을 정하고, 테스트할 workspace를 선택합니다.
4. 왼쪽 메뉴에서 `Incoming Webhooks`를 엽니다.
5. `Activate Incoming Webhooks`를 켭니다.
6. `Add New Webhook to Workspace`를 누릅니다.
7. 메시지를 보낼 채널 또는 DM을 선택하고 `Allow`를 누릅니다.
8. 생성된 `https://hooks.slack.com/services/...` URL을 복사해서 `secrets.json`의 `slack_webhook_url`에 넣습니다.

Incoming Webhook은 설치할 때 선택한 채널로 보내는 방식이라, 일반 Slack 대화방 URL만으로는 전송할 수 없습니다.

기본 스케줄은 매주 수요일 오전 9시 KST입니다. GitHub Actions cron은 UTC 기준이라 `.github/workflows/weekly-digest.yml`에는 `0 0 * * 3`으로 설정되어 있습니다.

Slack 앱 설치 한도로 Incoming Webhook을 추가할 수 없다면 GitHub Issue 방식도 사용할 수 있습니다.

1. GitHub 저장소에 이 코드를 올립니다.
2. Slack에서 GitHub 앱이 설치된 채널 또는 DM에 아래 명령을 입력합니다.

```text
/github subscribe storm0710/aimstletter issues
```

3. GitHub Actions의 `Weekly AI digest issue` workflow가 매주 수요일 오전 9시 KST에 Issue를 생성합니다.
4. Slack에 설치된 GitHub 앱이 새 Issue 알림을 보내줍니다.

수동 테스트는 GitHub 저장소의 `Actions` 탭에서 `Weekly AI digest issue`를 선택한 뒤 `Run workflow`를 누르면 됩니다.

## Source Tuning

피드와 키워드는 [src/aimstletter/config.py](src/aimstletter/config.py)에서 조정합니다.

좋은 수업용 항목의 기준은 다음에 가깝게 잡았습니다.

- AI를 활용한 사업 기회, 제품화, 운영 자동화에 연결되는가
- 멘토링 때 토론 질문으로 이어질 수 있는가
- 모델, 에이전트, 멀티모달, 검색, 평가, 생성형 UX처럼 현재성이 있는가
- 논문은 abstract만 봐도 실험 아이디어나 비즈니스 적용점을 뽑을 수 있는가
