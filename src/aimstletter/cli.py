from __future__ import annotations

import argparse
import re
import sys

from aimstletter.composer import compose_digest
from aimstletter.config import AI_TOOL_DISCOVERY_KEYWORDS, Settings
from aimstletter.fetchers import DigestItem, fetch_recent_items
from aimstletter.ranking import rank_items
from aimstletter.slack import post_to_slack


def main() -> int:
    parser = argparse.ArgumentParser(description="Post the weekly AI Master Slack digest.")
    parser.add_argument("--dry-run", action="store_true", help="Print the digest without posting.")
    parser.add_argument("--max-items", type=int, help="Override the maximum number of items.")
    parser.add_argument("--lookback-days", type=int, help="Override the item lookback window.")
    parser.add_argument(
        "--output-format",
        choices=("slack", "github"),
        default="slack",
        help="Output Slack mrkdwn or GitHub Markdown.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    max_items = args.max_items or settings.max_items
    lookback_days = args.lookback_days or settings.lookback_days

    items = fetch_recent_items(settings.feeds, lookback_days)
    ranked_items = rank_items(items, max_items)
    digest = compose_digest(
        ranked_items,
        settings.channel_label,
        settings.openai_api_key,
        settings.openai_model,
        settings.azure_openai_endpoint,
        settings.azure_openai_api_key,
        settings.azure_openai_deployment,
        args.output_format,
    )
    tool_items = fetch_recent_items(settings.tool_feeds, lookback_days)
    digest = _append_ai_tool_alerts(digest, tool_items)

    if args.dry_run:
        print(digest)
        return 0

    if not settings.slack_webhook_url:
        print("SLACK_WEBHOOK_URL is required unless --dry-run is used.", file=sys.stderr)
        return 2

    post_to_slack(settings.slack_webhook_url, digest)
    print("Posted weekly AI digest to Slack.")
    return 0


def _append_ai_tool_alerts(digest: str, items: list[DigestItem]) -> str:
    """Add a notification-friendly list of newly discovered AI tools to the weekly Issue."""
    seen_urls: set[str] = set()
    ranked: list[tuple[int, DigestItem]] = []
    for item in items:
        text = f"{item.title} {item.summary}".lower()
        score = _ai_tool_keyword_score(text)
        if item.source == "Product Hunt launches" and not _is_ai_product_launch(text):
            continue
        if score and item.url not in seen_urls:
            seen_urls.add(item.url)
            ranked.append((score, item))

    selected = sorted(ranked, key=lambda pair: (pair[1].published, pair[0]), reverse=True)[:8]
    if not selected:
        return digest

    lines = ["## 새 AI 도구·업데이트 알림", "", "이번 주 자동 감지한 신규 AI 도구 및 제품 업데이트입니다.", ""]
    for _, item in selected:
        lines.extend(
            (
                f"- **{item.title}** ({item.source})",
                f"  - {item.summary[:220]}",
                f"  - {item.url}",
            )
        )
    return f"{digest.rstrip()}\n\n" + "\n".join(lines) + "\n"


def _ai_tool_keyword_score(text: str) -> int:
    return sum(
        bool(re.search(r"\bai\b", text)) if keyword == "ai" else keyword in text
        for keyword in AI_TOOL_DISCOVERY_KEYWORDS
    )


def _is_ai_product_launch(text: str) -> bool:
    text = text.lower()
    return any(
        (
            bool(re.search(r"\bai\b", text))
            if keyword == "ai"
            else keyword in text
        )
        for keyword in (
            "ai",
            "artificial intelligence",
            "agent",
            "agentic",
            "llm",
            "language model",
            "generative",
            "copilot",
            "mcp",
            "model context protocol",
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
