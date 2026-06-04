from __future__ import annotations

from datetime import UTC, datetime

from aimstletter.fetchers import DigestItem
from aimstletter.site import render_homepage


def test_render_homepage_contains_ai_and_tool_columns() -> None:
    ai_item = DigestItem(
        title="Database incident response with AI agents",
        url="https://example.com/infra",
        source="Example",
        kind="paper",
        published=datetime(2026, 6, 4, tzinfo=UTC),
        summary="AI agents help DBAs inspect logs, detect anomalies, and shorten incident response.",
    )
    tool_item = DigestItem(
        title="Claude adds a new developer workflow",
        url="https://example.com/claude",
        source="Anthropic News",
        kind="tool",
        published=datetime(2026, 6, 4, tzinfo=UTC),
        summary="Claude updates improve coding and operational work.",
    )

    html = render_homepage([ai_item] * 10, [tool_item])

    assert "AI Master Times" in html
    assert "현장 AI 스킬 · 상위 5개" in html
    assert "Claude와 AI 툴 업데이트" in html
    assert "https://cursor.com/changelog" in html
    assert "Database incident response with AI agents" in html
