from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import re
import textwrap

from aimstletter.composer import _make_client
from aimstletter.config import Settings
from aimstletter.fetchers import DigestItem, fetch_recent_items
from aimstletter.ranking import rank_items


@dataclass(frozen=True)
class SiteItem:
    title: str
    url: str
    source: str
    kind: str
    published: datetime
    summary: str
    key_points: tuple[str, ...]
    tags: tuple[str, ...]


WORK_SKILL_KEYWORDS = {
    "workflow": 8,
    "workflows": 8,
    "automation": 8,
    "automate": 8,
    "agent": 7,
    "agents": 7,
    "copilot": 7,
    "codex": 7,
    "api": 6,
    "sdk": 6,
    "github actions": 6,
    "database": 6,
    "query": 5,
    "monitoring": 6,
    "observability": 6,
    "incident": 6,
    "security": 5,
    "deployment": 5,
    "coding": 5,
    "developer": 5,
    "operations": 5,
    "server": 5,
    "network": 5,
    "kubernetes": 5,
    "cloud": 4,
    "rag": 4,
    "retrieval": 4,
}

GENERAL_STORY_KEYWORDS = {
    "case": 3,
    "story": 3,
    "scam": 5,
    "myth": 4,
    "pope": 4,
    "policy": 3,
    "agenda": 3,
    "health care": 2,
}


def build_site(output_dir: Path, settings: Settings) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    source_items = _dedupe_items(
        [
            *fetch_recent_items(settings.feeds, settings.lookback_days),
            *fetch_recent_items(settings.tool_feeds, 21),
        ]
    )
    skill_items = _rank_work_skill_updates(source_items, 5)
    skill_urls = {item.url for item in skill_items}
    other_source_items = [item for item in source_items if item.url not in skill_urls]
    ai_items = [*skill_items, *_latest_digest_items(rank_items(other_source_items, 12), 5)]
    tool_items = _rank_tool_updates(fetch_recent_items(settings.tool_feeds, 21), 10)
    ai_items = _localize_items(ai_items, settings, "DBA, 네트워크, 서버 운영자가 업무에 적용할 AI 스킬 업데이트")
    tool_items = _localize_items(tool_items, settings, "인공지능 도구 업데이트")
    html = render_homepage(ai_items, tool_items)

    path = output_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def render_homepage(ai_items: list[SiteItem], tool_items: list[SiteItem]) -> str:
    kst = timezone(timedelta(hours=9), name="KST")
    today = datetime.now(UTC).astimezone(kst).strftime("%Y년 %m월 %d일")
    infra_items = _latest_first(ai_items[:5])
    other_items = _latest_first(ai_items[5:10])
    latest_tool_items = _latest_first(tool_items[:10])

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Master Times</title>
  <meta name="description" content="인공지능 마스터 과정용 주간 인공지능 업데이트와 도구 출시 소식">
  <style>
    :root {{
      color-scheme: light;
      --ink: #111111;
      --muted: #5b5b5b;
      --line: #d8d2c4;
      --paper: #f7f3ea;
      --accent: #8b1e16;
      --rule: #222222;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
    }}
    a {{ color: inherit; text-decoration-thickness: 1px; text-underline-offset: 3px; }}
    .page {{
      width: min(1420px, calc(100% - 32px));
      margin: 0 auto;
      padding: 18px 0 44px;
    }}
    .topline {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      border-top: 3px solid var(--rule);
      border-bottom: 1px solid var(--rule);
      padding: 8px 0;
      font: 700 13px/1.4 Arial, "Noto Sans KR", sans-serif;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .masthead {{
      border-bottom: 3px double var(--rule);
      padding: 20px 0 18px;
      text-align: center;
    }}
    .masthead h1 {{
      margin: 0;
      font-size: clamp(48px, 9vw, 104px);
      line-height: .9;
      letter-spacing: 0;
    }}
    .masthead p {{
      margin: 12px auto 0;
      max-width: 860px;
      color: var(--muted);
      font: 16px/1.6 Arial, "Noto Sans KR", sans-serif;
    }}
    .kicker {{
      color: var(--accent);
      font: 800 12px/1.4 Arial, "Noto Sans KR", sans-serif;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h2, h3 {{ margin: 0; letter-spacing: 0; }}
    .summary {{
      color: #282828;
      font-size: 17px;
      line-height: 1.68;
      margin: 12px 0 0;
    }}
    .newspaper {{
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(340px, .65fr);
      gap: 32px;
      padding-top: 28px;
    }}
    .column {{
      min-width: 0;
    }}
    .column + .column {{
      border-left: 1px solid var(--rule);
      padding-left: 24px;
    }}
    .section-title {{
      border-bottom: 2px solid var(--rule);
      padding-bottom: 8px;
      margin-bottom: 14px;
      font-size: 24px;
    }}
    .article {{
      border-bottom: 1px solid var(--line);
      padding: 14px 0;
    }}
    .article h3 {{
      font-size: 22px;
      line-height: 1.22;
    }}
    .article p {{
      color: #303030;
      font-size: 15.5px;
      line-height: 1.65;
      margin: 8px 0 0;
    }}
    .meta {{
      color: var(--muted);
      font: 700 12px/1.45 Arial, "Noto Sans KR", sans-serif;
      margin-top: 8px;
    }}
    .key-points {{
      margin: 9px 0 0;
      padding-left: 18px;
      color: #222222;
      font: 14px/1.55 Arial, "Noto Sans KR", sans-serif;
    }}
    .points-label {{
      margin-top: 10px;
      color: var(--accent);
      font: 800 12px/1.3 Arial, "Noto Sans KR", sans-serif;
    }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }}
    .tag {{
      border: 1px solid var(--line);
      background: #fffaf0;
      padding: 3px 7px;
      font: 700 12px/1.3 Arial, "Noto Sans KR", sans-serif;
    }}
    .tool-list {{
      display: grid;
      gap: 12px;
    }}
    .tool-item {{
      border-bottom: 1px solid var(--line);
      padding-bottom: 12px;
    }}
    .tool-item h3 {{
      font-size: 19px;
      line-height: 1.26;
    }}
    .tool-item p {{
      margin: 7px 0 0;
      color: #333333;
      font: 14px/1.58 Arial, "Noto Sans KR", sans-serif;
    }}
    footer {{
      border-top: 3px double var(--rule);
      margin-top: 28px;
      padding-top: 12px;
      color: var(--muted);
      font: 13px/1.5 Arial, "Noto Sans KR", sans-serif;
    }}
    @media (max-width: 840px) {{
      .newspaper {{
        grid-template-columns: 1fr;
      }}
      .column + .column {{
        border-left: 0;
        padding-left: 0;
      }}
      .topline {{
        flex-direction: column;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <div class="topline">
      <span>AI Master 과정 주간판</span>
      <span>{escape(today)} · 깃허브 페이지판</span>
    </div>
    <header class="masthead">
      <h1>AI Master Times</h1>
      <p>데이터베이스 관리자, 네트워크, 서버 운영 직군이 AI를 업무 스킬과 비즈니스 모델로 연결할 수 있도록 매주 선별한 연구와 도구 업데이트입니다.</p>
    </header>

    <section class="newspaper" aria-label="주간 업데이트">
      <div class="column">
        <h2 class="section-title">업무 AI 스킬 업데이트 · 상위 5개</h2>
        {_render_articles(infra_items)}
        <h2 class="section-title">기타 AI 동향 · 하위 5개</h2>
        {_render_articles(other_items)}
      </div>
      <aside class="column">
        <h2 class="section-title">Claude와 AI 도구 업데이트</h2>
        <div class="tool-list">
          {_render_tool_items(latest_tool_items)}
        </div>
      </aside>
    </section>
    <footer>
      자동 생성: 깃허브 액션 · 출처 링크를 눌러 원문을 확인하세요. 커서는 공식 변경 이력 링크를 고정 노출하고, 웹 피드가 안정적인 도구는 최신 글을 자동 수집합니다.
    </footer>
  </main>
</body>
</html>
"""


def _render_articles(items: list[SiteItem]) -> str:
    if not items:
        return '<p class="summary">표시할 항목이 없습니다.</p>'
    return "\n".join(
        (
            '<article class="article">'
            f'<div class="kicker">{escape(item.kind)} · {escape(item.source)}</div>'
            f'<h3><a href="{escape(item.url)}">{escape(item.title)}</a></h3>'
            f'<p>{escape(_clip(item.summary, 300))}</p>'
            f"{_render_key_points(item)}"
            f"{_render_tags(item)}"
            f'<div class="meta">{_format_date(item.published)}</div>'
            "</article>"
        )
        for item in items
    )


def _render_tool_items(items: list[SiteItem]) -> str:
    if not items:
        return '<p class="summary">표시할 도구 업데이트가 없습니다.</p>'
    return "\n".join(
        (
            '<article class="tool-item">'
            f'<div class="kicker">{escape(item.source)}</div>'
            f'<h3><a href="{escape(item.url)}">{escape(item.title)}</a></h3>'
            f'<p>{escape(_clip(item.summary, 210))}</p>'
            f"{_render_key_points(item)}"
            f"{_render_tags(item)}"
            f'<div class="meta">{_format_date(item.published)}</div>'
            "</article>"
        )
        for item in items
    )


def _render_key_points(item: SiteItem) -> str:
    if not item.key_points:
        return ""
    points = "".join(f"<li>{escape(point)}</li>" for point in item.key_points[:3])
    return f'<div class="points-label">키포인트</div><ul class="key-points">{points}</ul>'


def _render_tags(item: SiteItem) -> str:
    if not item.tags:
        return ""
    tags = "".join(f'<span class="tag">#{escape(tag)}</span>' for tag in item.tags[:5])
    return f'<div class="tags" aria-label="중요 키워드">{tags}</div>'


def _localize_items(items: list[DigestItem], settings: Settings, context: str) -> list[SiteItem]:
    if not items:
        return []
    if not settings.openai_api_key and not settings.azure_openai_api_key:
        return [_fallback_korean_item(item) for item in items]

    source_block = "\n\n".join(
        textwrap.dedent(
            f"""
            [{index}]
            title: {item.title}
            source: {item.source}
            type: {item.kind}
            summary: {item.summary}
            """
        ).strip()
        for index, item in enumerate(items, start=1)
    )

    try:
        client, model = _make_client(
            openai_api_key=settings.openai_api_key,
            openai_model=settings.openai_model,
            azure_openai_endpoint=settings.azure_openai_endpoint,
            azure_openai_api_key=settings.azure_openai_api_key,
            azure_openai_deployment=settings.azure_openai_deployment,
        )
        response = client.responses.create(
            model=model,
            instructions=(
                "Return only a JSON array. Each item must contain title, summary, key_points, and tags. "
                "Titles and summaries must be Korean sentences. Product names such as OpenAI, "
                "Claude, Cursor, GitHub Copilot, Codex, Gartner, Endava, AWS, and Azure must stay in English. "
                "key_points must be an array of 2 or 3 concise Korean strings. tags must be an array of "
                "3 to 5 short Korean or product-name strings. Emphasize practical work skills, "
                "automation patterns, operational usage, and concrete tool adoption. Do not invent facts."
            ),
            input=(
                f"Translate and rewrite these {context} items for a Korean newsletter site. "
                "Use natural Korean titles that preserve product and company names in English. "
                "Summaries must be one concise Korean sentence and must make clear what a DBA, "
                "network engineer, server operator, or technical mentor can do with it at work. "
                "Key points should explain: what changed, where it can be used in work, and what "
                "to watch before adoption.\n\n"
                f"{source_block}"
            ),
        )
        localized = _parse_json_array(response.output_text)
        if _has_untranslated_items(localized):
            localized = _repair_korean_translation(client, model, source_block, context)
    except Exception:  # noqa: BLE001
        return [_fallback_korean_item(item) for item in items]

    if len(localized) != len(items):
        return [_fallback_korean_item(item) for item in items]

    return [
        SiteItem(
            title=_safe_korean_field(
                localized_item.get("title"),
                fallback=f"{_korean_source_name(item.source)}에서 확인한 최신 업데이트",
            ),
            url=item.url,
            summary=_safe_korean_field(
                localized_item.get("summary"),
                fallback="원문 요약을 한국어로 변환하지 못해 출처 링크에서 세부 내용을 확인해 주세요.",
            ),
            source=_korean_source_name(item.source),
            kind=_korean_kind_name(item.kind),
            published=item.published,
            key_points=_safe_key_points(localized_item, item),
            tags=_safe_tags(localized_item, item),
        )
        for item, localized_item in zip(items, localized, strict=True)
    ]


def _repair_korean_translation(
    client: object,
    model: str,
    source_block: str,
    context: str,
) -> list[dict[str, object]]:
    response = client.responses.create(
        model=model,
        instructions=(
            "Return only a JSON array. Each item must contain title, summary, key_points, and tags. "
            "Translate English article titles and summaries into Korean. Product names may "
            "remain in English, but English clauses or English explanatory sentences are not allowed. "
            "key_points must be an array of 2 or 3 concise Korean strings. tags must be an array of "
            "3 to 5 short Korean or product-name strings."
        ),
        input=(
            f"The previous Korean localization for these {context} items contained untranslated "
            "English. Rewrite them again. Examples: "
            "'OpenAI named a Leader in enterprise coding agents by Gartner' should become "
            "'OpenAI, 가트너 엔터프라이즈 코딩 에이전트 분야 리더로 선정'. "
            "'OpenAI is named a leader...' should become a Korean sentence.\n\n"
            f"{source_block}"
        ),
    )
    return _parse_json_array(response.output_text)


def _has_untranslated_items(items: list[dict[str, object]]) -> bool:
    return any(
        _looks_untranslated(str(item.get("title", "")))
        or _looks_untranslated(str(item.get("summary", "")))
        for item in items
    )


def _safe_korean_field(value: object, fallback: str) -> str:
    cleaned = _clean_visible_korean(str(value or ""))
    if not cleaned or _looks_untranslated(cleaned):
        return fallback
    return cleaned


def _safe_key_points(localized_item: dict[str, object], original: DigestItem) -> tuple[str, ...]:
    raw_points = localized_item.get("key_points")
    points = _coerce_string_list(raw_points)
    safe_points = [
        _clean_visible_korean(point)
        for point in points
        if point and not _looks_untranslated(point)
    ]
    if safe_points:
        return tuple(safe_points[:3])
    return (
        "원문에서 확인한 변화가 업무 자동화나 운영 방식에 어떤 영향을 줄지 검토하세요.",
        f"{_korean_source_name(original.source)}의 최신 발표이므로 원문 링크에서 세부 내용을 확인하세요.",
    )


def _safe_tags(localized_item: dict[str, object], original: DigestItem) -> tuple[str, ...]:
    raw_tags = localized_item.get("tags")
    tags = [_normalize_tag(tag) for tag in _coerce_string_list(raw_tags)]
    tags = [tag for tag in tags if tag]
    if tags:
        return tuple(list(dict.fromkeys(tags))[:5])
    return tuple(_fallback_tags(original)[:5])


def _coerce_string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [part.strip(" -") for part in re.split(r"[,;\n]", stripped) if part.strip(" -")]
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item).strip()]
    return []


def _normalize_tag(tag: str) -> str:
    tag = _clean_visible_korean(tag).strip("#")
    replacements = {
        "오픈에이아이": "OpenAI",
        "클로드": "Claude",
        "커서": "Cursor",
        "깃허브 코파일럿": "GitHub Copilot",
    }
    return replacements.get(tag, tag)


def _fallback_tags(item: DigestItem) -> list[str]:
    text = f"{item.title} {item.summary} {item.source}".lower()
    tags: list[str] = []
    for keyword, label in (
        ("openai", "OpenAI"),
        ("claude", "Claude"),
        ("copilot", "GitHub Copilot"),
        ("cursor", "Cursor"),
        ("agent", "AI 에이전트"),
        ("database", "데이터베이스"),
        ("network", "네트워크"),
        ("security", "보안"),
        ("server", "서버 운영"),
        ("coding", "코딩 자동화"),
        ("enterprise", "엔터프라이즈"),
    ):
        if keyword in text:
            tags.append(label)
    return tags or [_korean_source_name(item.source), _korean_kind_name(item.kind)]


def _looks_untranslated(text: str) -> bool:
    latin_letters = len(re.findall(r"[A-Za-z]", text))
    hangul_letters = len(re.findall(r"[가-힣]", text))
    if latin_letters < 18:
        return False
    return hangul_letters == 0 or latin_letters > hangul_letters * 2


def _fallback_korean_item(item: DigestItem) -> SiteItem:
    return SiteItem(
        title=f"{_korean_source_name(item.source)}에서 확인한 최신 업데이트",
        summary="원문을 한국어로 자동 변환하려면 저장소 비밀값에 Azure OpenAI 또는 OpenAI 연결 키를 설정하세요.",
        source=_korean_source_name(item.source),
        kind=_korean_kind_name(item.kind),
        url=item.url,
        published=item.published,
        key_points=(
            "원문 내용을 한국어로 자동 요약하려면 모델 연결 설정이 필요합니다.",
            "출처 링크에서 세부 내용을 확인한 뒤 수업 토론 주제로 활용하세요.",
        ),
        tags=tuple(_fallback_tags(item)[:5]),
    )


def _parse_json_array(text: str) -> list[dict[str, object]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            raise
        data = json.loads(match.group(0))

    if not isinstance(data, list):
        raise ValueError("Expected a JSON array.")

    normalized: list[dict[str, object]] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Expected each JSON item to be an object.")
        normalized.append({str(key): value for key, value in item.items() if value})
    return normalized


def _clean_visible_korean(text: str) -> str:
    return " ".join(text.split())


def _korean_kind_name(kind: str) -> str:
    return {
        "paper": "논문",
        "trend": "동향",
        "tool": "도구 업데이트",
    }.get(kind, "자료")


def _korean_source_name(source: str) -> str:
    names = {
        "Anthropic News": "Anthropic 소식",
        "OpenAI News": "OpenAI 소식",
        "GitHub Copilot Changelog": "GitHub Copilot 변경 이력",
        "GitHub Changelog": "GitHub 변경 이력",
        "Google AI Blog": "Google AI 블로그",
        "Microsoft AI Blog": "Microsoft AI 블로그",
        "arXiv Database AI": "arXiv 데이터베이스 AI",
        "arXiv Network AI": "arXiv 네트워크 AI",
        "arXiv Distributed Systems AI": "arXiv 분산시스템 AI",
        "arXiv Security AI": "arXiv 보안 AI",
        "arXiv AI": "arXiv AI",
        "MIT Technology Review AI": "MIT Technology Review AI",
        "VentureBeat AI": "VentureBeat AI",
    }
    return names.get(source, source)


def _rank_tool_updates(items: list[DigestItem], limit: int) -> list[DigestItem]:
    keywords = (
        "claude",
        "anthropic",
        "openai",
        "chatgpt",
        "copilot",
        "cursor",
        "agent",
        "agents",
        "model",
        "api",
        "developer",
        "coding",
    )

    def score(item: DigestItem) -> tuple[datetime, int]:
        text = f"{item.title} {item.summary} {item.source}".lower()
        return (item.published, sum(1 for keyword in keywords if keyword in text))

    return sorted(items, key=score, reverse=True)[:limit]


def _rank_work_skill_updates(items: list[DigestItem], limit: int) -> list[DigestItem]:
    def score(item: DigestItem) -> tuple[int, datetime]:
        text = f"{item.title} {item.summary} {item.source}".lower()
        skill_score = 0
        for keyword, weight in WORK_SKILL_KEYWORDS.items():
            if keyword in text:
                skill_score += weight
        for keyword, penalty in GENERAL_STORY_KEYWORDS.items():
            if keyword in text:
                skill_score -= penalty
        return (skill_score, item.published)

    ranked = sorted(items, key=score, reverse=True)
    practical = [item for item in ranked if score(item)[0] > 0]
    return practical[:limit] if len(practical) >= limit else ranked[:limit]


def _latest_digest_items(items: list[DigestItem], limit: int) -> list[DigestItem]:
    return sorted(items, key=lambda item: item.published, reverse=True)[:limit]


def _dedupe_items(items: list[DigestItem]) -> list[DigestItem]:
    deduped: list[DigestItem] = []
    seen_urls: set[str] = set()
    for item in items:
        if item.url in seen_urls:
            continue
        seen_urls.add(item.url)
        deduped.append(item)
    return deduped


def _latest_first(items: list[SiteItem]) -> list[SiteItem]:
    return sorted(items, key=lambda item: item.published, reverse=True)


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _format_date(value: datetime) -> str:
    kst = timezone(timedelta(hours=9), name="KST")
    return value.astimezone(kst).strftime("%Y-%m-%d")


def main() -> int:
    parser = argparse.ArgumentParser(description="인공지능 마스터 타임즈 깃허브 페이지 사이트를 생성합니다.")
    parser.add_argument("--output-dir", default="public", help="Directory where index.html is written.")
    args = parser.parse_args()

    path = build_site(Path(args.output_dir), Settings.from_env())
    print(f"Built {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
