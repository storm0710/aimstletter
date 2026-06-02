from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class FeedSource:
    name: str
    url: str
    kind: str = "trend"


@dataclass(frozen=True)
class Settings:
    slack_webhook_url: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment: str = "gpt-5-mini"
    lookback_days: int = 7
    max_items: int = 8
    channel_label: str = "AI마스터"
    feeds: tuple[FeedSource, ...] = field(default_factory=tuple)

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        secrets = _load_secret_file()
        return cls(
            slack_webhook_url=_setting("SLACK_WEBHOOK_URL", "slack_webhook_url", secrets),
            openai_api_key=_setting("OPENAI_API_KEY", "openai_api_key", secrets),
            openai_model=_setting("OPENAI_MODEL", "openai_model", secrets, "gpt-5-mini"),
            azure_openai_endpoint=_setting(
                "AZURE_OPENAI_ENDPOINT",
                "azure_openai_endpoint",
                secrets,
            ),
            azure_openai_api_key=_setting(
                "AZURE_OPENAI_API_KEY",
                "azure_openai_api_key",
                secrets,
            ),
            azure_openai_deployment=_setting(
                "AZURE_OPENAI_DEPLOYMENT",
                "azure_openai_deployment",
                secrets,
                "gpt-5-mini",
            ),
            lookback_days=int(os.getenv("DIGEST_LOOKBACK_DAYS", "7")),
            max_items=int(os.getenv("DIGEST_MAX_ITEMS", "8")),
            channel_label=_setting(
                "DIGEST_CHANNEL_LABEL",
                "digest_channel_label",
                secrets,
                "AI마스터",
            ),
            feeds=DEFAULT_FEEDS,
        )


def _load_secret_file() -> dict[str, str]:
    path = Path(os.getenv("AIMSTLETTER_SECRETS_FILE", "secrets.json"))
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")

    return {str(key): str(value) for key, value in data.items() if value}


def _setting(
    env_name: str,
    secret_name: str,
    secrets: dict[str, str],
    default: str | None = None,
) -> str | None:
    return os.getenv(env_name) or secrets.get(secret_name) or default


DEFAULT_FEEDS = (
    FeedSource(
        name="arXiv AI",
        kind="paper",
        url=(
            "https://export.arxiv.org/api/query?"
            "search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG"
            "&sortBy=submittedDate&sortOrder=descending&max_results=25"
        ),
    ),
    FeedSource("MIT Technology Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed/"),
    FeedSource("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    FeedSource("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    FeedSource("OpenAI News", "https://openai.com/news/rss.xml"),
)

SIGNAL_KEYWORDS = {
    "agent": 4,
    "agents": 4,
    "workflow": 3,
    "automation": 3,
    "enterprise": 3,
    "startup": 3,
    "business": 3,
    "product": 2,
    "multimodal": 2,
    "reasoning": 2,
    "rag": 2,
    "retrieval": 2,
    "evaluation": 2,
    "benchmark": 2,
    "llm": 2,
    "generative": 2,
    "customer": 2,
    "market": 2,
    "paper": 1,
}
