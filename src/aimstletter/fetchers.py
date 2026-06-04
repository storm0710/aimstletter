from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
import html
import re

from dateutil import parser as date_parser
import feedparser
import requests

from aimstletter.config import FeedSource


@dataclass(frozen=True)
class DigestItem:
    title: str
    url: str
    source: str
    kind: str
    published: datetime
    summary: str
    score: int = 0


def fetch_recent_items(feeds: tuple[FeedSource, ...], lookback_days: int) -> list[DigestItem]:
    cutoff = datetime.now(UTC) - timedelta(days=lookback_days)
    items: list[DigestItem] = []
    seen_urls: set[str] = set()

    for feed in feeds:
        try:
            response = requests.get(feed.url, timeout=20)
            response.raise_for_status()
        except requests.RequestException:
            continue

        parsed = feedparser.parse(response.content)
        for entry in parsed.entries:
            item = _entry_to_item(feed, entry)
            if not item or item.published < cutoff or item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            items.append(item)

    return items


def _entry_to_item(feed: FeedSource, entry: object) -> DigestItem | None:
    title = _clean_text(getattr(entry, "title", ""))
    url = getattr(entry, "link", "")
    if not title or not url:
        return None

    published = _parse_entry_date(entry)
    summary = _clean_text(
        getattr(entry, "summary", "")
        or getattr(entry, "description", "")
        or getattr(entry, "subtitle", "")
    )

    return DigestItem(
        title=title,
        url=url,
        source=feed.name,
        kind=feed.kind,
        published=published,
        summary=summary,
    )


def _parse_entry_date(entry: object) -> datetime:
    for attr in ("published", "updated", "created"):
        value = getattr(entry, attr, None)
        if not value:
            continue
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            parsed = date_parser.parse(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return datetime.now(UTC)


def _clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()
