from __future__ import annotations

import requests


def post_to_slack(webhook_url: str, text: str) -> None:
    response = requests.post(
        webhook_url,
        json={
            "text": text,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _truncate_for_slack(text),
                    },
                }
            ],
        },
        timeout=20,
    )
    response.raise_for_status()


def _truncate_for_slack(text: str) -> str:
    return text if len(text) <= 2900 else text[:2890].rstrip() + "\n..."
