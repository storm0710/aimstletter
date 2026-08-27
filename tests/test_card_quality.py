from __future__ import annotations

import html
import json
from datetime import UTC, datetime

import requests

from aimstletter.fetchers import DigestItem
from aimstletter.site import (
    _localized_site_item,
    _normalize_search_text,
    _paper_focused_summary,
    _recover_web_source_item,
    _render_smart_insight_cards,
    _refresh_homepage_archive_navigation,
    _refresh_known_specific_cards_in_html,
    _refresh_paper_cards_in_html,
    _source_match_confidence,
)


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
