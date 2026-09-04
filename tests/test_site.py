from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from aimstletter.fetchers import DigestItem
from aimstletter.config import AI_TOOL_DISCOVERY_KEYWORDS, Settings, TOOL_UPDATE_FEEDS
from aimstletter.knowledge_content import (
    KNOWLEDGE_PAGES,
    REQUIRED_KNOWLEDGE_METADATA,
    validate_knowledge_pages,
)
from aimstletter.site import (
    KNOWLEDGE_TOPICS,
    SiteItem,
    _collect_archive_entries,
    _fallback_display_summary,
    _fallback_korean_item,
    _fallback_three_line_summary,
    _dedupe_insight_buttons_in_html,
    _has_reused_or_generic_localizations,
    _item_slug,
    _items_in_window,
    _localized_site_item,
    _rank_work_skill_updates,
    _repair_archive_card_interaction_script,
    _render_analytics,
    _render_ai_tool_directory,
    _render_detail_page,
    _render_knowledge_topic_page,
    _safe_korean_field,
    _safe_tags,
    _weekly_archive_entry,
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
    assert 'data-title="Example: Database incident response with AI agents"' not in html
    assert "Database incident response with AI agents" not in html
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


def test_render_homepage_backfills_card_limit_after_copy_quality_filter() -> None:
    valid = SiteItem(
        title="운영 자동화 업데이트",
        url="https://example.com/valid-0",
        source="Example",
        kind="동향",
        published=datetime(2026, 8, 31, tzinfo=UTC),
        summary="운영 담당자가 자동화 절차의 실행 상태와 승인 지점을 확인할 수 있습니다.",
        detail="자동화 작업을 단계별로 추적하고 문제가 생긴 구간을 빠르게 찾는 방법을 설명합니다.",
        key_points=("1. 한 줄 요약: 자동화 실행 상태를 단계별로 확인합니다.",),
        tags=("운영 자동화",),
    )
    invalid = replace(
        valid,
        title="본문이 부족한 항목",
        url="https://example.com/invalid",
        summary="수집된 본문 요약이 부족해 제목과 출처 범위에서만 다룹니다.",
    )
    valid_items = [
        replace(valid, title=f"운영 자동화 업데이트 {index}", url=f"https://example.com/valid-{index}")
        for index in range(1, 12)
    ]

    html = render_homepage([invalid, *valid_items], [])

    assert html.count('<button class="insight-card"') == 10
    assert "본문이 부족한 항목" not in html


def test_render_homepage_deduplicates_identical_visible_cards_with_different_urls() -> None:
    item = SiteItem(
        title="OpenAI 도구와 AI 에이전트",
        url="https://example.com/update-a",
        source="OpenAI 소식",
        kind="도구",
        published=datetime(2026, 8, 31, tzinfo=UTC),
        summary="OpenAI 소식에서 공개한 자료의 핵심 변경과 적용 범위를 다룹니다.",
        detail="업무에 적용할 수 있는 기능과 범위를 설명합니다.",
        key_points=("1. 한 줄 요약: 핵심 변경과 적용 범위를 설명합니다.",),
        tags=("OpenAI",),
    )
    duplicate = replace(item, url="https://example.com/update-b")

    html = render_homepage([item, duplicate], [])

    assert html.count('<button class="insight-card"') == 1
    assert 'data-source="https://example.com/update-a"' in html
    assert 'data-source="https://example.com/update-b"' not in html


def test_smart_insight_moves_source_prefix_to_badge_and_koreanizes_title() -> None:
    item = SiteItem(
        title=(
            "arXiv 데이터베이스 AI: Query-Centric Optimization of AI Workflows "
            "via Approximate Algorithms"
        ),
        url="https://example.com/query",
        source="arXiv 데이터베이스 AI",
        kind="논문",
        published=datetime(2026, 7, 6, tzinfo=UTC),
        summary="AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위한 연구입니다.",
        detail="AI가 데이터베이스를 다룰 때 필요한 통제 방식을 설명합니다.",
        key_points=("읽기 전용 권한과 쿼리 검토가 중요합니다.",),
        tags=("AI 에이전트",),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 8, tzinfo=UTC))

    assert '<span class="card-title">AI 워크플로의 쿼리 중심 최적화</span>' in html
    assert '<span class="topic-badge sub">arXiv 데이터베이스 AI</span>' in html
    assert '<span class="card-title">arXiv 데이터베이스 AI:' not in html


def test_smart_insight_uses_specific_tool_titles_instead_of_generic_topics() -> None:
    item = SiteItem(
        title="Copilot agent session streaming is now in public preview",
        url="https://github.blog/changelog/2026-07-02-copilot-agent-session-streaming-is-now-in-public-preview",
        source="GitHub Copilot 변경 이력",
        kind="도구 업데이트",
        published=datetime(2026, 7, 3, tzinfo=UTC),
        summary="반복되는 코드 수정과 PR 보조 작업을 줄여주는 GitHub Copilot 업데이트입니다.",
        detail="반복되는 코드 수정과 PR 보조 작업을 줄여주는 GitHub Copilot 업데이트입니다.",
        key_points=("세션 진행 상황을 더 잘 확인할 수 있습니다.",),
        tags=("GitHub Copilot",),
    )

    html = render_homepage([], [item], now=datetime(2026, 7, 8, tzinfo=UTC))

    assert '<span class="card-title">Copilot 에이전트 세션 스트리밍</span>' in html
    assert '<span class="card-title">개발 도구와 코딩 자동화</span>' not in html


def test_smart_insight_rewrites_generic_localized_titles_from_url_context() -> None:
    item = SiteItem(
        title="개발 도구와 코딩 자동화",
        url="https://github.blog/changelog/2026-07-02-copilot-agent-session-streaming-is-now-in-public-preview",
        source="GitHub Copilot 변경 이력",
        kind="도구 업데이트",
        published=datetime(2026, 7, 3, tzinfo=UTC),
        summary="반복되는 코드 수정과 PR 보조 작업을 줄여주는 GitHub Copilot 업데이트입니다.",
        detail="반복되는 코드 수정과 PR 보조 작업을 줄여주는 GitHub Copilot 업데이트입니다.",
        key_points=("세션 진행 상황을 더 잘 확인할 수 있습니다.",),
        tags=("GitHub Copilot",),
    )

    html = render_homepage([], [item], now=datetime(2026, 7, 8, tzinfo=UTC))

    assert '<span class="card-title">Copilot 에이전트 세션 스트리밍</span>' in html
    assert '<span class="card-title">개발 도구와 코딩 자동화</span>' not in html


def test_smart_insight_rewrites_generic_summary_from_url_context() -> None:
    item = SiteItem(
        title="AI 워크플로의 쿼리 중심 최적화",
        url="https://arxiv.org/abs/2607.03501v1",
        source="arXiv 데이터베이스 AI",
        kind="논문",
        published=datetime(2026, 7, 1, tzinfo=UTC),
        summary="AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다. 읽기 전용 권한, 스키마 범위 제한, 쿼리 검토, 감사 로그입니다.",
        detail="AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다. 읽기 전용 권한, 스키마 범위 제한, 쿼리 검토, 감사 로그입니다.",
        key_points=(
            "1. 왜 필요한가요? AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 읽기 전용 권한, 스키마 범위 제한, 쿼리 검토, 감사 로그입니다.",
            "3. 일반 DB 도구와의 차이점: 사람이 직접 쿼리하는 상황보다 AI의 자동 실행 위험을 더 강하게 통제합니다.",
        ),
        tags=("AI 에이전트",),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 8, tzinfo=UTC))

    assert "기상 데이터처럼 시간·공간 조건이 있는 질문을 SQL로 바꾸는 Text-to-SQL 연구입니다." in html
    assert "시공간 조건 해석" in html
    card = re.search(r'<button class="insight-card"[^>]+data-source="https://arxiv.org/abs/2607.03501v1"[^>]*>', html)
    assert card
    assert "실수로 위험한 조회나 변경" not in card.group(0)


def test_smart_insight_rewrites_broken_question_mark_title() -> None:
    item = SiteItem(
        title="AI 에이전트와 업무 자동화 ? ???",
        url="https://blog.google/innovation-and-ai/technology/ai/full-stack-ai-explainer/",
        source="Google AI 블로그",
        kind="도구 업데이트",
        published=datetime(2026, 7, 1, tzinfo=UTC),
        summary="터미널에서 코드 탐색, 수정, 리팩터링을 끊기지 않고 이어가기 위해 필요합니다.",
        detail="터미널에서 코드 탐색, 수정, 리팩터링을 끊기지 않고 이어가기 위해 필요합니다.",
        key_points=("1. 왜 필요한가요? 터미널에서 코드 탐색, 수정, 리팩터링을 끊기지 않고 이어가기 위해 필요합니다.",),
        tags=("AI 에이전트",),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 8, tzinfo=UTC))

    assert '<span class="card-title">풀스택 AI 앱 구조 설명</span>' in html
    assert "AI 에이전트와 업무 자동화 ? ???" not in html
    assert "풀스택 AI 애플리케이션을 구성하는 화면, 서버, 모델 호출, 데이터 흐름" in html
    card = re.search(
        r'<button class="insight-card"[^>]+data-source="https://blog.google/innovation-and-ai/technology/ai/full-stack-ai-explainer/"[^>]*>',
        html,
    )
    assert card
    assert "터미널에서 코드 탐색" not in card.group(0)


def test_smart_insight_uses_specific_titles_for_new_week_arxiv_items() -> None:
    item = SiteItem(
        title="네트워크 운영 AI 활용",
        url="https://arxiv.org/abs/2607.08282v1",
        source="arXiv 보안 AI",
        kind="논문",
        published=datetime(2026, 7, 9, tzinfo=UTC),
        summary="AI 앱을 빠르게 공개하고 프론트엔드와 서버 기능을 함께 운영하기 위해 필요합니다.",
        detail="AI 앱을 빠르게 공개하고 프론트엔드와 서버 기능을 함께 운영하기 위해 필요합니다.",
        key_points=("1. 무엇을 다루나요? 네트워크 운영 AI 활용 주제를 다룹니다.",),
        tags=("AI 에이전트", "보안"),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 14, tzinfo=UTC))

    assert '<span class="card-title">민감 데이터 보호용 멀티 에이전트 방화벽</span>' in html
    assert "민감 데이터 유출을 막기 위한 멀티 에이전트 방화벽 구조" in html
    card = re.search(r'<button class="insight-card"[^>]+data-source="https://arxiv.org/abs/2607.08282v1"[^>]*>', html)
    assert card
    assert "네트워크 운영 AI 활용" not in card.group(0)
    assert "프론트엔드와 서버 기능" not in card.group(0)


def test_smart_insight_uses_specific_titles_for_latest_week_arxiv_items() -> None:
    item = SiteItem(
        title="데이터베이스 업무 AI 활용",
        url="https://arxiv.org/abs/2607.10265v1",
        source="arXiv 데이터베이스 AI",
        kind="논문",
        published=datetime(2026, 7, 11, tzinfo=UTC),
        summary="오래 걸리는 AI 작업이 중간에 실패해도 재시도와 복구를 안정적으로 처리하기 위해 필요합니다.",
        detail="오래 걸리는 AI 작업이 중간에 실패해도 재시도와 복구를 안정적으로 처리하기 위해 필요합니다.",
        key_points=("1. 무엇을 다루나요? 데이터베이스 업무 AI 활용 주제를 다룹니다.",),
        tags=("AI 에이전트", "데이터베이스"),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 14, tzinfo=UTC))

    assert '<span class="card-title">시간 이력 그래프를 다루는 에이전트 DBMS</span>' in html
    assert "bi-temporal 그래프 관리 시스템" in html
    card = re.search(r'<button class="insight-card"[^>]+data-source="https://arxiv.org/abs/2607.10265v1"[^>]*>', html)
    assert card
    assert "데이터베이스 업무 AI 활용" not in card.group(0)
    assert "재시도와 복구" not in card.group(0)


def test_smart_insight_recomputes_specific_paper_points_when_seed_points_are_mismatched() -> None:
    item = SiteItem(
        title="HPC 워크플로의 자연어 실행 오케스트레이션",
        url="https://arxiv.org/abs/2607.10081v1",
        source="arXiv 분산시스템 AI",
        kind="논문",
        published=datetime(2026, 7, 11, tzinfo=UTC),
        summary="HPC 애플리케이션과 워크플로를 자연어 설명과 도구 호출로 실행하는 접근입니다.",
        detail="HPC 애플리케이션과 워크플로를 자연어 설명과 도구 호출로 실행하는 접근입니다.",
        key_points=(
            "1. 한 줄 요약: 시간 이력이 함께 기록되는 그래프 데이터를 에이전트가 안정적으로 질의하도록 만든 bi-temporal 그래프 관리 시스템입니다.",
            "2. 무엇이 바뀌었나: bi-temporal 그래프, 검증된 시간 연산자, 비용 제한, 결정적 도구 호출입니다.",
            "3. 왜 중요한가: 이력 데이터나 감사 로그를 AI가 조회할 때는 자연어 답변보다 검증 가능한 연산 경계가 필요합니다.",
            "4. 한계와 주의사항: 아직 논문 단계일 수 있습니다.",
            "5. 이번 주 해볼 일: 작은 실험 1개를 정해보세요.",
            "6. 누가 보면 좋은가: AI 엔지니어",
            "7. 출처와 상태: arXiv 분산시스템 AI · 논문 · 2026-07-11",
        ),
        tags=("AI 에이전트",),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 14, tzinfo=UTC))

    card = re.search(r'<button class="insight-card"[^>]+data-source="https://arxiv.org/abs/2607.10081v1"[^>]*>', html)
    assert card
    assert "HPC 애플리케이션과 워크플로" in card.group(0)
    assert "bi-temporal 그래프 관리 시스템" not in card.group(0)


def test_smart_insight_uses_paper_specific_summary_for_week_one_arxiv_items() -> None:
    item = SiteItem(
        title="데이터 에이전트 성능 벤치마크",
        url="https://arxiv.org/abs/2607.01647v1",
        source="arXiv 데이터베이스 AI",
        kind="논문",
        published=datetime(2026, 7, 2, tzinfo=UTC),
        summary="AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다.",
        detail="AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다.",
        key_points=("1. 왜 필요한가요? AI가 데이터베이스를 다룰 때 실수하지 않게 하기 위해 필요합니다.",),
        tags=("AI 에이전트", "데이터베이스"),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 8, tzinfo=UTC))

    assert '<span class="card-title">데이터 에이전트 성능 벤치마크</span>' in html
    assert "AgenticDataBench는 데이터 과학 업무를 자동화하는 LLM 기반 데이터 에이전트" in html
    card = re.search(r'<button class="insight-card"[^>]+data-source="https://arxiv.org/abs/2607.01647v1"[^>]*>', html)
    assert card
    assert "실수로 위험한 조회나 변경" not in card.group(0)
    assert "읽기 전용 권한" not in card.group(0)


def test_smart_insight_uses_specific_summary_for_july_twentieth_items() -> None:
    item = SiteItem(
        title="Claude와 생성형 AI 도구",
        url="https://venturebeat.com/ai/the-agent-security-gap-54-of-enterprises-have-already-had-an-ai-agent-incident-and-most-still-let-agents-share-credentials",
        source="VentureBeat AI",
        kind="동향",
        published=datetime(2026, 7, 17, tzinfo=UTC),
        summary="AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다.",
        detail="AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다.",
        key_points=("1. 무엇을 다루나요? Claude와 생성형 AI 도구 주제를 다룹니다.",),
        tags=("OpenAI", "AI 에이전트"),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 21, tzinfo=UTC))

    card = re.search(
        r'<button class="insight-card"[^>]+data-source="https://venturebeat.com/ai/the-agent-security-gap-54-of-enterprises-have-already-had-an-ai-agent-incident-and-most-still-let-agents-share-credentials"[^>]*>',
        html,
    )
    assert card
    assert 'data-title="AI 에이전트 자격 증명 공유 리스크"' in card.group(0)
    assert "에이전트 간 자격 증명 공유를 허용한다는 보안 리스크" in card.group(0)
    assert "Claude와 생성형 AI 도구" not in card.group(0)
    assert "실수로 위험한 조회나 변경" not in card.group(0)


def test_smart_insight_skips_unmapped_generic_items_without_source_summary() -> None:
    item = SiteItem(
        title="Claude와 생성형 AI 도구",
        url="https://example.com/ai/the-enterprise-agent-reliability-gap-for-production-workflows",
        source="Example AI",
        kind="동향",
        published=datetime(2026, 7, 21, tzinfo=UTC),
        summary="이번 업데이트가 어떤 업무 문제를 해결하는지 업무 적용 관점으로 요약합니다.",
        detail="이번 업데이트가 어떤 업무 문제를 해결하는지 업무 적용 관점으로 요약합니다.",
        key_points=("1. 무엇을 다루나요? Claude와 생성형 AI 도구 주제를 다룹니다.",),
        tags=("AI 에이전트", "엔터프라이즈"),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 7, 21, tzinfo=UTC))

    card = re.search(
        r'<button class="insight-card"[^>]+data-source="https://example.com/ai/the-enterprise-agent-reliability-gap-for-production-workflows"[^>]*>',
        html,
    )
    assert card is None


def test_ai_tool_directory_includes_logo_roll_tools() -> None:
    html = _render_ai_tool_directory()

    for tool in (
        "Stitch",
        "getdesign.md",
        "Supabase",
        "Neon",
        "Temporal",
        "Harness",
        "Pinecone",
        "Qdrant",
        "Datadog",
        "Infisical",
    ):
        assert f"<h3>{tool}</h3>" in html


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
            {"year": 2026, "month": 5, "week": 4, "href": "archive/2026/05/week-4/"},
            {"year": 2026, "month": 6, "week": 1, "href": "archive/2026/06/week-1/"},
            {"year": 2026, "month": 6, "week": 2, "href": "archive/2026/06/week-2/"},
        ],
        now=datetime(2026, 6, 11, tzinfo=UTC),
    )

    assert "Archive" in html
    assert "Knowledge" in html
    assert 'href="knowledge/langchain/"' in html
    assert 'href="knowledge/harness-engineering/"' in html
    assert "01.LangChain" in html
    assert "05.하네스 엔지니어링" in html
    assert "06.루프 엔지니어링" in html
    assert "07.그래프 엔지니어링" in html
    assert "1.1 프롬프트" not in html
    assert "data-archive-index=" in html
    assert '<details class="archive-year-group archive-month-group"><summary class="archive-year archive-month-summary">05월</summary>' in html
    assert '<details class="archive-year-group archive-month-group" open><summary class="archive-year archive-month-summary">06월</summary>' in html
    assert "point-question" in html
    assert "point-answer" in html
    assert "monthGroup.open = true" in html
    assert "2026년" in html
    assert "06월 2째주" in html
    assert 'href="archive/2026/06/week-1/"' in html
    assert html.index("06월 1째주") < html.index("06월 2째주")
    assert 'class="is-current" data-archive-link' in html
    assert 'href="archive/2026/06/week-2/"' in html


def test_archive_navigation_keeps_week_when_one_card_fails_copy_quality(tmp_path: Path) -> None:
    archive_path = tmp_path / "archive" / "2026" / "06" / "week-3" / "index.html"
    archive_path.parent.mkdir(parents=True)
    archive_path.write_text(
        """
        <button class="insight-card" data-insight-card
          data-title="개발 도구와 코딩 자동화"
          data-source="https://example.com/update"
          data-subcategory="Example"
          data-category="도구"
          data-body="원문 제목과 링크를 보존했습니다."
          data-detail="원문을 확인해야 합니다."
          data-meta="Example · 도구 · 2026-06-17"
          data-points="[]"
          data-tags="[]"></button>
        """,
        encoding="utf-8",
    )

    current_entry = _weekly_archive_entry(datetime(2026, 9, 1, tzinfo=UTC))
    entries = _collect_archive_entries(tmp_path, current_entry)

    assert any(
        entry["year"] == 2026 and entry["month"] == 6 and entry["week"] == 3
        for entry in entries
    )


def test_weekly_window_uses_previous_monday_7am_to_current_monday_7am_range() -> None:
    start, end = _weekly_window(datetime(2026, 6, 15, 0, tzinfo=UTC))

    assert start.isoformat() == "2026-06-08T07:00:00+09:00"
    assert end.isoformat() == "2026-06-15T07:00:00+09:00"

    inside = DigestItem(
        title="inside",
        url="https://example.com/inside",
        source="Example",
        kind="tool",
        published=datetime(2026, 6, 8, 0, tzinfo=UTC),
        summary="inside",
    )
    outside = DigestItem(
        title="outside",
        url="https://example.com/outside",
        source="Example",
        kind="tool",
        published=datetime(2026, 6, 7, 21, 59, tzinfo=UTC),
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


def test_fallback_summary_uses_item_specific_explanation() -> None:
    item = DigestItem(
        title="Security validation for third-party coding agents",
        url="https://github.blog/changelog/2026-06-09-security-validation-for-third-party-coding-agents",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 6, 9, tzinfo=UTC),
        summary="Security validation for third-party coding agents.",
    )

    summary = _fallback_display_summary(item)
    points = _fallback_three_line_summary(item)

    assert "서드파티 코딩 에이전트" in summary
    assert "신원과 권한" in summary
    assert any("보안 절차" in point for point in points)
    assert "공개된 개발 도구와 코딩 자동화 관련 소식" not in summary
    assert "새 기능이나 변경 사항이 업무 흐름" not in summary


def test_fallback_summary_avoids_generic_placeholder_points() -> None:
    item = DigestItem(
        title="Advancing Responsible AI",
        url="https://openai.com/index/advancing-responsible-ai-across-europe",
        source="OpenAI News",
        kind="tool",
        published=datetime(2026, 7, 30, tzinfo=UTC),
        summary="Advancing Responsible AI",
    )

    summary = _fallback_display_summary(item)
    points = _fallback_three_line_summary(item)

    assert "유럽" in summary
    assert "EU AI Act" in summary
    assert any("투명성" in point for point in points)
    assert all("주제를 다룹니다" not in point for point in points)
    assert all("원문에서 다루는 문제" not in point for point in points)


def test_unknown_arxiv_database_item_keeps_its_source_specific_summary() -> None:
    item = DigestItem(
        title="Self Prompting Cross",
        url="https://arxiv.org/abs/2608.19025v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 20, tzinfo=UTC),
        summary="Self-prompting and cross-model consensus enable reproducible data extraction from scientific literature.",
    )

    summary = _fallback_display_summary(item)
    points = _fallback_three_line_summary(item)

    assert "과학 논문" in summary
    assert "AI가 데이터베이스와 쿼리 작업을 더 안전하고 정확하게" not in summary
    assert "스키마 이해, 쿼리 생성 또는 최적화" not in " ".join(points)
    assert "한 번 쓰고 버리는 프롬프트" not in " ".join(points)


def test_localization_repair_detects_reused_or_generic_summaries() -> None:
    repeated = [
        {"summary": "원문 내용을 업무 관점으로 정리했습니다.", "detail": "첫 번째 항목의 설명입니다."},
        {"summary": "원문 내용을 업무 관점으로 정리했습니다.", "detail": "두 번째 항목의 설명입니다."},
    ]
    distinct = [
        {"summary": "코드 변경 전에 비밀값 접근 권한을 검사하는 업데이트입니다.", "detail": "저장소 권한과 감사 기록을 분리해 관리합니다."},
        {"summary": "쿼리 계획을 비교해 데이터베이스 질의를 개선하는 논문입니다.", "detail": "실행 전 검증으로 잘못된 질의를 줄이는 방법을 평가합니다."},
    ]

    assert _has_reused_or_generic_localizations(repeated)
    assert not _has_reused_or_generic_localizations(distinct)


def test_quote_bench_localized_item_uses_command_path_specific_summary() -> None:
    item = DigestItem(
        title="QuoteBench: How Matched Scores Can Hide Command-Path Failures",
        url="https://arxiv.org/abs/2608.13547v1",
        source="arXiv AI",
        kind="paper",
        published=datetime(2026, 8, 14, tzinfo=UTC),
        summary=(
            "LLM coding agents issue Bash commands through interfaces that may serialize, "
            "wrap, and reparse model output."
        ),
    )
    localized_item = {
        "title": "Quotebench Matched Scores",
        "summary": "여러 단계로 이어지는 AI 작업이나 분산 실행 흐름을 안정적으로 운영하는 방법을 다룹니다.",
        "detail": "작업 상태, 실행 순서, 재시도와 복구, 비용과 성능 제약입니다.",
        "key_points": [
            "1. 한 줄 요약: 여러 단계로 이어지는 AI 작업이나 분산 실행 흐름을 안정적으로 운영하는 방법을 다룹니다.",
            "2. 무엇이 바뀌었나: 작업 상태, 실행 순서, 재시도와 복구, 비용과 성능 제약입니다.",
            "3. 왜 중요한가: 장기 실행 에이전트를 운영할 때 실패한 단계부터 재개합니다.",
            "4. 한계와 주의사항: 아직 논문 단계일 수 있습니다.",
            "5. 이번 주 해볼 일: 작은 화면 1개를 체크리스트로 검토해보세요.",
            "6. 누가 보면 좋은가: 프론트엔드, 백엔드, AI 엔지니어",
            "7. 출처와 상태: arXiv AI · arXiv 논문 · 2026-08-14",
        ],
        "tags": ["AI 에이전트", "코딩 자동화"],
    }

    site_item = _localized_site_item(item, localized_item)

    assert site_item.title == "QuoteBench: 명령 실행 경로 평가"
    assert "Bash 명령 실행 성능" in site_item.summary
    assert "56개 one-shot Bash 작업" in site_item.key_points[1]
    assert "작업 상태, 실행 순서, 재시도와 복구" not in " ".join(site_item.key_points)


def test_august_arxiv_items_use_source_specific_summaries_instead_of_domain_templates() -> None:
    cases = (
        (
            "CTIFoundry: An Agent-Native Corpus Scaffold for Cyber Threat Intelligence",
            "https://arxiv.org/abs/2608.18613v1",
            "arXiv Security AI",
            "Cyber threat intelligence is increasingly consumed by LLM agents that compose multi-step investigations.",
            "CTIFoundry",
            "CTI",
        ),
        (
            "Walk Before You Run: The Importance of Data Exploration for Data Analysis Agents",
            "https://arxiv.org/abs/2608.16045v1",
            "arXiv Database AI",
            "Reliable data analysis depends on understanding what the dataset contains before solving the requested task.",
            "데이터 분석 에이전트",
            "스프레드시트",
        ),
        (
            "AI4AI-Bench: Benchmarking LLM Agents in Algorithmic Design for Recursive Self-Improvement",
            "https://arxiv.org/abs/2608.20318v1",
            "arXiv AI",
            "Recursive self-improvement asks whether an AI system can improve the process that produces AI systems.",
            "AI4AI-Bench",
            "학습 알고리즘",
        ),
    )
    generic_localized = {
        "title": "데이터베이스 업무 AI 활용",
        "summary": "AI가 데이터베이스와 쿼리 작업을 더 안전하고 정확하게 다루는 방법을 살펴봅니다. 스키마 이해, 쿼리 생성 또는 최적화, 실행 전 검토, 데이터 변경 위험 통제입니다.",
        "detail": "AI가 데이터베이스와 쿼리 작업을 더 안전하고 정확하게 다루는 방법을 살펴봅니다. 스키마 이해, 쿼리 생성 또는 최적화, 실행 전 검토, 데이터 변경 위험 통제입니다.",
        "key_points": [
            "1. 한 줄 요약: AI가 데이터베이스와 쿼리 작업을 더 안전하고 정확하게 다루는 방법을 살펴봅니다.",
            "2. 무엇이 바뀌었나: 스키마 이해, 쿼리 생성 또는 최적화, 실행 전 검토, 데이터 변경 위험 통제입니다.",
            "3. 왜 중요한가: 데이터 에이전트나 자연어 질의 기능을 만들 때 읽기 전용 권한, 검증 절차, 감사 로그를 함께 설계해야 합니다.",
            "4. 한계와 주의사항: 아직 논문 단계일 수 있습니다.",
            "5. 이번 주 해볼 일: 작은 PoC를 만들어보세요.",
            "6. 누가 보면 좋은가: AI 엔지니어",
            "7. 출처와 상태: arXiv · 논문 · 2026-08-19",
        ],
        "tags": ["AI 에이전트"],
    }

    for title, url, source, summary, expected_title, expected_summary in cases:
        item = DigestItem(
            title=title,
            url=url,
            source=source,
            kind="paper",
            published=datetime(2026, 8, 20, tzinfo=UTC),
            summary=summary,
        )

        site_item = _localized_site_item(item, generic_localized)

        assert expected_title in site_item.title
        assert expected_summary in site_item.summary
        assert "스키마 이해, 쿼리 생성 또는 최적화" not in site_item.summary
        assert "데이터 변경 위험 통제" not in " ".join(site_item.key_points)


def test_smart_insight_points_render_answer_on_next_line_without_space_after_question() -> None:
    item = SiteItem(
        title="Upcoming August GitHub Copilot",
        url="https://github.blog/changelog/2026-08-01-upcoming-august-github-copilot",
        source="GitHub Copilot 변경 이력",
        kind="도구 업데이트",
        published=datetime(2026, 8, 1, tzinfo=UTC),
        summary="반복되는 코드 수정을 줄이는 업데이트입니다.",
        detail="반복되는 코드 수정을 줄이는 업데이트입니다.",
        key_points=(
            "1. 한 줄 요약:반복되는 코드 수정과 PR 보조를 줄여줍니다.",
            "2. 무엇이 바뀌었나:코드 맥락 이해와 테스트·PR 흐름 연결이 강화됐습니다.",
            "3. 왜 중요한가:한 줄 추천을 넘어 이슈 해결 흐름을 돕습니다.",
            "4. 한계와 주의사항:저장소 권한과 테스트 결과를 반드시 확인해야 합니다.",
            "5. 이번 주 해볼 일:낮은 우선순위 이슈 1개로 PR 초안 작성을 시험해보세요.",
            "6. 누가 보면 좋은가:프론트엔드, 백엔드, AI 엔지니어",
            "7. 출처와 상태:GitHub Copilot 변경 이력 · 공식 발표 · 2026-08-01",
        ),
        tags=("GitHub Copilot",),
    )

    html = render_homepage([item] * 5, [], now=datetime(2026, 8, 5, tzinfo=UTC))

    assert '<span class="point-question"><span class="point-number">1.</span> 한 줄 요약:</span>' in html
    assert '<span class="point-answer">반복되는 코드 수정과 PR 보조를 줄여줍니다.</span>' in html
    assert '<span class="point-question"><span class="point-number">7.</span> 출처와 상태:</span>' in html
    assert ".detail-points .point-question" in html
    assert "display: block;" in html
    assert "class=\"detail-criteria\"" not in html
    assert "data-insight-criteria" not in html


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
    assert "grid-template-columns: minmax(180px, 280px)" not in html
    assert "margin: 8px 0 0;" in html
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
    assert "<h3>getdesign.md</h3>" in html
    assert "<h3>Stitch</h3>" in html
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
    assert "서드파티 코딩 에이전트 보안 검증" in week_2
    assert "서드파티 코딩 에이전트를 개발 환경에 연결할 때 신원과 권한을 검증하는 보안 업데이트" in week_2
    assert "외부 에이전트가 저장소, 코드 변경, 비밀값에 접근하는 범위" in week_2
    assert "공개된 개발 도구와 코딩 자동화 관련 소식" not in week_2
    assert "새 기능이나 변경 사항이 업무 흐름" not in week_2
    assert "이번 업데이트가 실제 업무 흐름" not in week_2
    assert "해당 주간 수집 데이터에서 날짜, 출처, 업무 적용 가능성을 기준" in week_2
    assert "Previous Week" in week_2
    assert 'href="ai-sources/"' in week_2
    assert "전주로" not in week_2
    assert "1. 한 줄 요약:" in week_2
    assert "2. 무엇이 바뀌었나:" in week_2
    assert "3. 왜 중요한가:" in week_2
    assert "4. 한계와 주의사항:" in week_2
    assert "5. 이번 주 해볼 일:" in week_2
    assert "6. 누가 보면 좋은가:" in week_2
    assert "7. 출처와 상태:" in week_2
    assert '<span class="point-question"><span class="point-number">1.</span> 한 줄 요약:</span>' in week_2
    assert '<span class="point-answer">서드파티 코딩 에이전트를 개발 환경에 연결할 때' in week_2
    assert ".detail-points .point-question" in week_2
    assert "data-insight-criteria" not in week_2
    assert "criteria.textContent" not in week_2
    assert "원문 제목과 요약을 기준으로 선별된 항목입니다." not in week_2
    assert "출처 링크에서 세부 변경 사항과 적용 조건을 확인하세요." not in week_2
    assert "�" not in week_1
    assert "�" not in week_2
    assert '<a class="brand" href="./">AI MASTER TIMES</a>' in week_2
    assert "button.insertAdjacentElement('afterend', detailPanel)" in week_2
    assert "detailPanel.hidden = false;" in week_2
    assert ".insight-grid.has-selection .insight-detail { display: flex; }" in week_2
    assert 'class="detail-summary"' not in week_2
    assert "data-insight-body" not in week_2
    assert "smartInsightLinks.forEach" in week_2
    assert "data-insight-footnotes-title" in week_2
    assert "단어 설명" in week_2
    assert "const clearInsightSelection" in week_2
    assert 'insightGrid.classList.remove("has-selection")' in week_2
    assert "insightDetail.hidden = true" not in week_2
    assert "clearInsightSelection();" in week_2
    assert "selectFirstVisibleCard();" in week_2
    assert "window.sessionStorage.setItem(\"aimstletter.archiveInsightsOnly\", \"1\")" in week_2
    assert "2026-06-03~2026-06-09 데이터" in week_2
    assert "grid-template-columns: 1fr" in week_2
    assert "justify-self: end" in week_2
    assert "max-width: 100%" in week_2
    assert "max-height: calc(100vh - 48px)" in week_2
    assert "overflow-y: auto" in week_2
    assert "justify-content: flex-start" in week_2
    assert "font-size: 19px" in week_2
    assert "font-weight: 500" in week_2
    assert "font-weight: 700" in week_2
    assert "data-archive-index=" in week_2
    assert "link.dataset.archiveIndex" in week_2
    assert "Knowledge" in week_2
    assert "archive-month-group" in week_2
    assert "archive-month-summary" in week_2
    assert week_2.count("archive-month-summary") >= 2
    assert 'href="knowledge/langchain/"' in week_2
    assert 'href="knowledge/harness-engineering/"' in week_2
    assert "01.LangChain" in week_2
    assert "02.LangGraph" in week_2
    assert "03.프롬프트엔지니어링" in week_2
    assert "04.컨텍스트엔지니어링" in week_2
    assert "05.하네스 엔지니어링" in week_2
    assert week_2.index("Archive") < week_2.index("Knowledge")
    assert "1.1 프롬프트" not in week_2
    assert "overscroll-behavior: contain" in week_2
    assert "background: #e4efff" in week_2
    assert "color: #2462a8" in week_2
    assert ".topic-badge.paper" in week_2
    assert "background: #dff5e7" in week_2
    assert ".topic-badge.trend" in week_2
    assert "background: #ffe8e8" in week_2
    paper = "\ub17c\ubb38"
    tool = "\ub3c4\uad6c"
    trend = "\ub3d9\ud5a5"
    source_label = "\uc6d0\ubb38 \ubcf4\uae30"
    assert f'class="topic-badge paper">{paper}</span>' in week_2
    assert f'class="topic-badge">{tool}</span>' in week_2
    assert '<a class="detail-source" data-insight-source' in week_2
    assert f">{source_label}</a>" in week_2
    assert "원문 보기" in week_2
    assert "margin: 14px 0 22px" in week_2
    assert "width: 100%" in week_2
    assert "box-sizing: border-box" in week_2


def test_repair_archive_card_interaction_script_removes_stale_body_dependency() -> None:
    legacy = """
    const body = document.querySelector('[data-insight-body]');
    if (!buttons.length || !body || !detail || !grid) return;
    grid.classList.add('has-selection');
    body.textContent = button.dataset.body || '';
    if (insightDetail) insightDetail.hidden = true;
    """

    repaired = _repair_archive_card_interaction_script(legacy)

    assert "data-insight-body" not in repaired
    assert "!body" not in repaired
    assert "body.textContent" not in repaired
    assert "detailPanel.hidden = false;" in repaired
    assert "insightDetail.hidden = true" not in repaired


def test_committed_knowledge_page_exists() -> None:
    main = Path("public/knowledge/index.html").read_text(encoding="utf-8")
    html = Path("public/knowledge/harness-engineering/index.html").read_text(encoding="utf-8")
    langchain = Path("public/knowledge/langchain/index.html").read_text(encoding="utf-8")
    langgraph = Path("public/knowledge/langgraph/index.html").read_text(encoding="utf-8")
    loop = Path("public/knowledge/loop-engineering/index.html").read_text(encoding="utf-8")
    graph = Path("public/knowledge/graph-engineering/index.html").read_text(encoding="utf-8")

    assert "AI 엔지니어링 Knowledge" in main
    assert "개념 간 전체 비교표" in main
    assert "헷갈리기 쉬운 개념" in main
    assert 'href="langchain/"' in main
    assert "Knowledge" in html
    assert "Archive" in html
    assert "05. 하네스 엔지니어링" in html
    assert html.index("Archive") < html.index("Knowledge")
    assert 'href="../../archive/2026/06/week-2/"' in html
    assert 'href="../../knowledge/langchain/"' in html
    assert 'href="../../knowledge/harness-engineering/"' in html
    assert 'class="knowledge-link is-current"' in html
    assert "knowledge-article" in html
    assert "knowledge-toc" not in html
    assert "1.1 프롬프트" not in html
    assert "2.1 하네스 엔지니어링이란?" not in html
    assert "고객 문의 자동 분류" not in html
    assert "권한" in html
    assert "검증" in html
    assert "Tool Registry" in html
    assert "Audit Log" in html
    assert "검증 필요" in html
    assert "한 줄 정의" in html
    assert "주의" in html
    assert "확인 날짜: 2026-08-06" in html
    assert 'target="_blank"' in html
    assert "code-details" in html
    assert "01. LangChain" in langchain
    assert "회의록 자동 등록" in langchain
    assert "Prompt Template" in langchain
    assert "장애 원인 분석" in langgraph
    assert "테스트 실패 자동 수정" in loop
    assert "결제 API 변경 영향 분석" in graph
    assert "LangGraph와 그래프 엔지니어링의 차이" in graph


def test_knowledge_page_includes_practical_engineering_playbook() -> None:
    topic = next(topic for topic in KNOWLEDGE_TOPICS if topic.slug == "langgraph")
    html = _render_knowledge_topic_page(topic, analytics_html="", back_href="../../")

    assert "한 줄 정의" in html
    assert "한눈에 보는 구조" in html
    assert "장애 원인 분석" in html
    assert "헷갈리는 개념과 차이" in html
    assert "30초 요약" not in html
    assert "왜 필요한가" in html
    assert "언제 쓰는가" in html
    assert "실제 업무 사례" in html
    assert "최소 구현 예제" in html
    assert "비슷한 개념과 비교" in html
    assert "주의할 점" in html
    assert "운영 체크리스트" in html
    assert "역할별 업무 적용" in html
    assert "더 알아보기" in html
    assert "AI 엔지니어링 관계도" in html
    assert "개념 간 전체 비교표" in html
    assert "헷갈리기 쉬운 개념" in html
    assert "State" in html
    assert "Checkpoint" in html
    assert "Interrupt" in html
    assert "Resume" in html
    assert "Human-in-the-loop" in html
    assert "기획자" in html
    assert "백엔드" in html
    assert "최종 검토 날짜: 2026-08-06" in html
    assert "한 줄 정의" in html
    assert "code-details" in html


def test_all_knowledge_pages_start_with_metadata_first_screen() -> None:
    for topic in KNOWLEDGE_TOPICS:
        html = _render_knowledge_topic_page(topic, analytics_html="", back_href="../../")
        assert '<section class="knowledge-focus"' in html
        assert "한 줄 정의" in html
        assert "한눈에 보는 구조" in html
        assert "실제 업무 사례" in html
        assert "헷갈리는 개념과 차이" in html
        assert "핵심 구성요소" in html
        assert html.index("knowledge-focus") < html.index("definition-box")
        assert html.index("knowledge-focus") < html.index("더 알아보기: AI 엔지니어링 관계도")


def test_knowledge_metadata_schema_is_complete_and_unique() -> None:
    assert validate_knowledge_pages() == ()
    known_slugs = set(KNOWLEDGE_PAGES)

    for topic in KNOWLEDGE_TOPICS:
        page = KNOWLEDGE_PAGES[topic.slug]
        for field in REQUIRED_KNOWLEDGE_METADATA:
            assert page.get(field), f"{topic.slug} missing {field}"
        assert page["id"] == topic.order
        assert 3 <= len(page["coreComponents"]) <= 5
        assert page["officialSources"]
        assert page["confusingConcepts"]
        assert set(page["relatedConcepts"]).issubset(known_slugs)
        assert {"title", "situation", "oldProblem", "process", "result", "limit"}.issubset(
            page["representativeUseCase"]
        )


def test_knowledge_layout_keeps_sidebar_toggles_and_compare_table_aligned() -> None:
    topic = next(topic for topic in KNOWLEDGE_TOPICS if topic.slug == "prompt-engineering")
    html = _render_knowledge_topic_page(topic, analytics_html="", back_href="../../")

    sidebar_rule = re.search(
        r"\.archive-year,\s*\.archive-month-summary\s*\{(?P<body>.*?)\}",
        html,
        flags=re.S,
    )
    assert sidebar_rule
    assert "box-sizing: border-box;" in sidebar_rule.group("body")
    assert "justify-content: flex-start;" in sidebar_rule.group("body")
    assert "justify-content: space-between;" not in sidebar_rule.group("body")

    compare_section = html.split("<h2>비슷한 개념과 비교</h2>", 1)[1]
    compare_table = compare_section.split("</table>", 1)[0]
    assert "<th>개념</th>" in compare_table
    assert compare_table.count("<th>") == 7

    for row in re.findall(r"<tr>(.*?)</tr>", compare_table, flags=re.S)[1:]:
        assert row.count("<td>") == compare_table.count("<th>")


def test_dedupe_insight_buttons_removes_repeated_source_urls() -> None:
    html = (
        '<button class="insight-card" data-title="A" data-source="https://example.com/a">A</button>'
        '<button class="insight-card" data-title="B" data-source="https://example.com/b">B</button>'
        '<button class="insight-card" data-title="A2" data-source="https://example.com/a">A2</button>'
    )

    refreshed, count = _dedupe_insight_buttons_in_html(html)

    assert count == 1
    assert 'data-title="A"' in refreshed
    assert 'data-title="B"' in refreshed
    assert 'data-title="A2"' not in refreshed


def test_dedupe_insight_buttons_removes_repeated_visible_content() -> None:
    html = (
        '<button class="insight-card" data-title="동일한 업데이트" data-body="같은 핵심 내용입니다." '
        'data-source="https://example.com/a">A</button>'
        '<button class="insight-card" data-title="동일한 업데이트" data-body="같은 핵심 내용입니다." '
        'data-source="https://example.com/b">B</button>'
        '<button class="insight-card" data-title="다른 업데이트" data-body="다른 핵심 내용입니다." '
        'data-source="https://example.com/c">C</button>'
    )

    refreshed, count = _dedupe_insight_buttons_in_html(html)

    assert count == 1
    assert 'data-source="https://example.com/a"' in refreshed
    assert 'data-source="https://example.com/b"' not in refreshed
    assert 'data-source="https://example.com/c"' in refreshed


def test_committed_archive_cards_have_unique_visible_content() -> None:
    paths = [Path("public/index.html"), *Path("public/archive").glob("**/index.html")]

    for path in paths:
        html = path.read_text(encoding="utf-8")
        cards = re.findall(r'<button class="insight-card"[^>]*>', html)
        visible_content = [
            (
                re.search(r'data-title="([^"]*)"', card).group(1),
                re.search(r'data-body="([^"]*)"', card).group(1),
            )
            for card in cards
        ]
        assert len(visible_content) == len(set(visible_content)), path


def test_committed_weekly_smart_insights_use_week_specific_items() -> None:
    index = Path("public/index.html").read_text(encoding="utf-8")
    week_3 = Path("public/archive/2026/06/week-3/index.html").read_text(encoding="utf-8")
    week_2 = Path("public/archive/2026/06/week-2/index.html").read_text(encoding="utf-8")
    week_1 = Path("public/archive/2026/06/week-1/index.html").read_text(encoding="utf-8")
    may_4 = Path("public/archive/2026/05/week-4/index.html").read_text(encoding="utf-8")

    week_3_titles = re.findall(r'data-title="([^"]*)"', week_3)
    week_2_titles = re.findall(r'data-title="([^"]*)"', week_2)
    week_1_titles = re.findall(r'data-title="([^"]*)"', week_1)
    may_4_titles = re.findall(r'data-title="([^"]*)"', may_4)

    assert week_3_titles
    assert week_2_titles
    assert week_1_titles
    assert may_4_titles
    assert "06월 3째주" in index
    assert "06월 3째주" in week_3
    assert "2026-06-08~2026-06-15 데이터" in week_3
    assert 'href="archive/2026/06/week-3/"' in index
    assert 'href="archive/2026/06/week-3/"' in week_3
    assert '<base href="../../../../">' not in index
    assert '<base href="../../../../">' in week_3
    assert week_2_titles != week_1_titles
    assert week_3_titles != week_2_titles
    assert may_4_titles != week_1_titles
    assert may_4_titles != week_2_titles
    assert may_4_titles != week_3_titles
    assert len(week_3_titles) == len(set(week_3_titles))
    assert len(week_1_titles) == len(set(week_1_titles))
    assert len(may_4_titles) == len(set(may_4_titles))
    assert any("서드파티 코딩 에이전트 보안 검증" in title for title in week_2_titles)
    assert any("스프레드시트 업무 자동화" in title for title in week_1_titles)
    assert "2026-05-20~2026-05-26" in may_4
    assert not any("프롬프트를 업무 워크플로로 전환" in title for title in may_4_titles)
    assert "Harness Engineering" not in week_2_titles
    assert "Harness Engineering" not in week_1_titles
    assert "Harness Engineering" not in may_4_titles


def test_weekly_pages_workflow_runs_monday_7am_kst() -> None:
    workflow = Path(".github/workflows/weekly-pages.yml").read_text(encoding="utf-8")

    assert "07:00 every Monday in Asia/Seoul" in workflow
    assert 'cron: "0 22 * * 0"' in workflow
