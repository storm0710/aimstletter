from __future__ import annotations

import html
import json
from datetime import UTC, datetime

import requests

from aimstletter.fetchers import DigestItem
from aimstletter.site import (
    _localized_site_item,
    _recover_web_source_item,
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
