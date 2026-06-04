from __future__ import annotations

from datetime import UTC, datetime

from aimstletter.fetchers import DigestItem
from aimstletter.site import (
    SiteItem,
    _fallback_korean_item,
    _safe_korean_field,
    _safe_tags,
    render_homepage,
)


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

    html = render_homepage([_fallback_korean_item(ai_item)] * 10, [_fallback_korean_item(tool_item)])

    assert "AI Master Times" in html
    assert "현장 AI 스킬 · 상위 5개" in html
    assert "Claude와 AI 도구 업데이트" in html
    assert "최신 업데이트" in html
    assert "키포인트" in html
    assert "tag" in html
    assert "lead-image" not in html
    assert "watch-links" not in html


def test_safe_korean_field_rejects_untranslated_article_text() -> None:
    title = "OpenAI named a Leader in enterprise coding agents by Gartner"
    summary = (
        "OpenAI is named a leader in the 2026 Gartner Magic Quadrant for "
        "Enterprise AI Coding Agents."
    )

    assert _safe_korean_field(title, fallback="한국어 제목") == "한국어 제목"
    assert _safe_korean_field(summary, fallback="한국어 요약") == "한국어 요약"
    assert (
        _safe_korean_field(
            "OpenAI, 가트너 엔터프라이즈 코딩 에이전트 분야 리더로 선정",
            fallback="한국어 제목",
        )
        == "OpenAI, 가트너 엔터프라이즈 코딩 에이전트 분야 리더로 선정"
    )


def test_render_homepage_orders_each_section_newest_first() -> None:
    old_item = SiteItem(
        title="오래된 항목",
        url="https://example.com/old",
        source="OpenAI 소식",
        kind="동향",
        published=datetime(2026, 6, 1, tzinfo=UTC),
        summary="오래된 요약입니다.",
        key_points=("기존 변경 사항입니다.",),
        tags=("OpenAI",),
    )
    new_item = SiteItem(
        title="최신 항목",
        url="https://example.com/new",
        source="OpenAI 소식",
        kind="동향",
        published=datetime(2026, 6, 5, tzinfo=UTC),
        summary="최신 요약입니다.",
        key_points=("최근 변경 사항입니다.",),
        tags=("OpenAI", "AI 에이전트"),
    )

    html = render_homepage([old_item, new_item, old_item, old_item, old_item], [old_item, new_item])

    assert html.index("최신 항목") < html.index("오래된 항목")
    assert '<span class="tag">AI 에이전트</span>' in html


def test_safe_tags_keeps_product_names_and_deduplicates() -> None:
    original = DigestItem(
        title="OpenAI and GitHub Copilot update",
        url="https://example.com/tool",
        source="OpenAI News",
        kind="tool",
        published=datetime(2026, 6, 5, tzinfo=UTC),
        summary="Tool update.",
    )

    tags = _safe_tags(
        {"tags": ["오픈에이아이", "AI 에이전트", "AI 에이전트", "깃허브 코파일럿"]},
        original,
    )

    assert tags == ("OpenAI", "AI 에이전트", "GitHub Copilot")
