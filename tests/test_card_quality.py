from __future__ import annotations

import html
import json
from datetime import UTC, datetime

import pytest
import requests

from aimstletter.fetchers import DigestItem
from aimstletter.config import Settings
from aimstletter.site import (
    SiteItem,
    build_site,
    _clean_unpublishable_archive_indexes,
    _clean_unpublishable_intro_copy,
    _filter_publishable_source_items,
    _localized_site_item,
    _load_latest_verified_korean_archive,
    _load_verified_korean_archive_items,
    _load_week_source_items,
    _localize_items,
    _normalize_search_text,
    _paper_focused_summary,
    _recover_web_source_item,
    _remove_unpublishable_cards_in_html,
    _replace_html_attr,
    _render_smart_insight_cards,
    _refresh_homepage_archive_navigation,
    _refresh_known_specific_cards_in_html,
    _renumber_insight_buttons_in_html,
    _refresh_paper_cards_in_html,
    _source_match_confidence,
    _weekly_archive_entry,
    _write_week_source_items,
)


def test_html_attribute_replacement_treats_source_backslashes_as_literal_text() -> None:
    updated = _replace_html_attr(
        '<button data-body="old"></button>',
        "data-body",
        r"The source uses the pattern \s+ without changing its meaning.",
    )

    assert r"pattern \s+" in updated


def test_refresh_cleans_unpublishable_archive_search_index() -> None:
    html_text = (
        '<a data-archive-link data-archive-index="08월 5째주 '
        '수집된 본문 요약이 부족해 제목과 출처 범위에서만 다룹니다" '
        'href="archive/2026/08/week-5/">08월 5째주</a>'
    )

    refreshed, count = _clean_unpublishable_archive_indexes(html_text)

    assert count == 1
    assert "수집된 본문 요약이 부족" not in refreshed
    assert "제목과 출처 범위에서만" not in refreshed
    assert "08월 5째주" in refreshed
    assert "archive/2026/08/week-5/" in refreshed


def test_refresh_cleans_unpublishable_intro_copy() -> None:
    html_text = (
        '<p class="intro-copy">이번 주 대표 신호: '
        '수집된 본문 요약이 부족해 제목과 출처 범위에서만 다룹니다.</p>'
    )

    refreshed, count = _clean_unpublishable_intro_copy(html_text)

    assert count == 1
    assert "수집된 본문 요약이 부족" not in refreshed
    assert "원문 근거가 확인된 항목 중심" in refreshed


def test_render_smart_insights_skips_unpublishable_fallback_item() -> None:
    item = SiteItem(
        title="Traccia",
        url="https://example.com/traccia",
        source="Product Hunt launches",
        kind="도구 업데이트",
        published=datetime(2026, 8, 24, tzinfo=UTC),
        summary="수집된 본문 요약이 부족해 Traccia의 세부 기능은 Product Hunt launches의 제목과 출처 범위에서만 다룹니다.",
        detail="원문 본문을 재수집해 확인하기 전까지 기능, 성능, 적용 효과를 추정하지 않습니다.",
        key_points=(
            "1. 한 줄 요약: Traccia와 관련된 변화가 업무 흐름에 미치는 영향을 정리한 항목입니다.",
            "2. 무엇이 바뀌었나: 수집된 본문 요약이 부족해 제목과 출처 범위에서만 다룹니다.",
        ),
        tags=("AI 에이전트",),
    )

    assert _render_smart_insight_cards([item]) == ""


def test_removed_cards_are_renumbered_without_gaps() -> None:
    html_text = (
        '<button class="insight-card" data-number="8"><span class="card-icon">8</span></button>'
        '<button class="insight-card" data-number="12"><span class="card-icon">12</span></button>'
    )

    refreshed, count = _renumber_insight_buttons_in_html(html_text)

    assert count == 2
    assert 'data-number="1"' in refreshed
    assert 'data-number="2"' in refreshed
    assert '<span class="card-icon">1</span>' in refreshed
    assert '<span class="card-icon">2</span>' in refreshed


def test_paper_cards_prioritize_quantitative_abstract_results() -> None:
    item = DigestItem(
        title="Thinkingbox: Stateful Business Workflow Reliability Benchmark",
        url="https://arxiv.org/abs/2608.19741v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 20, tzinfo=UTC),
        summary=(
            "Existing agent benchmarks often reward one successful completion. "
            "Thinkingbox evaluates 507 policy-conditioned business workflows with executable final-state checks. "
            "The best model reaches 65.36% single-attempt success, but only 25.25% reliability over 20 repeated runs."
        ),
    )
    localized_item = {
        "title": "Thinkingbox",
        "summary": "Generic benchmark summary.",
        "detail": "Generic benchmark summary.",
        "key_points": [
            "1. Summary: Generic benchmark summary.",
            "2. Change: Generic benchmark.",
            "3. Importance: Reliability matters.",
            "4. Caution: Paper-stage result.",
            "5. Action: Try a small evaluation.",
            "6. Audience: AI engineers",
            "7. Source: arXiv paper, 2026-08-20",
        ],
        "tags": ["AI agent"],
    }

    site_item = _localized_site_item(item, localized_item)
    card_text = f"{site_item.summary} {' '.join(site_item.key_points)}"

    assert "65.36%" in card_text
    assert "25.25%" in card_text
    assert "single-attempt" in card_text or "single attempt" in card_text
    assert "20" in card_text


def test_paper_focused_summary_rewrites_english_evidence_to_korean() -> None:
    item = DigestItem(
        title="Ensi RAG Entity Retrieval Generation",
        url="https://arxiv.org/abs/2608.21111v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 22, tzinfo=UTC),
        summary=(
            "Each record (e, t, k, v) represents an entity e, its type t, a semantic category k in "
            "{property, relation, aspect}, and a value v, while retaining links to the original source passages. "
            "Across Loong and Oolong, EnSI-RAG achieves an average accuracy of 78.24."
        ),
    )

    summary = _paper_focused_summary(item)

    assert "평균 정확도 78.24" in summary
    assert "Each record" not in summary
    assert "Across Loong and Oolong" not in summary
    assert "an entity" not in summary


def test_bolo_metrics_are_labeled_instead_of_forced_numeric_fallback() -> None:
    item = DigestItem(
        title="Bolo: Verified Model Hub for Next-Generation AI Databases",
        url="https://arxiv.org/abs/2608.20525v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 21, tzinfo=UTC),
        summary=(
            "While they host millions of model repositories, many contain only raw weights without runnable pipelines. "
            "In preliminary experiments, Bolo achieves 97.27\\% and 86.08\\% runnable coverage for "
            "Type~II and Type~III models, respectively, demonstrating that agentic synthesis with targeted "
            "verification can make model repositories directly usable."
        ),
    )

    site_item = _localized_site_item(
        item,
        {
            "title": "Bolo Verified 모델 생성 AI",
            "summary": "Generic paper summary.",
            "detail": "Generic paper summary.",
            "key_points": [],
            "tags": ["paper"],
        },
    )
    card_text = f"{site_item.summary} {' '.join(site_item.key_points)}"

    assert "Type-II" in card_text
    assert "Type-III" in card_text
    assert "커버리지 97.27%" in card_text
    assert "86.08%" in card_text
    assert "97.27, 86.08 같은 핵심 수치" not in card_text
    assert "같은 핵심 수치" not in card_text


def test_dagsmith_metrics_are_labeled_instead_of_forced_numeric_fallback() -> None:
    item = DigestItem(
        title="Dagsmith Dependency Aware Query Rewriting",
        url="https://arxiv.org/abs/2608.22551v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 24, tzinfo=UTC),
        summary=(
            "On the open-source Tuva dbt project, DAGSmith reduces elapsed time by 42.6% and "
            "warehouse compute cost by 67.7%, substantially outperforming single-query rewriting."
        ),
    )

    site_item = _localized_site_item(
        item,
        {
            "title": "Dagsmith Dependency Aware",
            "summary": "Generic paper summary.",
            "detail": "Generic paper summary.",
            "key_points": [],
            "tags": ["paper"],
        },
    )
    card_text = f"{site_item.summary} {' '.join(site_item.key_points)}"

    assert "실행 시간을 42.6%" in card_text
    assert "비용을 67.7%" in card_text
    assert "파이프라인 전체 의존성" in card_text
    assert "42.6%, 67.7% 같은 핵심 수치" not in card_text
    assert "같은 핵심 수치" not in card_text


def test_existing_paper_summary_with_evidence_leak_is_regenerated() -> None:
    item = DigestItem(
        title="Agentic Data Cleaning",
        url="https://arxiv.org/abs/2608.19999v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 14, tzinfo=UTC),
        summary=(
            "Seven configurations are evaluated across financial, clinical, and environmental-monitoring "
            "datasets using controlled synthetic corruption and original-data descriptive analysis, resulting "
            "in 126 completed runs."
        ),
    )
    leaked = (
        "\uadfc\uac70 \ubb38\uc7a5: seven configurations are evaluated across financial, clinical, and "
        "environmental-monitoring datasets, resulting in 126 completed runs."
    )

    site_item = _localized_site_item(
        item,
        {
            "title": "Agentic Data Cleaning",
            "summary": leaked,
            "detail": leaked,
            "key_points": [
                "1. \ud55c \uc904 \uc694\uc57d: " + leaked,
                "2. \ubb34\uc5c7\uc774 \ubc14\ub00c\uc5c8\ub098: " + leaked,
                "3. \uc65c \uc911\uc694\ud55c\uac00: " + leaked,
                "4. \ud55c\uacc4\uc640 \uc8fc\uc758\uc0ac\ud56d: paper-stage result.",
                "5. \uc774\ubc88 \uc8fc \ud574\ubcfc \uc77c: try a small evaluation.",
                "6. \ub204\uac00 \ubcf4\uba74 \uc88b\uc740\uac00: AI engineers",
                "7. \ucd9c\ucc98\uc640 \uc0c1\ud0dc: arXiv paper",
            ],
            "tags": ["AI agent"],
        },
    )

    card_text = f"{site_item.summary} {site_item.detail} {' '.join(site_item.key_points)}"

    assert "\uadfc\uac70 \ubb38\uc7a5:" not in card_text
    assert "126" in card_text


def test_existing_recursive_paper_summary_is_regenerated() -> None:
    item = DigestItem(
        title="Ensi RAG Entity Retrieval Generation",
        url="https://arxiv.org/abs/2608.21111v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 22, tzinfo=UTC),
        summary="Across Loong and Oolong, EnSI-RAG achieves an average accuracy of 78.24.",
    )
    recursive = (
        "\ucd08\ub85d\uc5d0\uc11c \ud655\uc778\ub418\ub294 \uacb0\uacfc\uc640 \ud3c9\uac00 \uae30\uc900\uc744 "
        "\uc911\uc2ec\uc73c\ub85c \ubd10\uc57c \ud569\ub2c8\ub2e4. "
        "\uae30\uc874 \uc811\uadfc\uacfc\uc758 \ucc28\uc774\ub294 \u201cEnsi RAG Entity "
        "\ucd08\ub85d\uc5d0\uc11c \ud655\uc778\ub418\ub294 \uacb0\uacfc\uc640 \ud3c9\uac00 "
        "\uae30\uc900\uc744 \uc911\uc2ec\uc73c\ub85c \ubd10\uc57c \ud569\ub2c8\ub2e4\u201d"
    )

    site_item = _localized_site_item(
        item,
        {
            "title": "Ensi RAG Entity",
            "summary": recursive,
            "detail": recursive,
            "key_points": [
                "1. \ud55c \uc904 \uc694\uc57d: " + recursive,
                "2. \ubb34\uc5c7\uc774 \ubc14\ub00c\uc5c8\ub098: " + recursive,
                "3. \uc65c \uc911\uc694\ud55c\uac00: " + recursive,
                "4. \ud55c\uacc4\uc640 \uc8fc\uc758\uc0ac\ud56d: paper-stage result.",
                "5. \uc774\ubc88 \uc8fc \ud574\ubcfc \uc77c: try a small evaluation.",
                "6. \ub204\uac00 \ubcf4\uba74 \uc88b\uc740\uac00: AI engineers",
                "7. \ucd9c\ucc98\uc640 \uc0c1\ud0dc: arXiv paper",
            ],
            "tags": ["AI agent"],
        },
    )

    card_text = f"{site_item.summary} {site_item.detail} {' '.join(site_item.key_points)}"

    assert "\uae30\uc874 \uc811\uadfc\uacfc\uc758 \ucc28\uc774\ub294 \u201c" not in card_text
    assert "\ud3c9\uade0 \uc815\ud655\ub3c4 78.24" in card_text


def test_archive_search_text_strips_generated_evidence_leaks() -> None:
    value = (
        "Agentic Data Cleaning "
        "\uadfc\uac70 \ubb38\uc7a5: seven configurations are evaluated across datasets, resulting in 126 runs. "
        "arxiv database ai"
    )

    search_text = _normalize_search_text(value)

    assert "\uadfc\uac70 \ubb38\uc7a5:" not in search_text
    assert "seven configurations" not in search_text
    assert "agentic data cleaning" in search_text


def test_smart_insight_card_keeps_long_detail_without_700_char_truncation() -> None:
    long_detail = "요약 본문입니다. " + ("자세한 근거를 확인할 수 있습니다. " * 45)
    item = _localized_site_item(
        DigestItem(
            title="Long Detail Tool",
            url="https://example.com/long-detail-tool",
            source="Example",
            kind="tool",
            published=datetime(2026, 8, 24, tzinfo=UTC),
            summary=long_detail,
        ),
        {
            "title": "Long Detail Tool",
            "summary": long_detail,
            "detail": long_detail,
            "key_points": [
                "1. 한 줄 요약: " + long_detail,
                "2. 무엇이 바뀌었나: " + long_detail,
                "3. 왜 중요한가: " + long_detail,
                "4. 한계와 주의사항: " + long_detail,
                "5. 이번 주 해볼 일: " + long_detail,
                "6. 누가 보면 좋은가: AI 엔지니어",
                "7. 출처와 상태: Example · 자료 · 2026-08-24",
            ],
            "tags": ["tool"],
        },
    )

    html_text = _render_smart_insight_cards([item])

    assert 'data-detail="' in html_text
    assert "..." not in html_text.split('data-detail="', 1)[1].split('"', 1)[0]


def test_smart_insight_card_does_not_clip_long_summary_or_detail() -> None:
    summary_tail = "요약의 마지막 문장도 빠짐없이 표시됩니다."
    detail_tail = "상세 설명의 마지막 근거도 빠짐없이 표시됩니다."
    summary = ("한국어 한 줄 설명을 충분히 제공합니다. " * 30) + summary_tail
    detail = ("원문에서 확인한 상세 근거를 순서대로 설명합니다. " * 60) + detail_tail
    item = SiteItem(
        title="긴 설명 표시 확인",
        url="https://example.com/full-copy",
        source="Example",
        kind="도구",
        published=datetime(2026, 8, 24, tzinfo=UTC),
        summary=summary,
        detail=detail,
        key_points=tuple(f"{index}. 확인 항목: 전체 내용을 표시합니다." for index in range(1, 8)),
        tags=("표시 검증",),
    )

    html_text = _render_smart_insight_cards([item])

    assert summary_tail in html_text
    assert detail_tail in html_text


def test_source_fallback_never_exposes_untranslated_or_clipped_copy() -> None:
    english = "An English-only explanation that must not leak into a Korean card. " * 12
    item = DigestItem(
        title="Unknown workflow update",
        url="https://example.com/unknown-workflow-update",
        source="Example",
        kind="tool",
        published=datetime(2026, 8, 24, tzinfo=UTC),
        summary=english,
    )

    localized = _localize_items([item], Settings(openai_api_key=""), "test")[0]
    rendered_copy = " ".join((localized.summary, localized.detail, *localized.key_points))

    assert english.strip() not in rendered_copy
    assert "..." not in rendered_copy
    assert "…" not in rendered_copy
    assert any("가" <= char <= "힣" for char in rendered_copy)


def test_quantitative_paper_logic_does_not_rewrite_tool_cards() -> None:
    item = DigestItem(
        title="Tool usage grows",
        url="https://example.com/tool",
        source="Example",
        kind="tool",
        published=datetime(2026, 8, 20, tzinfo=UTC),
        summary="The tool reached 65.36% adoption after a release.",
    )
    localized_item = {
        "title": "Tool usage grows",
        "summary": "Tool adoption changed after release.",
        "detail": "Tool adoption changed after release.",
        "key_points": [
            "1. Summary: Tool adoption changed.",
            "2. Change: Release applied.",
            "3. Importance: Operations can track adoption.",
            "4. Caution: Check support scope.",
            "5. Action: Try the setting.",
            "6. Audience: AI engineers",
            "7. Source: Example",
        ],
        "tags": ["tool"],
    }

    site_item = _localized_site_item(item, localized_item)

    assert "65.36%" not in " ".join(site_item.key_points)


def test_agnost_tool_card_uses_source_specific_summary_not_generic_template() -> None:
    item = DigestItem(
        title="Agnost AI",
        url="https://www.producthunt.com/products/agnost-ai",
        source="Product Hunt Launches",
        kind="tool",
        published=datetime(2026, 8, 23, tzinfo=UTC),
        summary="Agnost AI",
    )
    site_item = _localized_site_item(item, {})
    card_text = f"{site_item.summary} {' '.join(site_item.key_points)}"

    assert "silent failure" in card_text
    assert "eval" in card_text
    assert "related changes" not in card_text


def test_missing_body_fallback_does_not_pose_as_source_summary() -> None:
    item = DigestItem(
        title="Unknown Launch",
        url="https://example.com/unknown",
        source="Example",
        kind="tool",
        published=datetime(2026, 8, 23, tzinfo=UTC),
        summary="Unknown Launch",
    )
    site_item = _localized_site_item(item, {})
    card_text = f"{site_item.summary} {' '.join(site_item.key_points)}"

    assert "related changes" not in card_text
    assert "자동 실행 범위" not in card_text
    assert "승인 지점" not in card_text


def test_build_filters_items_without_source_backed_summary_after_retry() -> None:
    weak = DigestItem(
        title="Upcoming Changes GitHub Copilot",
        url="https://github.blog/changelog/2026-08-28-upcoming-changes-github-copilot",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="Upcoming Changes GitHub Copilot",
    )
    strong = DigestItem(
        title="Copilot code review effort levels",
        url="https://github.blog/changelog/2026-08-07-copilot-code-review-effort-levels-are-generally-available",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 7, tzinfo=UTC),
        summary="GitHub Copilot code review effort levels are generally available for repository reviews.",
    )

    filtered = _filter_publishable_source_items([weak, strong], "test items")

    assert filtered == [strong]


def test_localize_items_without_openai_publishes_korean_source_summary() -> None:
    item = DigestItem(
        title="Copilot code review Resolution",
        url="https://github.blog/changelog/2026-08-28-copilot-code-review-resolution",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="GitHub Copilot code review adds a resolution workflow for review comments.",
    )

    localized = _localize_items([item], Settings(openai_api_key=""), "test")

    assert len(localized) == 1
    assert localized[0].url == item.url
    assert "검토 의견을 해결 상태로 표시" in localized[0].summary
    assert "resolution workflow for review comments" not in localized[0].summary.lower()
    assert len(localized[0].key_points) == 7


def test_localize_items_without_openai_uses_specific_source_grounded_korean_summary() -> None:
    item = DigestItem(
        title="Credo: Reusable Declarative Primitives for Agentic Workflows",
        url="https://arxiv.org/abs/2608.27790v1",
        source="arXiv Database AI",
        kind="paper",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary=(
            "Credo recovers a structured declarative description of a searched harness, "
            "catalogues reusable primitives with provenance, and compiles them for new tasks."
        ),
    )

    localized = _localize_items([item], Settings(openai_api_key=""), "test")

    assert len(localized) == 1
    assert "선언형 실행 단계를 추출" in localized[0].summary
    assert "작업마다 다시 탐색하지 않고" in localized[0].key_points[2]
    assert "원문 제목과 링크를 보존" not in localized[0].summary


@pytest.mark.parametrize(
    ("title", "url", "summary", "expected_title"),
    (
        ("Credo: Reusable Declarative Primitives for Agentic Workflows", "https://arxiv.org/abs/2608.27790v1", "Reusable declarative agent workflow primitives.", "Credo: 재사용 가능한 선언형 에이전트 워크플로"),
        ("Enterprise AI's real risk isn't autonomous agents. It's the complexity between them.", "https://venturebeat.com/ai/enterprise-ais-real-risk-isnt-autonomous-agents-its-the-complexity-between-them", "Enterprise agents create complexity between systems.", "기업 AI의 진짜 위험: 에이전트 간 복잡성"),
        ("FaulT-Bench", "https://arxiv.org/abs/2608.27021v1", "A benchmark for fault diagnosis agents.", "FaulT-Bench: 네트워크 장애 진단 에이전트 평가"),
        ("When agents act on their own, governance has to live in the data layer", "https://venturebeat.com/security/when-agents-act-on-their-own-governance-has-to-live-in-the-data-layer", "Data-layer governance for autonomous agents.", "자율 에이전트 거버넌스를 데이터 계층에 두는 이유"),
        ("Orchestration is the new challenge for CX in the age of AI agents", "https://venturebeat.com/orchestration/orchestration-is-the-new-challenge-for-cx-in-the-age-of-ai-agents", "Customer experience orchestration across AI agents.", "AI 고객 경험의 새 과제: 에이전트 오케스트레이션"),
        ("Reachability-Based Capability Control", "https://arxiv.org/abs/2608.30041v1", "Restricting agent capability after untrusted tool output.", "SkillGuard: 오염 상태 기반 에이전트 권한 제한"),
        ("Diachronic Hypergraphs for Orchestrated Agents", "https://arxiv.org/abs/2608.29678v1", "A temporal hypergraph memory for agents.", "MAGE: 시간·근거를 보존하는 다중 에이전트 메모리"),
        ("Bridging Agent Semantics with Spot Capacity", "https://arxiv.org/abs/2608.29581v1", "Elastic and recoverable LLM serving.", "SemSpot: 중단 복구형 스팟 LLM 추론"),
        ("MedCache", "https://arxiv.org/abs/2608.29528v1", "Temporally valid memory for clinical agents.", "MedCache: 시간 유효성을 반영한 임상 에이전트 메모리"),
        ("Network Slice Allocation", "https://arxiv.org/abs/2608.29444v1", "Joint network and compute allocation.", "강화학습 기반 네트워크 슬라이스 공동 할당"),
        ("Superagent", "https://www.producthunt.com/products/superagent-a-home-for-your-ai-agents", "Claude Code for the rest of us.", "Superagent: 비개발자용 AI 에이전트 실행 도구"),
        ("oMLX", "https://www.producthunt.com/products/omlx", "Mac LLM server that cuts agent wait times from 90s to 5s.", "oMLX: Mac용 저지연 로컬 LLM 서버"),
        ("Orato", "https://www.producthunt.com/products/orato-speech-coach", "Practice speaking with AI.", "Orato: AI 말하기 연습 코치"),
        ("Maritime", "https://www.producthunt.com/products/maritime", "Dedicated computers for AI agents.", "Maritime: AI 에이전트용 전용 컴퓨터"),
        ("GitHub Copilot in Visual Studio — August update", "https://github.blog/changelog/visual-studio-august-update", "More control over Copilot models and specialized agents.", "Visual Studio용 GitHub Copilot 8월 업데이트"),
        ("GitHub Copilot weekly releases — August 24", "https://github.blog/changelog/copilot-weekly-releases-august-24", "Team sessions in Slack and Teams.", "GitHub Copilot 8월 24일 주간 업데이트"),
        ("Gauth AI Course", "https://www.producthunt.com/products/gauth-ai-course", "Watch, quiz through, and create AI courses.", "Gauth AI Course: 강의·퀴즈·제작 통합 학습 도구"),
        ("Upcoming changes to GitHub Copilot policies and billing", "https://github.blog/changelog/copilot-policies-and-billing", "Three upcoming policy and billing changes.", "GitHub Copilot 정책·과금 변경 예고"),
        ("Wzmacniamy w Polsce ochronę przed oszustwami", "https://about.fb.com/news/wzmacniamy-w-polsce-ochrone-przed-oszustwami", "Meta uses AI against scams in Poland.", "Meta의 폴란드 AI 사기 탐지 강화"),
        ("Our decision on Cursor following its acquisition by SpaceX", "https://openai.com/index/our-decision-on-cursor-following-its-acquisition-by-spacex", "OpenAI will wind down its Cursor model contract.", "Cursor 인수 이후 OpenAI 모델 공급 종료"),
    ),
)
def test_current_week_source_fallback_has_korean_content_title(
    title: str,
    url: str,
    summary: str,
    expected_title: str,
) -> None:
    item = DigestItem(
        title=title,
        url=url,
        source="source",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary=summary,
    )

    localized = _localize_items([item], Settings(openai_api_key=""), "test")

    assert localized[0].title == expected_title
    assert any("가" <= char <= "힣" for char in localized[0].summary)
    assert "원문 제목과 링크를 보존" not in localized[0].summary


def test_required_localization_preserves_source_content_without_credentials(monkeypatch) -> None:
    item = DigestItem(
        title="Copilot code review Resolution",
        url="https://example.com/copilot-code-review-resolution",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="GitHub Copilot adds a resolution workflow for review comments.",
    )
    monkeypatch.setenv("AIMSTLETTER_REQUIRE_OPENAI_LOCALIZATION", "1")

    localized = _localize_items(
        [item], Settings(openai_api_key="", azure_openai_api_key=""), "test"
    )

    assert len(localized) == 1
    assert localized[0].url == item.url
    assert "검토 의견을 해결 상태로 표시" in localized[0].detail


def test_weekly_archive_entry_uses_data_window_end_for_cross_month_retry() -> None:
    entry = _weekly_archive_entry(datetime(2026, 9, 1, tzinfo=UTC))

    assert entry["href"] == "archive/2026/08/week-5/"
    assert entry["period_start"] == "2026-08-24"
    assert entry["period_end"] == "2026-08-31"


def test_build_does_not_overwrite_homepage_when_no_verified_cards(monkeypatch, tmp_path) -> None:
    index_path = tmp_path / "index.html"
    index_path.write_text("previous verified homepage", encoding="utf-8")
    monkeypatch.setattr("aimstletter.site.fetch_recent_items", lambda *_args, **_kwargs: [])

    with pytest.raises(RuntimeError, match="no verified cards"):
        build_site(tmp_path, Settings(openai_api_key=""))

    assert index_path.read_text(encoding="utf-8") == "previous verified homepage"


def test_archive_fallback_skips_untranslated_week_and_selects_latest_korean_week(tmp_path) -> None:
    korean_item = SiteItem(
        title="GitHub Copilot 배포 승인",
        url="https://example.com/korean",
        source="GitHub Copilot 변경 이력",
        kind="도구 업데이트",
        published=datetime(2026, 8, 21, tzinfo=UTC),
        summary="GitHub Copilot이 배포 전에 지정 검토자의 승인을 받는 기능을 추가했습니다.",
        detail="배포 요청을 지정 검토자가 확인하고 승인한 뒤에만 실행하도록 흐름을 바꿉니다.",
        key_points=(
            "1. 한 줄 요약: 배포 전에 지정 검토자의 승인을 받습니다.",
            "2. 무엇이 바뀌었나: 자동 배포 흐름에 승인 단계를 추가했습니다.",
            "3. 왜 중요한가: 승인되지 않은 변경의 운영 반영을 막습니다.",
            "4. 한계와 주의사항: 저장소 권한과 검토자 구성을 확인해야 합니다.",
            "5. 이번 주 해볼 일: 시험 저장소에 승인 규칙을 설정합니다.",
            "6. 누가 보면 좋은가: 배포 담당자와 운영 담당자입니다.",
            "7. 출처와 상태: 공식 변경 이력에서 공개된 기능입니다.",
        ),
        tags=("GitHub Copilot", "배포 승인"),
    )
    english_item = SiteItem(
        title="Copilot deployment approvals",
        url="https://example.com/english",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="GitHub Copilot adds repository deployment approvals with named reviewers.",
        detail="Repository deployments require approval from a named reviewer before execution.",
        key_points=tuple(f"{index}. English source text only" for index in range(1, 8)),
        tags=("원문 스냅샷",),
    )
    week_four = tmp_path / "archive/2026/08/week-4/index.html"
    week_five = tmp_path / "archive/2026/08/week-5/index.html"
    week_four.parent.mkdir(parents=True)
    week_five.parent.mkdir(parents=True)
    week_four.write_text(_render_smart_insight_cards([korean_item]), encoding="utf-8")
    week_five.write_text(_render_smart_insight_cards([english_item]), encoding="utf-8")

    assert len(_load_verified_korean_archive_items(week_four)) == 1
    assert _load_verified_korean_archive_items(week_five) == []
    items, entry = _load_latest_verified_korean_archive(tmp_path)
    assert items[0].title == korean_item.title
    assert entry is not None
    assert entry["href"] == "archive/2026/08/week-4/"

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("aimstletter.site.fetch_recent_items", lambda *_args, **_kwargs: [])
    try:
        homepage = build_site(tmp_path, Settings(openai_api_key="")).read_text(encoding="utf-8")
    finally:
        monkeypatch.undo()
    assert korean_item.summary in homepage
    assert english_item.summary not in homepage
    # The unlocalized archive must not replace verified homepage content, but
    # its existing weekly page must remain reachable from archive navigation.
    assert "08월 5째주" in homepage


def test_required_build_rejects_a_stale_verified_archive(monkeypatch, tmp_path) -> None:
    item = SiteItem(
        title="GitHub Copilot 배포 승인",
        url="https://example.com/korean",
        source="GitHub Copilot 변경 이력",
        kind="도구 업데이트",
        published=datetime(2026, 8, 21, tzinfo=UTC),
        summary="GitHub Copilot이 배포 전에 지정 검토자의 승인을 받는 기능을 추가했습니다.",
        detail="배포 요청을 지정 검토자가 확인한 뒤에만 실행하도록 흐름을 바꿉니다.",
        key_points=tuple(
            f"{index}. 확인 항목: 배포 승인 기능을 운영 절차에 맞게 검토합니다."
            for index in range(1, 8)
        ),
        tags=("GitHub Copilot", "배포 승인"),
    )
    week_four = tmp_path / "archive/2026/08/week-4/index.html"
    week_four.parent.mkdir(parents=True)
    week_four.write_text(_render_smart_insight_cards([item]), encoding="utf-8")
    monkeypatch.setattr("aimstletter.site.fetch_recent_items", lambda *_args, **_kwargs: [])
    monkeypatch.setenv("AIMSTLETTER_REQUIRE_OPENAI_LOCALIZATION", "1")

    with pytest.raises(RuntimeError, match="expected archive/2026/08/week-5"):
        build_site(
            tmp_path,
            Settings(openai_api_key=""),
            build_at=datetime(2026, 9, 1, tzinfo=UTC),
        )


def test_localize_items_retries_structurally_invalid_response(monkeypatch) -> None:
    item = DigestItem(
        title="Copilot deployment approvals",
        url="https://example.com/copilot-deployment-approvals",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="GitHub Copilot adds repository deployment approvals with named reviewers.",
    )
    valid_response = json.dumps(
            [
                {
                    "title": "GitHub Copilot 배포 승인 기능",
                    "summary": "GitHub Copilot이 저장소 배포 전에 지정 검토자의 승인을 받는 기능을 추가했습니다.",
                    "detail": "배포 요청을 지정 검토자에게 보내고 승인 이후에만 실행합니다.",
                    "key_points": [
                        "1. 한 줄 요약: 저장소 배포 전에 지정 검토자의 승인을 받습니다.",
                        "2. 무엇이 바뀌었나: 자동 배포 흐름에 명시적인 승인 단계를 추가했습니다.",
                        "3. 왜 중요한가: 승인되지 않은 변경의 운영 반영을 막을 수 있습니다.",
                        "4. 한계와 주의사항: 저장소 권한과 검토자 구성을 먼저 확인해야 합니다.",
                        "5. 이번 주 해볼 일: 시험 저장소에서 승인 규칙 하나를 설정합니다.",
                        "6. 누가 보면 좋은가: 배포를 관리하는 개발자와 운영 담당자입니다.",
                        "7. 출처와 상태: GitHub Copilot 변경 이력에서 공개된 기능입니다.",
                    ],
                    "tags": ["GitHub Copilot", "배포 승인", "저장소"],
                    "comparisons": [],
                    "glossary": [],
                }
            ],
            ensure_ascii=False,
        )
    calls = {"count": 0}
    providers: list[str] = []

    def fake_generate(client, *_args, **_kwargs):
        providers.append(client)
        calls["count"] += 1
        return "[]" if calls["count"] == 1 else valid_response

    monkeypatch.setattr(
        "aimstletter.site._make_client",
        lambda **kwargs: (
            "openai" if kwargs["openai_api_key"] else "azure",
            "test-model",
        ),
    )
    monkeypatch.setattr("aimstletter.site._generate_openai_text", fake_generate)
    monkeypatch.setattr("aimstletter.site.time.sleep", lambda _seconds: None)

    localized = _localize_items(
        [item],
        Settings(
            openai_api_key="test-key",
            azure_openai_endpoint="https://example.openai.azure.com",
            azure_openai_api_key="azure-key",
        ),
        "test",
    )

    assert calls["count"] == 2
    assert providers == ["openai", "azure"]
    assert len(localized) == 1
    assert "지정 검토자의 승인" in localized[0].summary


def test_localize_items_splits_large_batches_before_generation(monkeypatch) -> None:
    items = [
        DigestItem(
            title=f"Deployment approval update {index}",
            url=f"https://example.com/deployment-approval-{index}",
            source="Example Changelog",
            kind="tool",
            published=datetime(2026, 8, 28, tzinfo=UTC),
            summary=f"Deployment approval update {index} adds a named reviewer requirement.",
        )
        for index in range(1, 5)
    ]
    batch_sizes: list[int] = []

    def fake_generate(_client, _model, _instructions, input_text):
        batch_size = input_text.count("title:")
        batch_sizes.append(batch_size)
        payload = []
        for index in range(1, batch_size + 1):
            payload.append(
                {
                    "title": f"배포 승인 업데이트 {index}",
                    "summary": f"배포 승인 업데이트 {index}은 지정 검토자의 승인을 요구합니다.",
                    "detail": f"배포 요청 {index}을 지정 검토자가 확인한 뒤 실행합니다.",
                    "key_points": [
                        f"1. 한 줄 요약: 배포 요청 {index}에 승인 단계를 추가합니다.",
                        f"2. 무엇이 바뀌었나: 배포 요청 {index}에 검토자를 지정합니다.",
                        f"3. 왜 중요한가: 승인되지 않은 배포 {index}을 막습니다.",
                        f"4. 한계와 주의사항: 검토자 {index}의 권한을 확인해야 합니다.",
                        f"5. 이번 주 해볼 일: 시험 배포 {index}에 승인 규칙을 적용합니다.",
                        f"6. 누가 보면 좋은가: 배포 {index} 담당자입니다.",
                        f"7. 출처와 상태: 변경 이력 {index}에서 공개됐습니다.",
                    ],
                    "tags": ["배포", "승인", f"업데이트 {index}"],
                    "comparisons": [],
                    "glossary": [],
                }
            )
        return json.dumps(payload, ensure_ascii=False)

    monkeypatch.setattr("aimstletter.site._make_client", lambda **_kwargs: (object(), "test-model"))
    monkeypatch.setattr("aimstletter.site._generate_openai_text", fake_generate)

    localized = _localize_items(items, Settings(openai_api_key="test-key"), "test")

    assert batch_sizes == [3, 1]
    assert len(localized) == 4


def test_localization_preserves_every_card_after_connection_retries(monkeypatch) -> None:
    item = DigestItem(
        title="Copilot deployment approvals",
        url="https://example.com/copilot-deployment-approvals",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="GitHub Copilot adds repository deployment approvals with named reviewers.",
    )
    calls = {"count": 0}

    def fail_connection(*_args, **_kwargs):
        calls["count"] += 1
        raise ConnectionError("Connection error")

    monkeypatch.setenv("AIMSTLETTER_REQUIRE_OPENAI_LOCALIZATION", "1")
    monkeypatch.setattr("aimstletter.site._make_client", lambda **_kwargs: (object(), "test-model"))
    monkeypatch.setattr("aimstletter.site._generate_openai_text", fail_connection)
    monkeypatch.setattr("aimstletter.site.requests.post", fail_connection)
    monkeypatch.setattr("aimstletter.site.time.sleep", lambda _seconds: None)

    localized = _localize_items([item] * 4, Settings(openai_api_key="test-key"), "test")

    assert calls["count"] == 10
    assert len(localized) == 4
    assert all(card.url == item.url for card in localized)
    assert all(any("가" <= char <= "힣" for char in card.summary) for card in localized)
    assert all("repository deployment approvals" not in card.summary.lower() for card in localized)


def test_week_source_items_survive_between_build_retries(tmp_path) -> None:
    build_at = datetime(2026, 8, 31, 8, tzinfo=UTC)
    archive_entry = _weekly_archive_entry(build_at)
    paper = DigestItem(
        title="Reliable agent benchmark",
        url="https://arxiv.org/abs/2608.99999",
        source="arXiv AI",
        kind="paper",
        published=datetime(2026, 8, 29, tzinfo=UTC),
        summary="The benchmark evaluates repeated reliability across 200 tasks.",
    )
    tool = DigestItem(
        title="Deployment approvals",
        url="https://example.com/deployment-approvals",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="Named reviewers approve deployments before execution.",
    )

    _write_week_source_items(tmp_path, archive_entry, [paper], [tool], build_at)
    ai_items, tool_items = _load_week_source_items(tmp_path, archive_entry)

    assert ai_items == [paper]
    assert tool_items == [tool]


def test_source_only_build_skips_feed_collection(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("AIMSTLETTER_SOURCE_ONLY", "1")
    monkeypatch.setattr(
        "aimstletter.site.fetch_recent_items",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("feed should not be fetched")),
    )
    with pytest.raises(RuntimeError, match="no verified cards"):
        build_site(tmp_path, Settings(openai_api_key=""))


def test_source_only_build_publishes_all_cached_cards_without_openai(monkeypatch, tmp_path) -> None:
    build_at = datetime(2026, 9, 1, tzinfo=UTC)
    archive_entry = _weekly_archive_entry(build_at)
    trend = DigestItem(
        title="Agent operations update",
        url="https://example.com/agent-operations",
        source="Example AI News",
        kind="trend",
        published=datetime(2026, 8, 29, tzinfo=UTC),
        summary="Agent operations now expose task state and approval checkpoints to administrators.",
    )
    tool = DigestItem(
        title="Deployment approvals",
        url="https://example.com/deployment-approvals",
        source="Example Tool News",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="Named reviewers approve deployments before execution begins.",
    )
    _write_week_source_items(tmp_path, archive_entry, [trend], [tool], build_at)
    monkeypatch.setenv("AIMSTLETTER_SOURCE_ONLY", "1")
    monkeypatch.setenv("AIMSTLETTER_REQUIRE_OPENAI_LOCALIZATION", "1")
    monkeypatch.setattr(
        "aimstletter.site.fetch_recent_items",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("feed should not be fetched")),
    )
    monkeypatch.setattr("aimstletter.site._enrich_items_from_source_pages", lambda items: items)

    index_path = build_site(tmp_path, Settings(openai_api_key=""), build_at=build_at)
    html_text = index_path.read_text(encoding="utf-8")
    archive_text = (tmp_path / "archive/2026/08/week-5/index.html").read_text(encoding="utf-8")

    assert html_text.count('<button class="insight-card"') == 2
    assert archive_text.count('<button class="insight-card"') == 2
    assert "수집된 본문 요약이 부족" not in archive_text
    assert "approval checkpoints" not in archive_text
    assert "Named reviewers approve deployments" not in archive_text
    assert "핵심 변경과 적용 범위" in archive_text


def test_source_match_confidence_rejects_unrelated_recovered_content() -> None:
    original = DigestItem(
        title="Purchase API Agentcard",
        url="https://www.producthunt.com/products/agent-card",
        source="Product Hunt Launches",
        kind="tool",
        published=datetime(2026, 8, 24, tzinfo=UTC),
        summary="Purchase API Agentcard",
    )

    assert _source_match_confidence(
        original,
        "Completely Different Product",
        "A calendar scheduling product for meetings and emails.",
        "https://www.producthunt.com/products/different-product",
    ) == 0


def test_web_source_recovery_retries_before_fallback(monkeypatch, tmp_path) -> None:
    item = DigestItem(
        title="Agent Card",
        url="https://www.producthunt.com/products/agent-card",
        source="Product Hunt Launches",
        kind="tool",
        published=datetime(2026, 8, 24, tzinfo=UTC),
        summary="Agent Card",
    )
    attempts = {"count": 0}
    monkeypatch.setenv("AIMSTLETTER_SOURCE_CACHE_DIR", str(tmp_path))

    class FakeResponse:
        url = item.url
        text = (
            '<meta property="og:title" content="Agent Card | Product Hunt">'
            '<meta property="og:description" content="Agent Card helps AI agents publish discoverable capability cards.">'
        )

        def raise_for_status(self) -> None:
            return None

    def fake_get(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise requests.RequestException("temporary network failure")
        return FakeResponse()

    monkeypatch.setattr("aimstletter.site.requests.get", fake_get)
    monkeypatch.setattr("aimstletter.site.time.sleep", lambda _seconds: None)

    recovered = _recover_web_source_item(item)

    assert recovered is not None
    assert attempts["count"] == 3
    assert "discoverable capability cards" in recovered.summary


def test_web_source_recovery_retries_successful_but_empty_page(monkeypatch, tmp_path) -> None:
    item = DigestItem(
        title="Agent Card",
        url="https://www.producthunt.com/products/agent-card",
        source="Product Hunt Launches",
        kind="tool",
        published=datetime(2026, 8, 24, tzinfo=UTC),
        summary="Agent Card",
    )
    attempts = {"count": 0}
    monkeypatch.setenv("AIMSTLETTER_SOURCE_CACHE_DIR", str(tmp_path))

    class FakeResponse:
        url = item.url

        @property
        def text(self) -> str:
            if attempts["count"] == 1:
                return '<meta property="og:title" content="Agent Card | Product Hunt">'
            return (
                '<script type="application/ld+json">'
                '{"name":"Agent Card","description":"Agent Card publishes verified capability cards for AI agents."}'
                "</script>"
            )

        def raise_for_status(self) -> None:
            return None

    def fake_get(*_args, **_kwargs):
        attempts["count"] += 1
        return FakeResponse()

    monkeypatch.setattr("aimstletter.site.requests.get", fake_get)
    monkeypatch.setattr("aimstletter.site.time.sleep", lambda _seconds: None)

    recovered = _recover_web_source_item(item)

    assert recovered is not None
    assert attempts["count"] == 2
    assert "verified capability cards" in recovered.summary


def test_homepage_archive_navigation_uses_fresh_archive_search_text(tmp_path) -> None:
    index_path = tmp_path / "index.html"
    index_path.write_text(
        '<aside class="archive-nav" aria-label="주간 아카이브">'
        '<a data-archive-index="stale related changes">08월 4째주</a>'
        "</aside>",
        encoding="utf-8",
    )
    entry = {
        "year": 2026,
        "month": 8,
        "week": 4,
        "href": "archive/2026/08/week-4/",
        "period_start": "2026-08-17",
        "period_end": "2026-08-24",
        "period_label": "2026-08-17~2026-08-24 데이터",
        "search_text": "fresh source-backed summary",
    }

    _refresh_homepage_archive_navigation(index_path, [entry], entry)

    html_text = index_path.read_text(encoding="utf-8")
    assert "fresh source-backed summary" in html_text
    assert "stale related changes" not in html_text


def test_refresh_known_specific_cards_updates_existing_agnost_html() -> None:
    old_body = "Agnost AI related changes affect the workflow."
    html_text = (
        '<button class="insight-card" type="button" data-insight-card data-number="12" '
        'data-title="Agnost AI" data-category="tool" data-subcategory="AI agent" '
        f'data-body="{html.escape(old_body)}" data-detail="{html.escape(old_body)}" '
        f'data-points="{html.escape(json.dumps(["1. Summary: " + old_body]))}" '
        'data-meta="Product Hunt Launches · tool update · 2026-08-23" '
        'data-tags="[]" data-source="https://www.producthunt.com/products/agnost-ai">'
        '<span><span class="card-heading"><span class="card-title">Agnost AI</span></span>'
        f"<p>{html.escape(old_body)}</p></span></button>"
    )

    refreshed, count = _refresh_known_specific_cards_in_html(html_text)

    assert count == 1
    assert "silent failure" in refreshed
    assert old_body not in refreshed


def test_refresh_paper_cards_in_html_updates_existing_card_data() -> None:
    old_body = "Thinkingbox evaluates stateful workflows."
    points = [
        "1. Summary: Thinkingbox evaluates stateful workflows.",
        "2. Change: It is a benchmark.",
        "3. Importance: Reliability matters.",
        "4. Caution: Paper-stage result.",
        "5. Action: Try a small evaluation.",
        "6. Audience: AI engineers",
        "7. Source: arXiv",
    ]
    html_text = (
        '<button class="insight-card" type="button" data-insight-card data-number="1" '
        'data-title="Thinkingbox" data-category="paper" data-subcategory="arXiv Database AI" '
        f'data-body="{html.escape(old_body)}" data-detail="{html.escape(old_body)}" '
        f'data-points="{html.escape(json.dumps(points))}" '
        'data-meta="arXiv Database AI · paper · 2026-08-20" '
        'data-tags="[]" data-source="https://arxiv.org/abs/2608.19741v1">'
        '<span><span class="card-heading"><span class="card-title">Thinkingbox</span></span>'
        f"<p>{html.escape(old_body)}</p></span></button>"
    )

    cache: dict[str, object] = {
        "https://arxiv.org/abs/2608.19741v1": DigestItem(
            title="Thinkingbox",
            url="https://arxiv.org/abs/2608.19741v1",
            source="arXiv Database AI",
            kind="paper",
            published=datetime(2026, 8, 20, tzinfo=UTC),
            summary=(
                "Existing agent benchmarks often reward one successful completion. "
                "Thinkingbox evaluates 507 policy-conditioned business workflows with executable final-state checks. "
                "The best model reaches 65.36% single-attempt success, but only 25.25% reliability over 20 repeated runs."
            ),
        )
    }

    refreshed, count = _refresh_paper_cards_in_html(html_text, cache)

    assert count == 1
    assert "65.36%" in refreshed
    assert "25.25%" in refreshed
    assert old_body not in refreshed


def test_refresh_paper_cards_removes_forced_metric_fallback_without_fetch() -> None:
    old_body = (
        "Ratrain Resource Aware 논문은 초록에 나온 평가 방식과 결과를 중심으로 봐야 합니다. "
        "Ratrain Resource Aware는 1.35, 3000 같은 핵심 수치를 통해 논문의 주장과 평가 결과를 확인하게 합니다."
    )
    points = [
        "1. 한 줄 요약: Ratrain Resource Aware는 1.35, 3000 같은 핵심 수치를 통해 논문의 주장과 평가 결과를 확인하게 합니다.",
        "2. 무엇이 바뀌었나: 기존 접근과의 차이는 초록의 대비 문장에서 확인됩니다.",
        "3. 왜 중요한가: 1.35, 3000 같은 핵심 수치가 논문의 주장과 실제 효과를 판단하는 기준입니다.",
        "4. 한계와 주의사항: Paper-stage result.",
        "5. 이번 주 해볼 일: Try a small evaluation.",
        "6. 누가 보면 좋은가: AI engineers",
        "7. 출처와 상태: arXiv",
    ]
    html_text = (
        '<button class="insight-card" type="button" data-insight-card data-number="1" '
        'data-title="Ratrain Resource Aware" data-category="paper" data-subcategory="arXiv Distributed AI" '
        f'data-body="{html.escape(old_body)}" data-detail="{html.escape(old_body)}" '
        f'data-points="{html.escape(json.dumps(points, ensure_ascii=False))}" '
        'data-meta="arXiv Distributed AI 쨌 paper 쨌 2026-06-09" '
        'data-tags="[]" data-source="https://arxiv.org/abs/2606.00000v1">'
        '<span><span class="card-heading"><span class="card-title">Ratrain Resource Aware</span></span>'
        f"<p>{html.escape(old_body)}</p></span></button>"
    )

    refreshed, count = _refresh_paper_cards_in_html(html_text, {"__arxiv_fetch_disabled__": None})

    assert count == 0
    assert refreshed == html_text


def test_refresh_rewrites_existing_unpublishable_fallback_card() -> None:
    bad_points = [
        "1. 한 줄 요약: Copilot 코드 리뷰 Resolution과 관련된 변화가 업무 흐름에 미치는 영향을 정리한 항목입니다.",
        "2. 무엇이 바뀌었나: 수집된 본문 요약이 부족해 Copilot 코드 리뷰 Resolution의 세부 기능은 GitHub Copilot 변경 이력의 제목과 출처 범위에서만 다룹니다.",
        "3. 왜 중요한가: 원문 본문을 재수집해 확인하기 전까지 기능, 성능, 적용 효과를 추정하지 않습니다.",
        "4. 한계와 주의사항: 현재 카드는 제목과 출처 메타데이터만 검증된 상태라 원문 확인 전 업무 적용 판단에 쓰면 안 됩니다.",
        "5. 이번 주 해볼 일: 원문을 다시 열어 확인하세요.",
        "6. 누가 보면 좋은가: AI 엔지니어",
        "7. 출처와 상태: GitHub Copilot 변경 이력 · 공식 발표 · 2026-08-28",
    ]
    good_points = [
        "1. 한 줄 요약: GitHub Copilot은 코드 리뷰 코멘트의 해결 상태를 추적하는 흐름을 추가했습니다.",
        "2. 무엇이 바뀌었나: 리뷰 코멘트 처리 상태를 더 명확히 볼 수 있습니다.",
        "3. 왜 중요한가: PR 리뷰 후속 조치가 누락되는 일을 줄입니다.",
        "4. 한계와 주의사항: 저장소 권한과 지원 플랜을 확인해야 합니다.",
        "5. 이번 주 해볼 일: 낮은 위험 PR에서 리뷰 해결 흐름을 확인하세요.",
        "6. 누가 보면 좋은가: 백엔드, AI 엔지니어",
        "7. 출처와 상태: GitHub Copilot 변경 이력 · 공식 발표 · 2026-08-28",
    ]
    html_text = (
        '<div data-insight-grid>'
        '<button class="insight-card" type="button" data-insight-card data-number="1" '
        'data-title="Copilot 코드 리뷰 Resolution" data-category="도구" data-subcategory="GitHub Copilot" '
        'data-body="수집된 본문 요약이 부족해 제목과 출처 범위에서만 다룹니다." '
        'data-detail="원문 본문을 재수집해 확인하기 전까지 기능, 성능, 적용 효과를 추정하지 않습니다." '
        f'data-points="{html.escape(json.dumps(bad_points, ensure_ascii=False))}" '
        'data-meta="GitHub Copilot 변경 이력 · 공식 발표 · 2026-08-28" data-tags="[]" '
        'data-source="https://github.blog/changelog/bad"><span><span class="card-title">Bad</span><p>수집된 본문 요약이 부족해 제목과 출처 범위에서만 다룹니다.</p></span></button>'
        '<button class="insight-card" type="button" data-insight-card data-number="2" '
        'data-title="GitHub Copilot 리뷰 해결 상태" data-category="도구" data-subcategory="GitHub Copilot" '
        'data-body="GitHub Copilot은 코드 리뷰 코멘트의 해결 상태를 추적하는 흐름을 추가했습니다." '
        'data-detail="GitHub Copilot은 코드 리뷰 코멘트의 해결 상태를 추적하는 흐름을 추가했습니다." '
        f'data-points="{html.escape(json.dumps(good_points, ensure_ascii=False))}" '
        'data-meta="GitHub Copilot 변경 이력 · 공식 발표 · 2026-08-28" '
        f'data-tags="{html.escape(json.dumps(["GitHub Copilot"], ensure_ascii=False))}" '
        'data-source="https://github.blog/changelog/good"><span><span class="card-title">Good</span><p>GitHub Copilot은 코드 리뷰 코멘트의 해결 상태를 추적하는 흐름을 추가했습니다.</p></span></button>'
        '<article class="insight-detail"><p>수집된 본문 요약이 부족해 제목과 출처 범위에서만 다룹니다.</p></article>'
        "</div>"
    )

    refreshed, count = _remove_unpublishable_cards_in_html(html_text)

    assert count == 1
    assert refreshed.count('<button class="insight-card"') == 2
    assert "https://github.blog/changelog/bad" in refreshed
    assert "수집된 본문 요약이 부족" not in refreshed
    assert "본문 수집 대기" in refreshed
    assert "GitHub Copilot은 코드 리뷰 코멘트의 해결 상태" in refreshed
