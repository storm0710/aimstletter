from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time

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
        response = _fetch_feed_response(feed.url)
        if response is None:
            continue

        parsed = feedparser.parse(response.content)
        for entry in parsed.entries:
            item = _entry_to_item(feed, entry)
            if not item or item.published < cutoff or item.url in seen_urls:
                continue
            seen_urls.add(item.url)
            items.append(item)

    return items


def _fetch_feed_response(url: str, attempts: int = 5) -> requests.Response | None:
    last_error: requests.RequestException | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 + attempt)
    print(f"Could not fetch feed {url} after {attempts} attempts: {last_error}", file=sys.stderr)
    return None


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
    cached_summary = _read_cached_summary(url)
    if cached_summary and (not summary or summary.strip().lower() == title.strip().lower()):
        summary = cached_summary

    item = DigestItem(
        title=title,
        url=url,
        source=feed.name,
        kind=feed.kind,
        published=published,
        summary=summary,
    )
    _write_source_cache(item)
    return item


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


def _source_cache_dir() -> Path:
    return Path(os.environ.get("AIMSTLETTER_SOURCE_CACHE_DIR", ".cache/aimstletter/source-text"))


def _source_cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return _source_cache_dir() / f"{digest}.json"


def _read_cached_summary(url: str) -> str:
    path = _source_cache_path(url)
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    summary = data.get("summary", "")
    return _clean_text(str(summary)) if summary else ""


def _write_source_cache(item: DigestItem) -> None:
    if not item.summary:
        return
    path = _source_cache_path(item.url)
    payload = {
        "title": item.title,
        "url": item.url,
        "source": item.source,
        "kind": item.kind,
        "published": item.published.isoformat(),
        "summary": item.summary,
        "cached_at": datetime.now(UTC).isoformat(),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        return
