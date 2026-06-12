from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path

from aimstletter.fetchers import DigestItem
from aimstletter.config import Settings
from aimstletter.site import (
    SiteItem,
    _fallback_korean_item,
    _item_slug,
    _items_in_window,
    _rank_work_skill_updates,
    _render_analytics,
    _render_detail_page,
    _safe_korean_field,
    _safe_tags,
    _weekly_window,
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
    assert "AI MASTER TIMES" in html
    assert "AI Talent Lab" in html
    assert "Smart Insights" in html
    assert 'data-title="Example: Database incident response with AI agents"' in html
    assert "topic-badge" in html
    assert 'href="ai-tools/"' in html
    assert 'href="ai-sources/"' in html
    assert '<section class="tool-directory"' not in html
    assert "<h3>Codex</h3>" not in html
    assert "상세 목록" not in html
    assert '<a href="#insights" data-smart-insights-link>Smart Insights</a>' not in html
    assert '<a href="work-skills/">Archive</a>' not in html
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


def test_render_homepage_includes_archive_entries() -> None:
    old_item = SiteItem(
        title="오래된 항목",
        url="https://example.com/old",
        source="OpenAI 소식",
        kind="동향",
        published=datetime(2026, 6, 1, tzinfo=UTC),
        summary="오래된 요약입니다.",
        detail="오래된 상세 설명입니다.",
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
        detail="최신 상세 설명입니다.",
        key_points=("최근 변경 사항입니다.",),
        tags=("OpenAI", "AI 에이전트"),
    )

    html = render_homepage(
        [old_item, new_item, old_item, old_item, old_item],
        [old_item, new_item],
        archive_entries=[
            {"year": 2026, "month": 6, "week": 1, "href": "archive/2026/06/week-1/"},
            {"year": 2026, "month": 6, "week": 2, "href": "archive/2026/06/week-2/"},
        ],
        now=datetime(2026, 6, 11, tzinfo=UTC),
    )

    assert "Archive" in html
    assert "2026년" in html
    assert "06월 2째주" in html
    assert 'href="archive/2026/06/week-1/"' in html
    assert html.index("06월 1째주") < html.index("06월 2째주")
    assert 'class="is-current" data-archive-link href="archive/2026/06/week-2/"' in html


def test_weekly_window_uses_previous_wednesday_to_tuesday_range() -> None:
    start, end = _weekly_window(datetime(2026, 6, 10, 6, tzinfo=UTC))

    assert start.date().isoformat() == "2026-06-03"
    assert end.date().isoformat() == "2026-06-09"

    inside = DigestItem(
        title="inside",
        url="https://example.com/inside",
        source="Example",
        kind="tool",
        published=datetime(2026, 6, 3, tzinfo=UTC),
        summary="inside",
    )
    outside = DigestItem(
        title="outside",
        url="https://example.com/outside",
        source="Example",
        kind="tool",
        published=datetime(2026, 6, 2, tzinfo=UTC),
        summary="outside",
    )

    assert _items_in_window([inside, outside], start, end) == [inside]


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


def test_item_slug_is_stable_and_uses_url_hash() -> None:
    item = SiteItem(
        title="Endava가 AI 에이전트를 중심으로 소프트웨어 전달을 재설계",
        url="https://example.com/endava",
        source="OpenAI 소식",
        kind="동향",
        published=datetime(2026, 6, 5, tzinfo=UTC),
        summary="요약입니다.",
        detail="상세입니다.",
        key_points=("키포인트입니다.",),
        tags=("Endava", "AI 에이전트"),
    )

    slug = _item_slug(item)

    assert slug.startswith("endava가-ai-에이전트를-중심으로")
    assert slug == _item_slug(item)


def test_detail_page_includes_comparison_and_glossary_notes() -> None:
    item = SiteItem(
        title="Endava가 AI 에이전트를 중심으로 소프트웨어 전달을 재설계",
        url="https://example.com/endava",
        source="OpenAI 소식",
        kind="동향",
        published=datetime(2026, 6, 5, tzinfo=UTC),
        summary="요약입니다.",
        detail="상세입니다.",
        key_points=("키포인트입니다.",),
        tags=("Endava", "AI 에이전트"),
        comparisons=("Endava는 조직 전환 접근이고 Harness는 전달 자동화 플랫폼입니다.",),
        glossary=("Warp: AI 기능을 결합한 개발자 터미널 도구입니다.",),
    )

    html = _render_detail_page(item, analytics_html="", back_href="../")

    assert "비교 설명" in html
    assert "용어 풀이" in html
    assert "Endava는 조직 전환 접근이고 Harness는 전달 자동화 플랫폼입니다." in html
    assert "Warp: AI 기능을 결합한 개발자 터미널 도구입니다." in html


def test_fallback_item_adds_endava_harness_comparison_and_glossary() -> None:
    original = DigestItem(
        title="Endava uses Codex while teams compare Harness Engineering",
        url="https://example.com/endava-harness",
        source="OpenAI News",
        kind="tool",
        published=datetime(2026, 6, 5, tzinfo=UTC),
        summary="Endava explains AI-native delivery with Codex and workflow automation.",
    )

    item = _fallback_korean_item(original)

    assert any("Harness Engineering" in note for note in item.comparisons)
    assert any("Endava:" in note for note in item.glossary)
    assert any("Codex:" in note for note in item.glossary)


def test_rank_work_skill_updates_prefers_practical_tool_skills() -> None:
    story = DigestItem(
        title="Meta scam story shows an AI security myth",
        url="https://example.com/story",
        source="MIT Technology Review AI",
        kind="trend",
        published=datetime(2026, 6, 5, tzinfo=UTC),
        summary="A case story about a social media account incident.",
    )
    skill = DigestItem(
        title="GitHub Copilot adds workflow automation for Actions failures",
        url="https://example.com/skill",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 6, 4, tzinfo=UTC),
        summary="Developers can automate incident fixes through GitHub Actions and agent workflows.",
    )

    ranked = _rank_work_skill_updates([story, skill], limit=1)

    assert ranked[0].url == "https://example.com/skill"


def test_render_analytics_is_empty_without_provider() -> None:
    assert _render_analytics(Settings()) == ""


def test_render_analytics_supports_ga4() -> None:
    html = _render_analytics(
        Settings(site_analytics_provider="ga4", site_analytics_id="G-TEST123")
    )

    assert "googletagmanager.com/gtag/js?id=G-TEST123" in html
    assert "gtag('config', 'G-TEST123')" in html


def test_render_analytics_supports_goatcounter() -> None:
    html = _render_analytics(
        Settings(site_analytics_provider="goatcounter", site_analytics_id="aimstletter")
    )

    assert "https://aimstletter.goatcounter.com/count" in html
    assert "gc.zgo.at/count.js" in html


def test_committed_pages_root_homepage_exists() -> None:
    html = Path("public/index.html").read_text(encoding="utf-8")

    assert "AI MASTER TIMES" in html
    assert 'href="ai-tools/"' in html
    assert '<section class="tool-directory"' not in html
    assert "<h3>Codex</h3>" not in html
    assert "archive/2026/06/week-2/" in html
    assert 'href="ai-sources/"' in html
    assert html.index("06월 1째주") < html.index("06월 2째주")
    assert "당신의 AI 역량을 성장시켜보세요" in html
    assert "�" not in html


def test_committed_ai_tools_page_exists() -> None:
    html = Path("public/ai-tools/index.html").read_text(encoding="utf-8")

    assert "AI 활용 도구" in html
    assert "background: #ffffff;" in html
    assert "white-space: nowrap;" in html
    assert "tool-category" in html
    assert "개발·코딩 에이전트" in html
    assert "앱 제작·프로토타입" in html
    assert "디자인·UI" in html
    assert "터미널·명령 자동화" in html
    assert "지식·문서·검색" in html
    assert "운영·협업" in html
    assert "tool-list-grid" in html
    assert "<h3>Codex</h3>" in html
    assert "<h3>Antigravity</h3>" in html
    assert "<h3>Claude Code</h3>" in html
    assert "<h3>n8n</h3>" in html
    assert "<h3>Perplexity</h3>" in html
    assert 'class="tool-action"' in html
    assert "https://developers.openai.com/codex/cli" in html
    assert "https://code.claude.com/docs/en/desktop-quickstart" in html
    assert "https://cursor.com/download" in html
    assert 'target="_blank" rel="noopener noreferrer"' in html
    assert "�" not in html


def test_committed_ai_sources_page_exists() -> None:
    html = Path("public/ai-sources/index.html").read_text(encoding="utf-8")

    assert "AI 소스" in html
    assert "source-grid" in html
    assert "GitHub Copilot 변경 이력" in html
    assert "OpenAI 소식" in html
    assert "github.blog" in html
    assert "developers.openai.com" in html
    assert 'target="_blank" rel="noopener noreferrer"' in html
    assert "�" not in html


def test_committed_archive_navigation_and_mobile_detail_rules() -> None:
    week_2 = Path("public/archive/2026/06/week-2/index.html").read_text(encoding="utf-8")
    week_1 = Path("public/archive/2026/06/week-1/index.html").read_text(encoding="utf-8")

    assert 'href="archive/2026/06/week-1/"' in week_2
    assert 'href="archive/2026/06/week-2/"' in week_1
    assert week_2.index("06월 1째주") < week_2.index("06월 2째주")
    assert week_1.index("06월 1째주") < week_1.index("06월 2째주")
    assert "06월 1째주" in week_1
    assert "당신의 AI 역량을 성장시켜보세요" in week_2
    assert "업무 AI" in week_2
    assert "Security validation for third-party coding agents" in week_2
    assert "해당 주간 수집 데이터에서 날짜, 출처, 업무 적용 가능성을 기준" in week_2
    assert "Previous Week" in week_2
    assert 'href="ai-sources/"' in week_2
    assert "전주로" not in week_2
    assert "1. 왜 필요한가요?" in week_2
    assert "2. 핵심 구성 요소:" in week_2
    assert "3. 기존 코드 자동완성과의 차이점:" in week_2
    assert "원문 제목과 요약을 기준으로 선별된 항목입니다." not in week_2
    assert "출처 링크에서 세부 변경 사항과 적용 조건을 확인하세요." not in week_2
    assert "�" not in week_1
    assert "�" not in week_2
    assert '<a class="brand" href="./">AI MASTER TIMES</a>' in week_2
    assert "button.insertAdjacentElement('afterend', detailPanel)" in week_2
    assert ".insight-grid.has-selection .insight-detail { display: flex; }" in week_2
    assert "smartInsightLinks.forEach" in week_2
    assert "data-insight-footnotes-title" in week_2
    assert "단어 설명" in week_2
    assert "const clearInsightSelection" in week_2
    assert "clearInsightSelection();" in week_2
    assert "selectFirstVisibleCard();" in week_2
    assert "window.sessionStorage.setItem(\"aimstletter.archiveInsightsOnly\", \"1\")" in week_2
    assert "2026-06-03~2026-06-09 데이터" in week_2
    assert "grid-template-columns: minmax(0, 1fr) max-content" in week_2
    assert "max-height: calc(100vh - 48px)" in week_2
    assert "overflow-y: auto" in week_2
    assert "justify-content: flex-start" in week_2
    assert "overscroll-behavior: contain" in week_2


def test_committed_weekly_smart_insights_use_week_specific_items() -> None:
    week_2 = Path("public/archive/2026/06/week-2/index.html").read_text(encoding="utf-8")
    week_1 = Path("public/archive/2026/06/week-1/index.html").read_text(encoding="utf-8")
    may_4 = Path("public/archive/2026/05/week-4/index.html").read_text(encoding="utf-8")

    week_2_titles = re.findall(r'data-title="([^"]*)"', week_2)
    week_1_titles = re.findall(r'data-title="([^"]*)"', week_1)
    may_4_titles = re.findall(r'data-title="([^"]*)"', may_4)

    assert week_2_titles
    assert week_1_titles
    assert may_4_titles
    assert week_2_titles != week_1_titles
    assert may_4_titles != week_1_titles
    assert may_4_titles != week_2_titles
    assert len(week_1_titles) == len(set(week_1_titles))
    assert len(may_4_titles) == len(set(may_4_titles))
    assert any("Security validation for third-party coding agents" in title for title in week_2_titles)
    assert any("Prompt to workflow migration" in title for title in week_1_titles)
    assert any("Claude Code SDK orchestration patterns" in title for title in may_4_titles)
    assert any("OpenAI Responses API tool calling update" in title for title in may_4_titles)
    assert any("GitHub Copilot pull request review workflow" in title for title in may_4_titles)
    assert "2026-05-20~2026-05-26" in may_4
    assert not any("Prompt to workflow migration" in title for title in may_4_titles)
    assert "Harness Engineering" not in week_2_titles
    assert "Harness Engineering" not in week_1_titles
    assert "Harness Engineering" not in may_4_titles


def test_weekly_pages_workflow_runs_wednesday_6am_kst() -> None:
    workflow = Path(".github/workflows/weekly-pages.yml").read_text(encoding="utf-8")

    assert "06:00 every Wednesday in Asia/Seoul" in workflow
    assert 'cron: "0 21 * * 2"' in workflow
