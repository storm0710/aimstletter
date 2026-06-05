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
    max_items: int = 10
    channel_label: str = "AI마스터"
    naver_blog_id: str | None = None
    naver_blog_username: str | None = None
    naver_blog_api_password: str | None = None
    site_analytics_provider: str | None = None
    site_analytics_id: str | None = None
    site_analytics_domain: str | None = None
    feeds: tuple[FeedSource, ...] = field(default_factory=tuple)
    tool_feeds: tuple[FeedSource, ...] = field(default_factory=tuple)

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
            max_items=int(os.getenv("DIGEST_MAX_ITEMS", "10")),
            channel_label=_setting(
                "DIGEST_CHANNEL_LABEL",
                "digest_channel_label",
                secrets,
                "AI마스터",
            ),
            naver_blog_id=_setting("NAVER_BLOG_ID", "naver_blog_id", secrets),
            naver_blog_username=_setting(
                "NAVER_BLOG_USERNAME",
                "naver_blog_username",
                secrets,
            ),
            naver_blog_api_password=_setting(
                "NAVER_BLOG_API_PASSWORD",
                "naver_blog_api_password",
                secrets,
            ),
            site_analytics_provider=_setting(
                "SITE_ANALYTICS_PROVIDER",
                "site_analytics_provider",
                secrets,
            ),
            site_analytics_id=_setting(
                "SITE_ANALYTICS_ID",
                "site_analytics_id",
                secrets,
            ),
            site_analytics_domain=_setting(
                "SITE_ANALYTICS_DOMAIN",
                "site_analytics_domain",
                secrets,
            ),
            feeds=DEFAULT_FEEDS,
            tool_feeds=TOOL_UPDATE_FEEDS,
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
        name="arXiv Database AI",
        kind="paper",
        url=(
            "https://export.arxiv.org/api/query?"
            "search_query=cat:cs.DB+AND+%28all:AI+OR+all:LLM+OR+all:agent%29"
            "&sortBy=submittedDate&sortOrder=descending&max_results=15"
        ),
    ),
    FeedSource(
        name="arXiv Network AI",
        kind="paper",
        url=(
            "https://export.arxiv.org/api/query?"
            "search_query=cat:cs.NI+AND+%28all:AI+OR+all:LLM+OR+all:agent%29"
            "&sortBy=submittedDate&sortOrder=descending&max_results=15"
        ),
    ),
    FeedSource(
        name="arXiv Distributed Systems AI",
        kind="paper",
        url=(
            "https://export.arxiv.org/api/query?"
            "search_query=cat:cs.DC+AND+%28all:AI+OR+all:LLM+OR+all:agent%29"
            "&sortBy=submittedDate&sortOrder=descending&max_results=15"
        ),
    ),
    FeedSource(
        name="arXiv Security AI",
        kind="paper",
        url=(
            "https://export.arxiv.org/api/query?"
            "search_query=cat:cs.CR+AND+%28all:AI+OR+all:LLM+OR+all:agent%29"
            "&sortBy=submittedDate&sortOrder=descending&max_results=15"
        ),
    ),
    FeedSource(
        name="arXiv AI",
        kind="paper",
        url=(
            "https://export.arxiv.org/api/query?"
            "search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.LG"
            "+OR+cat:cs.DB+OR+cat:cs.DC+OR+cat:cs.NI+OR+cat:cs.CR"
            "&sortBy=submittedDate&sortOrder=descending&max_results=25"
        ),
    ),
    FeedSource("MIT Technology Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed/"),
    FeedSource("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
    FeedSource("Google AI Blog", "https://blog.google/technology/ai/rss/"),
    FeedSource("OpenAI News", "https://openai.com/news/rss.xml"),
)

TOOL_UPDATE_FEEDS = (
    FeedSource("Anthropic News", "https://www.anthropic.com/news/rss.xml", "tool"),
    FeedSource("OpenAI News", "https://openai.com/news/rss.xml", "tool"),
    FeedSource("GitHub Copilot Changelog", "https://github.blog/changelog/label/copilot/feed/", "tool"),
    FeedSource("GitHub Changelog", "https://github.blog/changelog/feed/", "tool"),
    FeedSource("Google AI Blog", "https://blog.google/technology/ai/rss/", "tool"),
    FeedSource("Microsoft AI Blog", "https://blogs.microsoft.com/ai/feed/", "tool"),
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

INFRA_KEYWORDS = {
    "database": 6,
    "databases": 6,
    "sql": 6,
    "query": 5,
    "queries": 5,
    "index": 4,
    "transaction": 4,
    "replication": 5,
    "backup": 5,
    "recovery": 5,
    "data pipeline": 5,
    "data pipelines": 5,
    "observability": 6,
    "monitoring": 6,
    "incident": 6,
    "root cause": 5,
    "anomaly": 5,
    "anomalies": 5,
    "log": 4,
    "logs": 4,
    "server": 6,
    "servers": 6,
    "linux": 5,
    "kubernetes": 6,
    "container": 5,
    "containers": 5,
    "cloud": 4,
    "network": 6,
    "networks": 6,
    "networking": 6,
    "routing": 5,
    "traffic": 5,
    "latency": 5,
    "throughput": 4,
    "security": 4,
    "access control": 5,
    "configuration": 4,
    "infrastructure": 6,
    "devops": 6,
    "sre": 6,
    "operations": 5,
}
