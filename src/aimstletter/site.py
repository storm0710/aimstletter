from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta, timezone
from html import escape
from pathlib import Path

from aimstletter.config import Settings
from aimstletter.fetchers import DigestItem, fetch_recent_items
from aimstletter.ranking import rank_items


def build_site(output_dir: Path, settings: Settings) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    ai_items = rank_items(fetch_recent_items(settings.feeds, settings.lookback_days), 10)
    tool_items = _rank_tool_updates(fetch_recent_items(settings.tool_feeds, 21), 10)
    html = render_homepage(ai_items, tool_items)

    path = output_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def render_homepage(ai_items: list[DigestItem], tool_items: list[DigestItem]) -> str:
    kst = timezone(timedelta(hours=9), name="KST")
    today = datetime.now(UTC).astimezone(kst).strftime("%Y년 %m월 %d일")
    hero = ai_items[0] if ai_items else None
    tool_lead = tool_items[0] if tool_items else None

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Master Times</title>
  <meta name="description" content="AI마스터 과정용 주간 AI 업데이트와 AI 툴 릴리즈 뉴스">
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
      width: min(1180px, calc(100% - 32px));
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
      max-width: 760px;
      color: var(--muted);
      font: 16px/1.6 Arial, "Noto Sans KR", sans-serif;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.45fr) minmax(280px, .8fr);
      gap: 24px;
      border-bottom: 1px solid var(--rule);
      padding: 24px 0;
    }}
    .lead-image {{
      min-height: 240px;
      background:
        linear-gradient(180deg, rgba(0,0,0,.05), rgba(0,0,0,.34)),
        url("https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1400&q=80");
      background-size: cover;
      background-position: center;
      border: 1px solid var(--rule);
      margin-bottom: 14px;
    }}
    .kicker {{
      color: var(--accent);
      font: 800 12px/1.4 Arial, "Noto Sans KR", sans-serif;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h2, h3 {{ margin: 0; letter-spacing: 0; }}
    .lead-title {{
      font-size: clamp(30px, 5vw, 54px);
      line-height: 1.02;
      margin-top: 6px;
    }}
    .summary {{
      color: #282828;
      font-size: 17px;
      line-height: 1.68;
      margin: 12px 0 0;
    }}
    .brief {{
      border-bottom: 1px solid var(--line);
      padding: 0 0 14px;
      margin-bottom: 14px;
    }}
    .brief h3 {{
      font-size: 23px;
      line-height: 1.18;
      margin: 5px 0 8px;
    }}
    .newspaper {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(320px, .72fr);
      gap: 24px;
      padding-top: 22px;
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
    .watch-links {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 18px;
      font: 700 13px/1.35 Arial, "Noto Sans KR", sans-serif;
    }}
    .watch-links a {{
      border: 1px solid var(--rule);
      padding: 9px 10px;
      text-decoration: none;
      background: #fffaf0;
    }}
    footer {{
      border-top: 3px double var(--rule);
      margin-top: 28px;
      padding-top: 12px;
      color: var(--muted);
      font: 13px/1.5 Arial, "Noto Sans KR", sans-serif;
    }}
    @media (max-width: 840px) {{
      .hero-grid, .newspaper {{
        grid-template-columns: 1fr;
      }}
      .column + .column {{
        border-left: 0;
        padding-left: 0;
      }}
      .topline {{
        flex-direction: column;
      }}
      .watch-links {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <div class="topline">
      <span>AI마스터 과정 주간판</span>
      <span>{escape(today)} · GitHub Pages Edition</span>
    </div>
    <header class="masthead">
      <h1>AI Master Times</h1>
      <p>DBA, 네트워크, 서버 운영 직군이 AI를 업무 스킬과 비즈니스 모델로 연결할 수 있도록 매주 선별한 리서치와 AI 도구 업데이트입니다.</p>
    </header>

    <section class="hero-grid" aria-label="이번 주 주요 기사">
      <article>
        <div class="lead-image" role="img" aria-label="데이터센터 서버 랙"></div>
        <div class="kicker">Lead Story · Infra AI</div>
        {_render_lead(hero)}
      </article>
      <aside>
        <div class="kicker">Tool Watch</div>
        {_render_tool_lead(tool_lead)}
        <nav class="watch-links" aria-label="AI 도구 공식 업데이트">
          <a href="https://www.anthropic.com/news">Claude</a>
          <a href="https://openai.com/news/">OpenAI</a>
          <a href="https://github.blog/changelog/label/copilot/">GitHub Copilot</a>
          <a href="https://cursor.com/changelog">Cursor</a>
        </nav>
      </aside>
    </section>

    <section class="newspaper" aria-label="주간 업데이트">
      <div class="column">
        <h2 class="section-title">현장 AI 스킬 · 상위 5개</h2>
        {_render_articles(ai_items[:5])}
        <h2 class="section-title">기타 AI 동향 · 하위 5개</h2>
        {_render_articles(ai_items[5:10])}
      </div>
      <aside class="column">
        <h2 class="section-title">Claude와 AI 툴 업데이트</h2>
        <div class="tool-list">
          {_render_tool_items(tool_items[:10])}
        </div>
      </aside>
    </section>
    <footer>
      자동 생성: GitHub Actions · 출처 링크를 눌러 원문을 확인하세요. Cursor는 공식 changelog 링크를 고정 노출하고, RSS가 안정적인 도구는 최신 글을 자동 수집합니다.
    </footer>
  </main>
</body>
</html>
"""


def _render_lead(item: DigestItem | None) -> str:
    if not item:
        return '<h2 class="lead-title">이번 주 수집된 주요 항목이 없습니다.</h2>'
    return (
        f'<h2 class="lead-title"><a href="{escape(item.url)}">{escape(item.title)}</a></h2>'
        f'<p class="summary">{escape(_clip(item.summary, 420))}</p>'
        f'<div class="meta">{escape(item.source)} · {_format_date(item.published)}</div>'
    )


def _render_tool_lead(item: DigestItem | None) -> str:
    if not item:
        return '<div class="brief"><h3>AI 도구 업데이트를 기다리는 중입니다.</h3></div>'
    return (
        '<div class="brief">'
        f'<h3><a href="{escape(item.url)}">{escape(item.title)}</a></h3>'
        f'<p>{escape(_clip(item.summary, 220))}</p>'
        f'<div class="meta">{escape(item.source)} · {_format_date(item.published)}</div>'
        "</div>"
    )


def _render_articles(items: list[DigestItem]) -> str:
    if not items:
        return '<p class="summary">표시할 항목이 없습니다.</p>'
    return "\n".join(
        (
            '<article class="article">'
            f'<div class="kicker">{escape(item.kind)} · {escape(item.source)}</div>'
            f'<h3><a href="{escape(item.url)}">{escape(item.title)}</a></h3>'
            f'<p>{escape(_clip(item.summary, 300))}</p>'
            f'<div class="meta">{_format_date(item.published)}</div>'
            "</article>"
        )
        for item in items
    )


def _render_tool_items(items: list[DigestItem]) -> str:
    if not items:
        return '<p class="summary">표시할 도구 업데이트가 없습니다.</p>'
    return "\n".join(
        (
            '<article class="tool-item">'
            f'<div class="kicker">{escape(item.source)}</div>'
            f'<h3><a href="{escape(item.url)}">{escape(item.title)}</a></h3>'
            f'<p>{escape(_clip(item.summary, 210))}</p>'
            f'<div class="meta">{_format_date(item.published)}</div>'
            "</article>"
        )
        for item in items
    )


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

    def score(item: DigestItem) -> tuple[int, datetime]:
        text = f"{item.title} {item.summary} {item.source}".lower()
        return (sum(1 for keyword in keywords if keyword in text), item.published)

    return sorted(items, key=score, reverse=True)[:limit]


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _format_date(value: datetime) -> str:
    kst = timezone(timedelta(hours=9), name="KST")
    return value.astimezone(kst).strftime("%Y-%m-%d")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the AI Master Times GitHub Pages site.")
    parser.add_argument("--output-dir", default="public", help="Directory where index.html is written.")
    args = parser.parse_args()

    path = build_site(Path(args.output_dir), Settings.from_env())
    print(f"Built {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
