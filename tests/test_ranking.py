from __future__ import annotations

from datetime import UTC, datetime

from aimstletter.fetchers import DigestItem
from aimstletter.ranking import rank_items


def test_rank_items_prefers_business_relevant_ai_items() -> None:
    items = [
        DigestItem(
            title="A small benchmark note",
            url="https://example.com/a",
            source="Example",
            kind="trend",
            published=datetime(2026, 6, 1, tzinfo=UTC),
            summary="A narrow benchmark update.",
        ),
        DigestItem(
            title="Agent workflow automation for enterprise AI products",
            url="https://example.com/b",
            source="Example",
            kind="trend",
            published=datetime(2026, 6, 1, tzinfo=UTC),
            summary="Business teams use agents for customer workflow automation.",
        ),
    ]

    ranked = rank_items(items, limit=1)

    assert ranked[0].url == "https://example.com/b"
