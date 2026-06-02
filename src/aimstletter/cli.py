from __future__ import annotations

import argparse
import sys

from aimstletter.composer import compose_digest
from aimstletter.config import Settings
from aimstletter.fetchers import fetch_recent_items
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

    if args.dry_run:
        print(digest)
        return 0

    if not settings.slack_webhook_url:
        print("SLACK_WEBHOOK_URL is required unless --dry-run is used.", file=sys.stderr)
        return 2

    post_to_slack(settings.slack_webhook_url, digest)
    print("Posted weekly AI digest to Slack.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
