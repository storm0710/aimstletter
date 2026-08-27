from __future__ import annotations

from types import SimpleNamespace

from aimstletter.config import FeedSource
from aimstletter.fetchers import _entry_to_item


def test_feed_source_cache_reuses_previous_summary_when_feed_body_is_empty(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("AIMSTLETTER_SOURCE_CACHE_DIR", str(tmp_path))
    feed = FeedSource("Example", "https://example.com/feed.xml", "tool")
    url = "https://example.com/products/real-agent-tool"

    first = _entry_to_item(
        feed,
        SimpleNamespace(
            title="Real Agent Tool",
            link=url,
            published="Wed, 26 Aug 2026 00:00:00 GMT",
            summary="Analyzes production AI agent conversations to find failures and drift.",
        ),
    )
    second = _entry_to_item(
        feed,
        SimpleNamespace(
            title="Real Agent Tool",
            link=url,
            published="Wed, 26 Aug 2026 00:00:00 GMT",
            summary="Real Agent Tool",
        ),
    )

    assert first is not None
    assert second is not None
    assert second.summary == first.summary
