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


def test_rank_items_groups_infra_relevant_items_first_without_duplicates() -> None:
    items = [
        DigestItem(
            title=f"Generic AI product trend {index}",
            url=f"https://example.com/generic-{index}",
            source="Example",
            kind="trend",
            published=datetime(2026, 6, 1, tzinfo=UTC),
            summary="Business product market update.",
        )
        for index in range(8)
    ]
    items.extend(
        [
            DigestItem(
                title="AI observability for database incident response",
                url="https://example.com/infra-1",
                source="Example",
                kind="trend",
                published=datetime(2026, 6, 1, tzinfo=UTC),
                summary="Database monitoring, logs, anomaly detection, and root cause automation.",
            ),
            DigestItem(
                title="Network automation with LLM agents",
                url="https://example.com/infra-2",
                source="Example",
                kind="paper",
                published=datetime(2026, 6, 1, tzinfo=UTC),
                summary="Network routing, traffic, latency, and server operations.",
            ),
        ]
    )

    ranked = rank_items(items, limit=10)

    assert {item.url for item in ranked[:2]} == {
        "https://example.com/infra-1",
        "https://example.com/infra-2",
    }
    assert len({item.url for item in ranked}) == len(ranked)
