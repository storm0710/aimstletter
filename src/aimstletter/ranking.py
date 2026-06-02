from __future__ import annotations

from datetime import UTC, datetime

from aimstletter.config import INFRA_KEYWORDS, SIGNAL_KEYWORDS
from aimstletter.fetchers import DigestItem


def rank_items(items: list[DigestItem], limit: int) -> list[DigestItem]:
    ranked = [item.__class__(**{**item.__dict__, "score": _score(item)}) for item in items]
    target_count = min(5, limit)
    other_count = max(limit - target_count, 0)

    related = [item for item in ranked if _infra_score(item) > 0]
    related.sort(key=lambda item: (_infra_score(item), item.score, item.published), reverse=True)
    selected_related = related[:target_count]
    selected_urls = {item.url for item in selected_related}

    remaining = [item for item in ranked if item.url not in selected_urls]
    remaining.sort(key=lambda item: (item.score, item.published), reverse=True)

    if len(selected_related) < target_count:
        fill_count = target_count - len(selected_related)
        selected_related.extend(remaining[:fill_count])
        selected_urls = {item.url for item in selected_related}
        remaining = [item for item in ranked if item.url not in selected_urls]
        remaining.sort(key=lambda item: (item.score, item.published), reverse=True)

    selected_other = remaining[:other_count]
    return selected_related + selected_other


def _score(item: DigestItem) -> int:
    text = f"{item.title} {item.summary}".lower()
    score = 0
    for keyword, weight in SIGNAL_KEYWORDS.items():
        if keyword in text:
            score += weight

    age_hours = max((datetime.now(UTC) - item.published).total_seconds() / 3600, 1)
    recency_bonus = max(0, 48 - int(age_hours)) // 12
    kind_bonus = 2 if item.kind == "paper" else 0
    return score + recency_bonus + kind_bonus


def _infra_score(item: DigestItem) -> int:
    text = f"{item.title} {item.summary}".lower()
    score = 0
    for keyword, weight in INFRA_KEYWORDS.items():
        if keyword in text:
            score += weight
    return score
