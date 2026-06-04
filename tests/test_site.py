from __future__ import annotations

from datetime import UTC, datetime

from aimstletter.fetchers import DigestItem
from aimstletter.site import _fallback_korean_item, _safe_korean_field, render_homepage


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

    assert "인공지능 마스터 타임즈" in html
    assert "현장 인공지능 스킬 · 상위 5개" in html
    assert "클로드와 인공지능 도구 업데이트" in html
    assert "https://cursor.com/changelog" in html
    assert "최신 업데이트" in html


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
