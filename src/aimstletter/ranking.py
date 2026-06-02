from __future__ import annotations

from datetime import UTC, datetime

from aimstletter.config import SIGNAL_KEYWORDS
from aimstletter.fetchers import DigestItem


def rank_items(items: list[DigestItem], limit: int) -> list[DigestItem]:
    ranked = [item.__class__(**{**item.__dict__, "score": _score(item)}) for item in items]
    ranked.sort(key=lambda item: (item.score, item.published), reverse=True)
    return ranked[:limit]


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
