from datetime import UTC, datetime

from aimstletter.cli import _ai_tool_keyword_score, _append_ai_tool_alerts, _is_ai_product_launch
from aimstletter.config import AI_TOOL_DISCOVERY_KEYWORDS, TOOL_UPDATE_FEEDS
from aimstletter.fetchers import DigestItem


def test_github_digest_alerts_include_new_ai_tool_discovery() -> None:
    item = DigestItem(
        title="New agentic coding workspace",
        url="https://example.com/new-tool",
        source="Product Hunt launches",
        kind="tool",
        published=datetime(2026, 8, 26, tzinfo=UTC),
        summary="An AI agent helps developers plan, write, and test code.",
    )

    digest = _append_ai_tool_alerts("# AI마스터 주간 AI 업데이트", [item])

    assert "## 새 AI 도구·업데이트 알림" in digest
    assert "New agentic coding workspace" in digest
    assert "https://example.com/new-tool" in digest


def test_product_hunt_discovery_feed_and_agentic_keyword_are_enabled() -> None:
    assert any(feed.name == "Product Hunt launches" for feed in TOOL_UPDATE_FEEDS)
    assert "agentic" in AI_TOOL_DISCOVERY_KEYWORDS


def test_ai_keyword_does_not_match_unrelated_words() -> None:
    assert _ai_tool_keyword_score("paid email assistant") == 0
    assert _ai_tool_keyword_score("AI coding assistant") > 0
    assert not _is_ai_product_launch("Workflow automation for invoices")
    assert _is_ai_product_launch("AI workflow automation for invoices")
