from __future__ import annotations

import html
import json
from datetime import UTC, datetime

import requests

from aimstletter.fetchers import DigestItem
from aimstletter.config import Settings
from aimstletter.site import (
    _clean_unpublishable_archive_indexes,
    _clean_unpublishable_intro_copy,
    _filter_publishable_source_items,
    _localized_site_item,
    _localize_items,
    _normalize_search_text,
    _paper_focused_summary,
    _recover_web_source_item,
    _remove_unpublishable_cards_in_html,
    _render_smart_insight_cards,
    _refresh_homepage_archive_navigation,
    _refresh_known_specific_cards_in_html,
    _refresh_paper_cards_in_html,
    _source_match_confidence,
)


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


def test_localize_items_without_openai_does_not_emit_fallback_cards() -> None:
    item = DigestItem(
        title="Copilot code review Resolution",
        url="https://github.blog/changelog/2026-08-28-copilot-code-review-resolution",
        source="GitHub Copilot Changelog",
        kind="tool",
        published=datetime(2026, 8, 28, tzinfo=UTC),
        summary="GitHub Copilot code review adds a resolution workflow for review comments.",
    )

    assert _localize_items([item], Settings(openai_api_key=""), "test") == []


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


def test_refresh_removes_existing_unpublishable_fallback_card() -> None:
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
    assert "https://github.blog/changelog/bad" not in refreshed
    assert "수집된 본문 요약이 부족" not in refreshed
    assert "GitHub Copilot은 코드 리뷰 코멘트의 해결 상태" in refreshed
