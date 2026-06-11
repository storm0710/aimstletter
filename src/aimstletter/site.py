from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import sys
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
    detail: str
    key_points: tuple[str, ...]
    tags: tuple[str, ...]
    comparisons: tuple[str, ...] = ()
    glossary: tuple[str, ...] = ()


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
    html = render_homepage(ai_items, tool_items, analytics_html=_render_analytics(settings))

    path = output_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    _write_secondary_pages(output_dir, ai_items, tool_items, _render_analytics(settings))
    return path


def render_homepage(
    ai_items: list[SiteItem],
    tool_items: list[SiteItem],
    analytics_html: str = "",
) -> str:
    kst = timezone(timedelta(hours=9), name="KST")
    today = datetime.now(UTC).astimezone(kst).strftime("%Y년 %m월 %d일")
    infra_items = _latest_first(ai_items[:5])
    other_items = _latest_first(ai_items[5:10])
    latest_tool_items = _latest_first(tool_items[:10])
    return _render_dashboard_homepage(
        today=today,
        infra_items=infra_items,
        other_items=other_items,
        latest_tool_items=latest_tool_items,
        analytics_html=analytics_html,
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Master Times</title>
  <meta name="description" content="인공지능 마스터 과정용 주간 인공지능 업데이트와 도구 출시 소식">
  {analytics_html}
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
      grid-template-columns: 230px minmax(0, 1fr);
      gap: 28px;
      padding-top: 0;
      margin-top: 28px;
      border-top: 1px solid var(--rule);
      align-items: start;
    }}
    .content-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 28px;
      min-width: 0;
    }}
    .column {{
      min-width: 0;
      padding-top: 22px;
    }}
    .content-grid .column + .column {{
      border-left: 1px solid var(--rule);
      padding-left: 24px;
    }}
    .toc-column {{
      border-left: 0;
      padding-left: 0;
      position: sticky;
      top: 18px;
    }}
    .toc-list {{
      display: grid;
      gap: 10px;
      font: 700 14px/1.45 Arial, "Noto Sans KR", sans-serif;
    }}
    .toc-list a {{
      border: 1px solid var(--line);
      background: #fffaf0;
      display: grid;
      gap: 3px;
      padding: 10px 11px;
      text-decoration: none;
    }}
    .toc-list a:hover,
    .toc-list a:focus-visible {{
      border-color: var(--rule);
      outline: 0;
    }}
    .toc-number {{
      color: var(--accent);
      font: 800 12px/1.3 Arial, "Noto Sans KR", sans-serif;
    }}
    .toc-label {{
      font-size: 15px;
    }}
    .toc-desc {{
      color: var(--muted);
      font: 12px/1.45 Arial, "Noto Sans KR", sans-serif;
    }}
    .toc-note {{
      color: var(--muted);
      font: 13px/1.55 Arial, "Noto Sans KR", sans-serif;
      margin: 12px 0 0;
    }}
    .section-title {{
      border-bottom: 2px solid var(--rule);
      padding-bottom: 8px;
      margin-bottom: 14px;
      font-size: 24px;
      line-height: 1.2;
      min-height: 39px;
      display: flex;
      align-items: flex-start;
    }}
    .article {{
      border-bottom: 1px solid var(--line);
      min-height: 316px;
      padding: 14px 0 16px;
    }}
    .section-title + .article,
    .section-title + .tool-list .tool-item:first-child {{
      padding-top: 0;
    }}
    .article h3 {{
      font-size: 22px;
      line-height: 1.22;
    }}
    .title-date {{
      color: var(--muted);
      font: 700 13px/1.35 Arial, "Noto Sans KR", sans-serif;
      white-space: nowrap;
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
      gap: 0;
    }}
    .tool-item {{
      border-bottom: 1px solid var(--line);
      min-height: 316px;
      padding: 14px 0 16px;
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
      .newspaper,
      .content-grid {{
        grid-template-columns: 1fr;
      }}
      .content-grid .column + .column {{
        border-left: 0;
        padding-left: 0;
      }}
      .toc-column {{
        position: static;
      }}
      .article,
      .tool-item {{
        min-height: 0;
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
      <nav class="column toc-column" aria-label="상세 목차">
        <h2 class="section-title">목차</h2>
        <div class="toc-list">
          <a href="work-skills/"><span class="toc-number">1.</span><span class="toc-label">업무 AI 스킬 업데이트</span><span class="toc-desc">DBA·네트워크·서버 업무 적용 사례</span></a>
          <a href="tools/"><span class="toc-number">2.</span><span class="toc-label">Claude와 AI 도구 업데이트</span><span class="toc-desc">Claude·OpenAI·Copilot 최신 변경</span></a>
        </div>
        <p class="toc-note">번호를 눌러 게시판으로 이동하고, 항목 제목을 클릭하면 번역된 상세 설명과 원문 링크를 확인할 수 있습니다.</p>
      </nav>
      <div class="content-grid">
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
      </div>
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
            f'<h3><a href="{escape(_detail_href(item))}">{escape(item.title)} '
            f'<span class="title-date">({_format_date(item.published)})</span></a></h3>'
            f'<p>{escape(_clip(item.summary, 300))}</p>'
            f"{_render_key_points(item)}"
            f"{_render_tags(item)}"
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
            f'<h3><a href="{escape(_detail_href(item))}">{escape(item.title)} '
            f'<span class="title-date">({_format_date(item.published)})</span></a></h3>'
            f'<p>{escape(_clip(item.summary, 210))}</p>'
            f"{_render_key_points(item)}"
            f"{_render_tags(item)}"
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


def _render_editorial_homepage(
    today: str,
    infra_items: list[SiteItem],
    other_items: list[SiteItem],
    latest_tool_items: list[SiteItem],
    analytics_html: str,
) -> str:
    all_items = [*infra_items, *other_items, *latest_tool_items]
    lead_item = (infra_items or other_items or latest_tool_items)[0] if all_items else None
    lead_summary = lead_item.summary if lead_item else "이번 주 AI 업무 업데이트를 선별해 보여줍니다."
    insight_cards = _render_smart_insight_cards(all_items)
    logo_roll = _render_logo_roll()
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Master Times</title>
  <meta name="description" content="AI Master Times 주간 AI 업무 업데이트">
  {analytics_html}
  <style>
    :root {{
      color-scheme: light;
      --bg: #ffffff;
      --ink: #111111;
      --muted: #767676;
      --line: #e8e8e4;
      --soft: #f6f6f3;
      --panel: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, "Noto Sans KR", sans-serif;
    }}
    a {{ color: inherit; text-decoration: none; }}
    .page {{
      width: min(1180px, calc(100% - 34px));
      margin: 0 auto;
      min-height: 100vh;
    }}
    .nav {{
      height: 58px;
      display: flex;
      align-items: center;
      border-bottom: 1px solid var(--line);
      font-size: 12px;
      color: #555;
    }}
    .brand {{
      font-weight: 900;
      margin-right: auto;
      color: var(--ink);
    }}
    .nav-links {{
      display: flex;
      gap: 26px;
      align-items: center;
      justify-content: center;
      flex: 1;
    }}
    .nav-actions {{
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 18px;
    }}
    .button {{
      min-height: 32px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0 14px;
      background: #050505;
      color: #fff;
      border-radius: 5px;
      font-weight: 800;
      font-size: 12px;
    }}
    .hero {{
      min-height: 720px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      padding: 70px 0 0;
    }}
    .hero h1 {{
      max-width: 720px;
      margin: 0;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(38px, 5.8vw, 78px);
      line-height: .98;
      font-weight: 700;
      letter-spacing: 0;
    }}
    .hero-image {{
      align-self: end;
      margin-top: 64px;
      overflow: hidden;
      border-radius: 20px;
      min-height: clamp(260px, 34vw, 430px);
      background:
        linear-gradient(rgba(0,0,0,.028) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,.024) 1px, transparent 1px),
        #f7f7f4;
      background-size: 34px 34px;
      border: 1px solid var(--line);
      display: grid;
      grid-template-columns: minmax(260px, .86fr) minmax(320px, 1.14fr);
      gap: 10px;
      padding: clamp(22px, 3.2vw, 42px);
      align-items: stretch;
    }}
    .talent-card {{
      background: rgba(255,255,255,.72);
      border: 1px solid rgba(0,0,0,.08);
      padding: clamp(24px, 3vw, 38px);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 280px;
    }}
    .talent-logo {{
      display: inline-flex;
      gap: 6px;
      align-items: baseline;
      font-family: Arial, "Noto Sans KR", sans-serif;
      font-size: clamp(24px, 3vw, 36px);
      font-weight: 900;
      letter-spacing: -.01em;
    }}
    .talent-logo .sk {{ color: #e21424; }}
    .talent-logo .ax {{ color: #ff8200; }}
    .talent-title {{
      margin: 58px 0 0;
      color: #4f5f9a;
      font-family: Arial, "Noto Sans KR", sans-serif;
      font-size: clamp(38px, 5vw, 68px);
      line-height: .98;
      font-weight: 900;
      letter-spacing: 0;
    }}
    .talent-copy {{
      margin: 28px 0 0;
      color: #111;
      font-family: "Noto Sans KR", Arial, sans-serif;
      font-size: clamp(26px, 3.3vw, 46px);
      line-height: 1.22;
      font-weight: 900;
      letter-spacing: 0;
    }}
    .criteria-card {{
      border: 1px solid #111;
      border-radius: 42px;
      background: rgba(255,255,255,.8);
      padding: clamp(28px, 4vw, 54px);
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}
    .criteria-card h2 {{
      margin: 0 0 28px;
      color: #111;
      font-family: "Noto Sans KR", Arial, sans-serif;
      font-size: clamp(24px, 2.7vw, 38px);
      line-height: 1.18;
      letter-spacing: 0;
      font-weight: 800;
    }}
    .criteria-card ul {{
      margin: 0;
      padding-left: 1.1em;
      display: grid;
      gap: 10px;
      color: #111;
      font-family: "Noto Sans KR", Arial, sans-serif;
      font-size: clamp(18px, 2.05vw, 30px);
      line-height: 1.25;
      letter-spacing: 0;
      font-weight: 500;
    }}
    .criteria-card strong {{
      font-weight: 900;
    }}
    .intro-row {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(240px, 420px);
      gap: 32px;
      align-items: end;
      padding: 34px 0 36px;
      border-bottom: 1px solid var(--line);
    }}
    .intro-copy {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
      max-width: 620px;
    }}
    .date {{
      color: #9a9a9a;
      font-size: 12px;
      text-align: right;
    }}
    .logo-roll {{
      overflow: hidden;
      border-bottom: 1px solid var(--line);
      padding: 24px 0;
    }}
    .logo-track {{
      display: flex;
      width: max-content;
      gap: 54px;
      animation: roll 24s linear infinite;
      color: #2f2f2f;
      font-family: Georgia, "Times New Roman", serif;
      font-size: 15px;
      letter-spacing: .08em;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    @keyframes roll {{
      from {{ transform: translateX(0); }}
      to {{ transform: translateX(-50%); }}
    }}
    .insights {{
      padding: 64px 0 90px;
    }}
    .section-kicker {{
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 10px;
    }}
    .insights h2 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(26px, 3vw, 44px);
      line-height: 1.08;
      letter-spacing: 0;
    }}
    .insights-header {{
      max-width: 620px;
      margin-bottom: 34px;
    }}
    .insights-header p {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }}
    .insight-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
    }}
    .insight-grid.has-selection {{
      grid-template-columns: minmax(300px, .92fr) minmax(360px, 1.08fr);
      gap: 28px;
      align-items: start;
    }}
    .insight-list {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .insight-grid.has-selection .insight-list {{
      grid-template-columns: 1fr;
      gap: 0;
      border-top: 1px solid var(--line);
    }}
    .insight-card {{
      width: 100%;
      border: 1px solid var(--line);
      background: var(--panel);
      min-height: 230px;
      padding: 28px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      text-align: left;
      cursor: pointer;
      color: var(--ink);
      font: inherit;
    }}
    .insight-grid.has-selection .insight-card {{
      border: 0;
      border-bottom: 1px solid var(--line);
      background: transparent;
      min-height: 112px;
      padding: 22px 0;
      display: grid;
      grid-template-columns: 36px minmax(0, 1fr);
      gap: 14px;
      justify-content: initial;
    }}
    .insight-card:hover,
    .insight-card.is-active {{
      background: #fbfbf8;
    }}
    .card-icon {{
      width: 22px;
      height: 22px;
      border: 1px solid #111;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-size: 11px;
      margin-bottom: 26px;
      flex: 0 0 auto;
    }}
    .insight-grid.has-selection .card-icon {{
      margin-top: 1px;
      margin-bottom: 0;
    }}
    .card-title {{
      display: block;
      margin: 0 0 10px;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: 22px;
      letter-spacing: 0;
      font-weight: 700;
    }}
    .insight-grid.has-selection .card-title {{
      margin-bottom: 6px;
      font-size: 18px;
    }}
    .insight-card p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.58;
    }}
    .insight-grid.has-selection .insight-card p {{
      font-size: 12px;
      line-height: 1.52;
    }}
    .insight-detail {{
      min-height: 520px;
      border: 1px solid var(--line);
      background:
        linear-gradient(rgba(0,0,0,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,.028) 1px, transparent 1px),
        #f7f7f4;
      background-size: 32px 32px;
      padding: 34px;
      display: none;
      flex-direction: column;
      justify-content: space-between;
      position: sticky;
      top: 24px;
    }}
    .insight-grid.has-selection .insight-detail {{
      display: flex;
    }}
    .detail-number {{
      width: 26px;
      height: 26px;
      border: 1px solid #111;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-size: 12px;
      margin-bottom: 42px;
      background: #fff;
    }}
    .insight-detail h3 {{
      margin: 0 0 16px;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(30px, 4vw, 54px);
      line-height: .98;
      letter-spacing: 0;
    }}
    .detail-meta {{
      margin-bottom: 16px;
      color: #777;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}
    .detail-summary,
    .detail-copy {{
      margin: 0;
      color: #565656;
      font-size: 14px;
      line-height: 1.68;
      max-width: 620px;
    }}
    .detail-summary {{
      color: #222;
      font-weight: 700;
      margin-bottom: 18px;
    }}
    .detail-points {{
      display: grid;
      gap: 8px;
      margin: 26px 0 0;
      padding: 0;
      list-style: none;
      max-width: 620px;
    }}
    .detail-points li {{
      border-top: 1px solid rgba(0,0,0,.12);
      padding-top: 8px;
      color: #444;
      font-size: 13px;
      line-height: 1.55;
    }}
    .detail-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 34px;
    }}
    .detail-tag {{
      border: 1px solid var(--line);
      background: #fff;
      padding: 6px 8px;
      color: #111;
      font-size: 11px;
      font-weight: 800;
    }}
    .mini-link,
    .detail-link {{
      color: #111;
      font-size: 12px;
      font-weight: 800;
    }}
    .detail-link {{
      margin-top: 42px;
      align-self: flex-start;
    }}
    .footer {{
      border-top: 1px solid var(--line);
      min-height: 82px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--muted);
      font-size: 12px;
    }}
    @media (max-width: 760px) {{
      .nav-links {{ display: none; }}
      .hero {{ min-height: auto; padding-top: 48px; }}
      .hero-image {{ grid-template-columns: 1fr; border-radius: 14px; }}
      .talent-card {{ min-height: 240px; }}
      .criteria-card {{ border-radius: 28px; }}
      .intro-row,
      .insight-grid {{
        grid-template-columns: 1fr;
      }}
      .insight-list,
      .insight-grid.has-selection,
      .insight-grid.has-selection .insight-list {{ grid-template-columns: 1fr; }}
      .insight-detail {{ position: static; min-height: 360px; }}
      .date {{ text-align: left; }}
      .insight-card {{ min-height: 210px; }}
      .insight-grid.has-selection .insight-card {{ min-height: 112px; }}
      .footer {{ align-items: flex-start; flex-direction: column; gap: 12px; padding: 22px 0; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header class="nav">
      <a class="brand" href="#">AI MASTER TIMES</a>
      <nav class="nav-links" aria-label="Primary">
        <a href="#insights">업무 AI</a>
        <a href="tools/">AI 도구</a>
        <a href="work-skills/">상세 목록</a>
        <a href="#insights">Smart Insights</a>
      </nav>
      <div class="nav-actions">
        <a href="work-skills/">Archive</a>
        <a class="button" href="#insights">Read This Week</a>
      </div>
    </header>
    <section class="hero" aria-label="Hero">
      <h1>AI MASTER TIMES</h1>
      <section class="hero-image" aria-label="AI Talent Lab pass criteria">
        <div class="talent-card">
          <div class="talent-logo"><span class="sk">SK</span><span class="ax">AX</span></div>
          <div>
            <div class="talent-title">AI Talent Lab</div>
            <p class="talent-copy">당신의 AI 역량을<br>성장시켜보세요</p>
          </div>
        </div>
        <div class="criteria-card">
          <h2>[통과기준]</h2>
          <ul>
            <li><strong>Business Logic</strong> 포함(상용툴과 차이점)</li>
            <li><strong>AI AGENT</strong> 포함(AI 단순호출 불가)</li>
            <li>시연 동영상 편집(5분내로 편집)</li>
            <li>AI 면접 통과</li>
          </ul>
        </div>
      </section>
      <div class="intro-row">
        <p class="intro-copy">{escape(_editorial_intro_copy(lead_summary))}</p>
        <div class="date">{escape(today)} · curated weekly for AI Master teams</div>
      </div>
    </section>
    <section class="logo-roll" aria-label="Source roll">
      <div class="logo-track">{logo_roll}{logo_roll}</div>
    </section>
    <section class="insights" id="insights">
      <div class="insights-header">
        <div class="section-kicker">Smart Insights</div>
        <h2>이번 주 AI 업데이트를 업무 관점으로 정리했습니다.</h2>
        <p>홀수 카드는 에이전트 운영과 엔지니어링 트렌드, 짝수 카드는 AI 제품 제작에 필요한 프론트·디자인·백엔드·데이터 도구를 함께 정리했습니다.</p>
      </div>
      <div class="insight-grid" data-insight-grid>
        {insight_cards}
      </div>
    </section>
    <footer class="footer">
      <strong>AI MASTER TIMES</strong>
      <span>Work Skills · AI Tools · Weekly Briefing · Source Links</span>
      <span>© AI Master Times</span>
    </footer>
  </main>
</body>
</html>
"""


def _render_romer_homepage(
    today: str,
    infra_items: list[SiteItem],
    other_items: list[SiteItem],
    latest_tool_items: list[SiteItem],
    analytics_html: str,
) -> str:
    all_items = [*infra_items, *other_items, *latest_tool_items]
    automation_count = _count_keyword_items(
        all_items, ("agent", "automation", "workflow", "copilot", "codex")
    )
    ops_count = _count_keyword_items(
        all_items, ("database", "network", "server", "security", "kubernetes", "cloud")
    )
    lead_item = (infra_items or other_items or latest_tool_items)[0] if all_items else None
    lead_title = lead_item.title if lead_item else "이번 주 AI 업데이트"
    lead_summary = lead_item.summary if lead_item else "표시할 업데이트가 없습니다."
    rows = _render_dashboard_rows([*infra_items, *other_items[:2]], "work")
    tasks = _render_command_tasks(latest_tool_items[:4])
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Master Command Dashboard</title>
  <meta name="description" content="AI Master 주간 AI 업무 업데이트 command dashboard">
  {analytics_html}
  <style>
    :root {{
      color-scheme: dark;
      --bg: #030507;
      --panel: #080b10;
      --panel-2: #0c1017;
      --ink: #f4f7fb;
      --muted: #8b94a7;
      --line: rgba(177, 194, 224, .16);
      --line-strong: rgba(210, 224, 250, .28);
      --blue: #7aa7ff;
      --lime: #b8ff72;
      --orange: #ffb86b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 50% 0, rgba(122,167,255,.12), transparent 0 34%),
        var(--bg);
      color: var(--ink);
      font-family: Arial, "Noto Sans KR", sans-serif;
    }}
    a {{ color: inherit; text-decoration: none; }}
    .site {{ width: min(1160px, calc(100% - 34px)); margin: 0 auto; padding: 16px 0 72px; }}
    .nav {{
      height: 46px; display: flex; align-items: center; gap: 24px;
      border-bottom: 1px solid var(--line); color: #c3ccda; font-size: 12px; font-weight: 700;
    }}
    .logo {{ display: inline-flex; align-items: center; gap: 8px; margin-right: 24px; color: #fff; font-weight: 900; }}
    .logo-mark {{ width: 14px; height: 14px; border-radius: 3px; background: linear-gradient(135deg, var(--lime), var(--blue)); }}
    .nav-links {{ display: flex; align-items: center; gap: 18px; flex: 1; }}
    .nav a.active {{ color: var(--blue); }}
    .nav-actions {{ margin-left: auto; display: flex; align-items: center; gap: 14px; }}
    .btn {{
      min-height: 32px; display: inline-flex; align-items: center; justify-content: center;
      border: 1px solid var(--line-strong); padding: 0 13px; font-size: 12px; font-weight: 900;
    }}
    .btn.primary {{ background: #fff; color: #05070b; border-color: #fff; }}
    .hero {{ padding: 74px 0 28px; }}
    .hero h1 {{ margin: 0; max-width: 720px; font-size: clamp(44px, 7vw, 78px); line-height: .91; letter-spacing: 0; }}
    .hero p {{ max-width: 520px; margin: 18px 0 0; color: var(--muted); font-size: 14px; line-height: 1.45; }}
    .hero-actions {{ display: flex; gap: 12px; margin-top: 28px; }}
    .mockup-wrap {{
      margin-top: 12px; display: grid; grid-template-columns: minmax(0, 1fr) 286px; gap: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.012));
      border: 1px solid var(--line); box-shadow: 0 30px 100px rgba(0,0,0,.5); padding: 14px;
    }}
    .command {{ display: grid; grid-template-columns: 150px minmax(0,1fr); min-height: 432px; border: 1px solid var(--line); background: #070a0f; }}
    .command-side {{ border-right: 1px solid var(--line); padding: 16px 12px; color: var(--muted); font-size: 11px; }}
    .command-side strong {{ display: block; color: #fff; margin-bottom: 14px; }}
    .side-link {{ display: block; padding: 8px 7px; border: 1px solid transparent; }}
    .side-link.active {{ color: #fff; background: rgba(122,167,255,.10); border-color: var(--line); }}
    .command-main {{ padding: 16px; }}
    .metric-strip {{ display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 10px; }}
    .mini-metric {{ border: 1px solid var(--line); background: #090d14; padding: 11px; min-height: 72px; }}
    .mini-metric span {{ color: var(--muted); display: block; font-size: 10px; font-weight: 800; text-transform: uppercase; }}
    .mini-metric strong {{ display: block; margin-top: 8px; color: #fff; font-size: 20px; }}
    .mini-metric em {{ color: var(--lime); font-size: 10px; font-style: normal; }}
    .signal-chart {{
      margin-top: 16px; height: 154px; border: 1px solid var(--line);
      background: linear-gradient(rgba(122,167,255,.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(122,167,255,.06) 1px, transparent 1px), #05080d;
      background-size: 40px 32px; position: relative; overflow: hidden;
    }}
    .signal-chart::before {{
      content: ""; position: absolute; left: 16px; right: 16px; bottom: 36px; height: 80px;
      background: linear-gradient(174deg, transparent 0 18%, rgba(122,167,255,.9) 19% 20%, transparent 21% 100%);
    }}
    .signal-chart::after {{
      content: ""; position: absolute; right: 18px; bottom: 34px; width: 1px; height: 76px;
      background: var(--blue); box-shadow: 0 0 18px rgba(122,167,255,.7);
    }}
    .command-grid {{ margin-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
    .command-card {{ border: 1px solid var(--line); background: #090d14; padding: 12px; min-height: 84px; }}
    .command-card h3 {{ margin: 0 0 7px; color: #fff; font-size: 13px; }}
    .command-card p {{ margin: 0; color: var(--muted); font-size: 11px; line-height: 1.45; }}
    .ops-panel {{ border: 1px solid var(--line); background: #070a0f; min-height: 432px; padding: 16px; }}
    .ops-panel h2 {{ margin: 0 0 14px; color: #fff; font-size: 14px; }}
    .task-list {{ display: grid; gap: 12px; }}
    .task {{ border-bottom: 1px solid var(--line); padding-bottom: 12px; }}
    .task strong {{ display: block; color: #fff; font-size: 12px; line-height: 1.4; }}
    .task span {{ display: block; margin-top: 5px; color: var(--muted); font-size: 11px; line-height: 1.45; }}
    .focus-line {{ text-align: center; margin: 26px auto 0; max-width: 650px; color: #fff; font-size: clamp(22px, 3vw, 34px); line-height: 1.03; font-weight: 900; }}
    .data-section {{ margin-top: 42px; border-top: 1px solid var(--line); padding-top: 22px; }}
    .section-head {{ display: flex; justify-content: space-between; gap: 18px; align-items: end; margin-bottom: 14px; }}
    .section-head h2 {{ margin: 0; color: #fff; font-size: 18px; }}
    .section-head p {{ margin: 0; color: var(--muted); font-size: 12px; }}
    .update-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; border: 1px solid var(--line); background: #070a0f; }}
    .update-table th {{ color: var(--muted); font-size: 10px; text-align: left; text-transform: uppercase; padding: 12px 8px; border-bottom: 1px solid var(--line); }}
    .update-table td {{ padding: 14px 8px; border-bottom: 1px solid var(--line); vertical-align: top; font-size: 13px; line-height: 1.45; }}
    .update-title {{ display: block; color: #fff; font-size: 14px; font-weight: 900; line-height: 1.35; margin-bottom: 4px; }}
    .update-summary {{ color: var(--muted); font-size: 12px; }}
    .status {{ display: inline-flex; align-items: center; gap: 6px; color: var(--lime); font-weight: 800; white-space: nowrap; }}
    .status::before {{ content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }}
    .badge {{ display: inline-flex; align-items: center; min-height: 22px; padding: 0 7px; border: 1px solid rgba(122,167,255,.32); background: rgba(122,167,255,.08); color: var(--blue); font-size: 11px; font-weight: 800; }}
    .action-btn {{ display: inline-flex; align-items: center; justify-content: center; min-height: 30px; padding: 0 10px; background: #fff; color: #05070b; font-size: 11px; font-weight: 900; text-transform: uppercase; }}
    @media (max-width: 960px) {{ .mockup-wrap, .command {{ grid-template-columns: 1fr; }} .command-side {{ border-right: 0; border-bottom: 1px solid var(--line); }} .metric-strip, .command-grid {{ grid-template-columns: 1fr 1fr; }} .nav-links {{ display: none; }} }}
    @media (max-width: 640px) {{ .hero {{ padding-top: 46px; }} .mockup-wrap {{ padding: 10px; }} .metric-strip, .command-grid {{ grid-template-columns: 1fr; }} .update-table, .update-table tbody, .update-table tr, .update-table td {{ display: block; width: 100%; }} .update-table thead {{ display: none; }} }}
  </style>
</head>
<body>
  <main class="site">
    <header class="nav">
      <a class="logo" href="#"><span class="logo-mark"></span><span>AIMST</span></a>
      <nav class="nav-links" aria-label="Primary">
        <a class="active" href="#">Platform</a><a href="work-skills/">Dashboards</a><a href="tools/">Automation</a><a href="#updates">Reports</a><a href="tools/">Resources</a><a href="#updates">Contact</a>
      </nav>
      <div class="nav-actions"><a href="#updates">Login</a><a class="btn primary" href="tools/">Start here</a></div>
    </header>
    <section class="hero">
      <h1>The command dashboard for focused AI teams</h1>
      <p>Turn scattered AI signals, tool releases, and operating notes into one calm weekly command center for practical teams.</p>
      <div class="hero-actions"><a class="btn primary" href="#updates">Get started</a><a class="btn" href="tools/">Book a demo</a></div>
    </section>
    <section class="mockup-wrap" aria-label="AI command dashboard preview">
      <div class="command">
        <aside class="command-side"><strong>AI OPS</strong><span class="side-link active">Overview</span><span class="side-link">Signals</span><span class="side-link">Operations</span><span class="side-link">AI Tools</span><span class="side-link">Models</span><span class="side-link">Reports</span><span class="side-link">Automations</span></aside>
        <div class="command-main">
          <div class="metric-strip">
            <div class="mini-metric"><span>Work signals</span><strong>{len(infra_items)}</strong><em>active</em></div>
            <div class="mini-metric"><span>Automation</span><strong>{automation_count}</strong><em>agent-ready</em></div>
            <div class="mini-metric"><span>Ops layer</span><strong>{ops_count}</strong><em>tracked</em></div>
            <div class="mini-metric"><span>AI tools</span><strong>{len(latest_tool_items)}</strong><em>fresh</em></div>
          </div>
          <div class="signal-chart" aria-hidden="true"></div>
          <div class="command-grid">
            <div class="command-card"><h3>{escape(_clip(lead_title, 72))}</h3><p>{escape(_clip(lead_summary, 150))}</p></div>
            <div class="command-card"><h3>Target workflow</h3><p>Prioritize database, network, server, and tool updates that can become training or operating routines.</p></div>
          </div>
        </div>
      </div>
      <aside class="ops-panel"><h2>Team briefing</h2><div class="task-list">{tasks}</div></aside>
    </section>
    <p class="focus-line">Operating rhythm, simplified. The architecture of a focused AI team.</p>
    <section class="data-section" id="updates">
      <div class="section-head"><h2>Weekly signal queue</h2><p>{escape(today)} · automatically collected from trusted feeds</p></div>
      <table class="update-table"><thead><tr><th style="width:42%">Update Name</th><th style="width:19%">Status</th><th style="width:23%">Signal</th><th style="width:16%">Action</th></tr></thead><tbody>{rows}</tbody></table>
    </section>
  </main>
</body>
</html>
"""


def _render_dashboard_homepage(
    today: str,
    infra_items: list[SiteItem],
    other_items: list[SiteItem],
    latest_tool_items: list[SiteItem],
    analytics_html: str,
) -> str:
    return _render_editorial_homepage(today, infra_items, other_items, latest_tool_items, analytics_html)

    all_items = [*infra_items, *other_items, *latest_tool_items]
    automation_count = _count_keyword_items(all_items, ("agent", "automation", "workflow", "copilot", "codex"))
    ops_count = _count_keyword_items(all_items, ("database", "network", "server", "security", "kubernetes", "cloud"))
    tool_count = len(latest_tool_items)
    lead_item = (infra_items or other_items or latest_tool_items)[0] if all_items else None
    lead_title = lead_item.title if lead_item else "이번 주 AI 업데이트"
    lead_summary = lead_item.summary if lead_item else "표시할 업데이트가 없습니다."
    radar_nodes = _render_radar_nodes(all_items[:6])
    work_rows = _render_dashboard_rows([*infra_items, *other_items[:3]], "work")
    tool_cards = _render_dashboard_tool_cards(latest_tool_items[:5])

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Master Dashboard</title>
  <meta name="description" content="AI Master 과정 주간 AI 업무 업데이트 대시보드">
  {analytics_html}
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f7fb;
      --panel: #ffffff;
      --nav: #eaf1fb;
      --ink: #101828;
      --muted: #667085;
      --line: #d9e2ef;
      --soft: #f7faff;
      --brand: #050b18;
      --accent: #087443;
      --warn: #b54708;
      --danger: #b42318;
      --blue: #175cd3;
      --shadow: 0 12px 30px rgba(16, 24, 40, .08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, "Noto Sans KR", sans-serif;
    }}
    a {{ color: inherit; text-decoration: none; }}
    .app-shell {{
      min-height: 100vh;
      display: grid;
      grid-template-columns: 236px minmax(0, 1fr);
    }}
    .sidebar {{
      background: var(--nav);
      border-right: 1px solid var(--line);
      padding: 22px 16px;
      display: flex;
      flex-direction: column;
      gap: 22px;
      min-height: 100vh;
    }}
    .brand h1 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    .brand p {{
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .nav-list {{
      display: grid;
      gap: 8px;
    }}
    .nav-item {{
      display: flex;
      align-items: center;
      gap: 10px;
      min-height: 42px;
      padding: 0 12px;
      border-radius: 4px;
      color: #344054;
      font-size: 14px;
      font-weight: 700;
    }}
    .nav-item.active {{
      background: var(--brand);
      color: #ffffff;
    }}
    .nav-icon {{
      width: 17px;
      height: 17px;
      display: grid;
      place-items: center;
      border: 1px solid currentColor;
      border-radius: 3px;
      font-size: 10px;
      line-height: 1;
    }}
    .sidebar-footer {{
      margin-top: auto;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    .main {{
      min-width: 0;
    }}
    .topbar {{
      height: 56px;
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      gap: 18px;
      padding: 0 24px;
    }}
    .topbar h2 {{
      margin: 0;
      font-size: 18px;
      white-space: nowrap;
    }}
    .search {{
      flex: 1;
      max-width: 520px;
      height: 34px;
      border: 1px solid #edf1f7;
      background: #f3f6fb;
      color: var(--muted);
      display: flex;
      align-items: center;
      padding: 0 12px;
      font-size: 12px;
    }}
    .top-actions {{
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 12px;
      color: #344054;
      font-size: 15px;
    }}
    .avatar {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #ffd8bf;
      border: 1px solid #ffb088;
    }}
    .dashboard {{
      padding: 26px;
      display: grid;
      gap: 24px;
    }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.7fr) minmax(280px, .85fr);
      gap: 24px;
    }}
    .radar-panel,
    .metric-card,
    .table-panel,
    .tool-panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
    }}
    .radar-panel {{
      min-height: 408px;
      padding: 26px;
      position: relative;
      overflow: hidden;
    }}
    .panel-title {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      margin-bottom: 14px;
    }}
    .panel-title h3 {{
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
    }}
    .panel-title span {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    .radar-map {{
      position: relative;
      min-height: 326px;
      background:
        linear-gradient(rgba(16,24,40,.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(16,24,40,.045) 1px, transparent 1px),
        radial-gradient(circle at 22% 28%, rgba(23,92,211,.08), transparent 0 1px, transparent 2px),
        radial-gradient(circle at 76% 64%, rgba(8,116,67,.08), transparent 0 1px, transparent 2px),
        #fbfdff;
      background-size: 34px 34px, 34px 34px, 100% 100%, 100% 100%, auto;
      border: 1px solid #e4ebf5;
      overflow: hidden;
    }}
    .radar-map::before,
    .radar-map::after {{
      content: "";
      position: absolute;
      inset: 26px;
      border: 1px solid rgba(16,24,40,.08);
      pointer-events: none;
      transform: none;
    }}
    .radar-map::after {{
      inset: 64px 92px 74px 72px;
      border-color: rgba(23,92,211,.10);
    }}
    .radar-node {{
      position: absolute;
      width: 26px;
      height: 26px;
      display: grid;
      place-items: center;
      background: #ffffff;
      color: #344054;
      border: 1px solid #ccd6e5;
      font-size: 9px;
      font-weight: 900;
      box-shadow: 0 0 0 4px rgba(255,255,255,.72);
    }}
    .radar-node.hot {{
      background: #f3fbf6;
      border-color: #8fd8b4;
      color: #087443;
    }}
    .lead-card {{
      position: absolute;
      left: 52px;
      right: 52px;
      bottom: 42px;
      width: auto;
      background: rgba(255,255,255,.88);
      border: 1px solid #e4ebf5;
      padding: 22px;
    }}
    .lead-card strong {{
      display: block;
      font-size: 16px;
      line-height: 1.32;
      margin-bottom: 10px;
    }}
    .lead-card p {{
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
    }}
    .telemetry-grid {{
      position: absolute;
      top: 46px;
      right: 44px;
      display: grid;
      grid-template-columns: repeat(9, 10px);
      grid-auto-rows: 10px;
      gap: 7px;
      opacity: .72;
    }}
    .telemetry-dot {{
      border: 1px solid #d8e0ec;
      background: #ffffff;
    }}
    .telemetry-dot.on {{
      background: #101828;
      border-color: #101828;
    }}
    .telemetry-line {{
      position: absolute;
      left: 48px;
      right: 48px;
      top: 48%;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(16,24,40,.26), transparent);
    }}
    .telemetry-axis {{
      position: absolute;
      left: 48px;
      bottom: 96px;
      right: 48px;
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      color: #98a2b3;
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .metrics {{
      display: grid;
      gap: 18px;
    }}
    .metric-card {{
      padding: 20px;
      border-left: 4px solid var(--accent);
      min-height: 118px;
    }}
    .metric-card.warn {{ border-left-color: var(--warn); }}
    .metric-card.blue {{ border-left-color: var(--blue); }}
    .metric-label {{
      color: var(--muted);
      font-size: 11px;
      font-weight: 900;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    .metric-value {{
      margin-top: 8px;
      font-size: 34px;
      font-weight: 900;
      line-height: 1;
    }}
    .metric-copy {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }}
    .lower-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.5fr) minmax(300px, .9fr);
      gap: 24px;
      align-items: start;
    }}
    .table-panel,
    .tool-panel {{
      padding: 18px;
    }}
    .tabs {{
      display: flex;
      gap: 7px;
      flex-wrap: wrap;
    }}
    .tab {{
      min-height: 28px;
      padding: 0 10px;
      border: 1px solid var(--line);
      background: #f8fbff;
      color: #344054;
      display: inline-flex;
      align-items: center;
      font-size: 12px;
      font-weight: 800;
    }}
    .tab.active {{
      background: var(--brand);
      color: #ffffff;
      border-color: var(--brand);
    }}
    .update-table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    .update-table th {{
      color: var(--muted);
      font-size: 10px;
      text-align: left;
      text-transform: uppercase;
      padding: 12px 8px;
      border-bottom: 1px solid var(--line);
    }}
    .update-table td {{
      padding: 14px 8px;
      border-bottom: 1px solid #edf1f7;
      vertical-align: top;
      font-size: 13px;
      line-height: 1.45;
    }}
    .update-title {{
      display: block;
      font-size: 14px;
      font-weight: 900;
      line-height: 1.35;
      margin-bottom: 4px;
    }}
    .update-summary {{
      color: var(--muted);
      font-size: 12px;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: var(--accent);
      font-weight: 800;
      white-space: nowrap;
    }}
    .status::before {{
      content: "";
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 0 7px;
      border: 1px solid #d0e4ff;
      background: #eff6ff;
      color: #175cd3;
      font-size: 11px;
      font-weight: 800;
      white-space: nowrap;
    }}
    .action-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 30px;
      padding: 0 10px;
      background: #050b18;
      color: #ffffff;
      font-size: 11px;
      font-weight: 900;
      text-transform: uppercase;
      white-space: nowrap;
    }}
    .tool-stack {{
      display: grid;
      gap: 12px;
    }}
    .tool-card {{
      border: 1px solid #edf1f7;
      background: var(--soft);
      padding: 14px;
    }}
    .tool-card h4 {{
      margin: 6px 0 6px;
      font-size: 15px;
      line-height: 1.35;
    }}
    .tool-card p {{
      margin: 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.5;
    }}
    @media (max-width: 980px) {{
      .app-shell {{
        grid-template-columns: 1fr;
      }}
      .sidebar {{
        min-height: auto;
        position: static;
      }}
      .nav-list {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
      .hero-grid,
      .lower-grid {{
        grid-template-columns: 1fr;
      }}
    }}
    @media (max-width: 640px) {{
      .topbar {{
        height: auto;
        padding: 14px 16px;
        flex-wrap: wrap;
      }}
      .dashboard {{
        padding: 16px;
      }}
      .nav-list {{
        grid-template-columns: 1fr;
      }}
      .update-table,
      .update-table tbody,
      .update-table tr,
      .update-table td {{
        display: block;
        width: 100%;
      }}
      .update-table thead {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar" aria-label="대시보드 내비게이션">
      <div class="brand">
        <h1>AI Master</h1>
        <p>Weekly Ops Admin</p>
      </div>
      <nav class="nav-list">
        <a class="nav-item active" href="#"><span class="nav-icon">D</span>Dashboard</a>
        <a class="nav-item" href="work-skills/"><span class="nav-icon">W</span>Work Skills</a>
        <a class="nav-item" href="tools/"><span class="nav-icon">T</span>AI Tools</a>
        <a class="nav-item" href="#updates"><span class="nav-icon">R</span>Reports</a>
      </nav>
      <div class="sidebar-footer">
        <strong>Admin User</strong><br>
        AI Master Curator<br>
        {escape(today)}
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <h2>Delivery Dashboard</h2>
        <div class="search">Search feeds, tools, papers, or workflows...</div>
        <div class="top-actions" aria-label="빠른 상태">
          <span>!</span><span>?</span><span>*</span><span class="avatar"></span>
        </div>
      </header>
      <section class="dashboard">
        <div class="hero-grid">
          <section class="radar-panel" aria-label="AI 업데이트 레이더">
            <div class="panel-title">
              <h3>Turn signals into focus</h3>
              <span>{escape(today)}</span>
            </div>
            <div class="radar-map">
              <div class="telemetry-grid" aria-hidden="true">{_render_telemetry_dots()}</div>
              <div class="telemetry-line" aria-hidden="true"></div>
              <div class="telemetry-axis" aria-hidden="true"><span>Input</span><span>Cluster</span><span>Rank</span><span>Review</span><span>Dispatch</span></div>
              {radar_nodes}
              <div class="lead-card">
                <strong>{escape(_clip(lead_title, 90))}</strong>
                <p>{escape(_clip(lead_summary, 170))}</p>
              </div>
            </div>
          </section>
          <aside class="metrics" aria-label="주간 지표">
            <div class="metric-card">
              <div class="metric-label">Work-ready signals</div>
              <div class="metric-value">{len(infra_items)}</div>
              <div class="metric-copy">DBA, 네트워크, 서버 운영에 바로 연결할 후보 업데이트입니다.</div>
            </div>
            <div class="metric-card warn">
              <div class="metric-label">Automation signals</div>
              <div class="metric-value">{automation_count}</div>
              <div class="metric-copy">에이전트, 워크플로, 코딩 자동화와 관련된 항목입니다.</div>
            </div>
            <div class="metric-card blue">
              <div class="metric-label">Tool updates</div>
              <div class="metric-value">{tool_count}</div>
              <div class="metric-copy">Claude, OpenAI, Copilot, Cursor 계열 도구 변경입니다.</div>
            </div>
          </aside>
        </div>
        <div class="lower-grid" id="updates">
          <section class="table-panel">
            <div class="panel-title">
              <h3>Active Work Skill Updates</h3>
              <div class="tabs">
                <span class="tab active">All Updates</span>
                <span class="tab">In Review</span>
                <span class="tab">Operations</span>
              </div>
            </div>
            <table class="update-table">
              <thead>
                <tr>
                  <th style="width:42%">Update Name</th>
                  <th style="width:19%">Status</th>
                  <th style="width:23%">Signal</th>
                  <th style="width:16%">Action</th>
                </tr>
              </thead>
              <tbody>
                {work_rows}
              </tbody>
            </table>
          </section>
          <aside class="tool-panel">
            <div class="panel-title">
              <h3>AI Tool Dispatch</h3>
              <span>{len(latest_tool_items)} items</span>
            </div>
            <div class="tool-stack">
              {tool_cards}
            </div>
          </aside>
        </div>
      </section>
    </main>
  </div>
</body>
</html>
"""


def _render_dashboard_rows(items: list[SiteItem], mode: str) -> str:
    if not items:
        return '<tr><td colspan="4">표시할 업데이트가 없습니다.</td></tr>'
    rows = []
    for item in items[:8]:
        rows.append(
            "<tr>"
            f'<td><a class="update-title" href="{escape(_detail_href(item))}">{escape(_clip(item.title, 84))}</a>'
            f'<span class="update-summary">{escape(_clip(item.summary, 96))}</span></td>'
            f'<td><span class="status">{escape(_dashboard_status(item))}</span></td>'
            f'<td><span class="badge">{escape(_dashboard_signal(item, mode))}</span></td>'
            f'<td><a class="action-btn" href="{escape(_detail_href(item))}">Review</a></td>'
            "</tr>"
        )
    return "\n".join(rows)


def _render_command_tasks(items: list[SiteItem]) -> str:
    if not items:
        return '<article class="task"><strong>No tool updates</strong><span>새 도구 업데이트가 없습니다.</span></article>'
    return "\n".join(
        (
            '<article class="task">'
            f'<strong><a href="{escape(_detail_href(item))}">{escape(_clip(item.title, 72))}</a></strong>'
            f'<span>{escape(_clip(item.summary, 120))}</span>'
            "</article>"
        )
        for item in items
    )


def _render_smart_insight_cards(items: list[SiteItem]) -> str:
    labels = _smart_insight_blueprint()
    entries = []
    for index, (title, fallback) in enumerate(labels):
        item = items[index] if index < len(items) else None
        body = _smart_insight_body(index, item, fallback)
        detail = item.detail if item else fallback
        meta = (
            f"{item.source} · {item.kind} · {_format_date(item.published)}"
            if item
            else "AI Master Times"
        )
        points = item.key_points if item else ()
        tags = item.tags if item else ()
        entries.append((index + 1, title, body, detail, meta, points, tags))

    if not entries:
        return ""

    cards = []
    for number, title, body, detail, meta, points, tags in entries:
        cards.append(
            '<button class="insight-card" type="button" '
            f'data-insight-card data-number="{number}" '
            f'data-title="{escape(title, quote=True)}" '
            f'data-body="{escape(body, quote=True)}" '
            f'data-detail="{escape(_clip(detail, 700), quote=True)}" '
            f'data-meta="{escape(meta, quote=True)}" '
            f'data-points="{escape(json.dumps(list(points[:4]), ensure_ascii=False), quote=True)}" '
            f'data-tags="{escape(json.dumps(list(tags[:6]), ensure_ascii=False), quote=True)}">'
            f'<span class="card-icon">{number}</span>'
            f'<span><span class="card-title">{escape(title)}</span><p>{escape(body)}</p></span>'
            '</button>'
        )

    first_number, first_title, first_body, first_detail, first_meta, first_points, first_tags = entries[0]
    return (
        '<div class="insight-list">'
        + "\n".join(cards)
        + "</div>"
        + '<article class="insight-detail" aria-live="polite">'
        + "<div>"
        + f'<div class="detail-number" data-insight-number>{first_number}</div>'
        + f'<div class="detail-meta" data-insight-meta>{escape(first_meta)}</div>'
        + f'<h3 data-insight-title>{escape(first_title)}</h3>'
        + f'<p class="detail-summary" data-insight-body>{escape(first_body)}</p>'
        + f'<p class="detail-copy" data-insight-detail>{escape(_clip(first_detail, 700))}</p>'
        + '<ul class="detail-points" data-insight-points>'
        + "".join(f"<li>{escape(point)}</li>" for point in first_points[:4])
        + "</ul>"
        + "</div>"
        + '<div class="detail-tags" data-insight-tags>'
        + "".join(f'<span class="detail-tag">#{escape(tag)}</span>' for tag in first_tags[:6])
        + "</div>"
        + "</article>"
        + """
<script>
(() => {
  const buttons = document.querySelectorAll('[data-insight-card]');
  const number = document.querySelector('[data-insight-number]');
  const title = document.querySelector('[data-insight-title]');
  const body = document.querySelector('[data-insight-body]');
  const detail = document.querySelector('[data-insight-detail]');
  const meta = document.querySelector('[data-insight-meta]');
  const points = document.querySelector('[data-insight-points]');
  const tags = document.querySelector('[data-insight-tags]');
  const grid = document.querySelector('[data-insight-grid]');
  if (!buttons.length || !number || !title || !body || !detail || !meta || !points || !tags || !grid) return;

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      grid.classList.add('has-selection');
      buttons.forEach((item) => item.classList.remove('is-active'));
      button.classList.add('is-active');
      number.textContent = button.dataset.number || '';
      title.textContent = button.dataset.title || '';
      body.textContent = button.dataset.body || '';
      detail.textContent = button.dataset.detail || '';
      meta.textContent = button.dataset.meta || '';

      let pointItems = [];
      let tagItems = [];
      try { pointItems = JSON.parse(button.dataset.points || '[]'); } catch (error) { pointItems = []; }
      try { tagItems = JSON.parse(button.dataset.tags || '[]'); } catch (error) { tagItems = []; }
      points.replaceChildren(...pointItems.map((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        return li;
      }));
      tags.replaceChildren(...tagItems.map((item) => {
        const tag = document.createElement('span');
        tag.className = 'detail-tag';
        tag.textContent = `#${item}`;
        return tag;
      }));
    });
  });
})();
</script>
"""
    )


def _smart_insight_blueprint() -> tuple[tuple[str, str], ...]:
    return (
        (
            "Harness Engineering",
            "모델이 제안하고 하네스가 검증·실행하는 구조입니다. 권한, 스키마, 로그, 재시도 정책을 분리해 에이전트 작업을 운영 가능한 흐름으로 만듭니다.",
        ),
        (
            "AI Product Builder Stack",
            "Stitch, v0, Lovable, Bolt 같은 도구는 화면과 프론트엔드 초안을 빠르게 만들고, Supabase·Neon·Convex 같은 백엔드 도구는 인증, 데이터, API를 붙이는 출발점이 됩니다.",
        ),
        (
            "Agent Harness",
            "에이전트가 직접 시스템을 만지는 대신, 하네스가 도구 호출을 검증하고 결과를 다시 모델에 주입하는 안전한 실행 계층입니다.",
        ),
        (
            "Design System to Backend",
            "DESIGN.md와 getdesign.md는 UI 규칙을 에이전트가 읽게 해주고, Prisma·Drizzle·tRPC·GraphQL 같은 도구는 화면 뒤의 데이터 모델과 API 계약을 안정적으로 연결합니다.",
        ),
        (
            "AI Software Delivery",
            "Harness 같은 플랫폼은 테스트 자동화, 배포, 보안, 비용 최적화에 AI 에이전트를 붙여 SDLC 운영을 자동화하는 방향으로 진화하고 있습니다.",
        ),
        (
            "Workflow and Data Layer",
            "LangGraph, Inngest, Temporal, n8n 같은 워크플로 도구와 pgvector, Pinecone, Weaviate 같은 벡터 저장소는 AI 기능을 백엔드 프로세스로 운영하는 데 필요합니다.",
        ),
        (
            "Production Agent Guardrails",
            "운영 환경의 에이전트는 평가, 롤백, 감사 로그, 제한된 권한, 사람 승인 단계를 포함해야 안정적으로 확장됩니다.",
        ),
        (
            "Deployable AI App Path",
            "Figma Make, Cursor, Replit, Vercel, Fly.io, Render를 함께 보면 디자인 시안, 코드 생성, API 서버, 배포까지 이어지는 AI 앱 제작 경로를 잡을 수 있습니다.",
        ),
        (
            "Model Gateway and Routing",
            "OpenRouter, LiteLLM, Portkey 같은 게이트웨이는 여러 모델 API를 한 인터페이스로 묶고 비용, 장애 대응, 모델 교체를 운영 레벨에서 관리하게 해줍니다.",
        ),
        (
            "AI Evaluation Stack",
            "LangSmith, Braintrust, OpenAI Evals, Ragas 같은 평가 도구는 프롬프트와 RAG 품질을 배포 전후로 비교하고 회귀를 잡는 데 필요합니다.",
        ),
        (
            "RAG and Knowledge Backend",
            "LlamaIndex, LangChain, pgvector, Qdrant, Weaviate는 문서 검색, 임베딩, 벡터 저장, 근거 추적을 AI 서비스의 백엔드 기능으로 만듭니다.",
        ),
        (
            "Observability and Incident AI",
            "Datadog, Grafana, Sentry, Harness Incident Agent 같은 도구는 AI 기능의 오류, 지연, 비용, 장애 원인을 운영자가 추적하게 해줍니다.",
        ),
        (
            "Secure Secrets and Policy",
            "Doppler, Infisical, Vault, OPA, Cedar 같은 도구는 API 키, 권한, 정책 결정을 분리해 에이전트와 백엔드가 안전하게 동작하게 합니다.",
        ),
        (
            "Team Knowledge Workflow",
            "Notion, Linear, GitHub Issues, Slack, Teams를 AI 워크플로와 연결하면 요구사항, 작업 상태, 릴리즈 노트를 자동으로 정리할 수 있습니다.",
        ),
    )


def _smart_insight_body(index: int, item: SiteItem | None, fallback: str) -> str:
    if index % 2 == 0 and item:
        return f"{fallback} 이번 주 관련 신호: {_clip(item.summary, 110)}"
    return fallback


def _editorial_intro_copy(lead_summary: str) -> str:
    summary = _clip(_clean_plain_text(lead_summary), 220)
    return (
        "AI Master Times는 매주 수집한 논문, 업무 AI 스킬, Claude와 AI 도구 업데이트를 "
        f"업무 적용 관점으로 재구성합니다. 이번 주 대표 신호: {summary}"
    )


def _render_logo_roll() -> str:
    names = (
        "OpenAI",
        "Claude",
        "Stitch",
        "getdesign.md",
        "Supabase",
        "Neon",
        "LangGraph",
        "Temporal",
        "Harness",
        "Cursor",
        "Vercel",
        "Pinecone",
        "LiteLLM",
        "LangSmith",
        "Braintrust",
        "Qdrant",
        "Datadog",
        "Infisical",
        "Linear",
    )
    return "".join(f"<span>{escape(name)}</span>" for name in names)


def _render_dashboard_tool_cards(items: list[SiteItem]) -> str:
    if not items:
        return '<p class="update-summary">표시할 도구 업데이트가 없습니다.</p>'
    return "\n".join(
        (
            '<article class="tool-card">'
            f'<div class="kicker">{escape(item.source)} · {_format_date(item.published)}</div>'
            f'<h4><a href="{escape(_detail_href(item))}">{escape(_clip(item.title, 78))}</a></h4>'
            f'<p>{escape(_clip(item.summary, 110))}</p>'
            "</article>"
        )
        for item in items
    )


def _render_radar_nodes(items: list[SiteItem]) -> str:
    positions = ((22, 28), (55, 22), (72, 47), (38, 58), (18, 72), (64, 76))
    nodes = []
    for index, item in enumerate(items[:6]):
        left, top = positions[index]
        hot_class = " hot" if index in (1, 2) else ""
        label = _dashboard_node_label(item)
        nodes.append(
            f'<a class="radar-node{hot_class}" href="{escape(_detail_href(item))}" '
            f'style="left:{left}%;top:{top}%;" title="{escape(item.title)}">{escape(label)}</a>'
        )
    return "\n".join(nodes)


def _render_telemetry_dots() -> str:
    active = {2, 7, 14, 18, 25, 31, 38, 44, 51, 58, 66, 72}
    return "".join(
        f'<span class="telemetry-dot{" on" if index in active else ""}"></span>'
        for index in range(81)
    )


def _dashboard_node_label(item: SiteItem) -> str:
    for tag in item.tags:
        cleaned = re.sub(r"[^A-Za-z0-9가-힣]", "", tag)
        if cleaned:
            return cleaned[:2].upper()
    return item.source[:2].upper()


def _dashboard_status(item: SiteItem) -> str:
    text = f"{item.title} {item.summary} {' '.join(item.tags)}".lower()
    if any(keyword in text for keyword in ("security", "risk", "incident", "보안")):
        return "Watch"
    if any(keyword in text for keyword in ("release", "update", "support", "add")):
        return "New"
    return "Review"


def _dashboard_signal(item: SiteItem, mode: str) -> str:
    if item.tags:
        return item.tags[0]
    return "AI 업데이트" if mode == "work" else "도구 변경"


def _count_keyword_items(items: list[SiteItem], keywords: tuple[str, ...]) -> int:
    count = 0
    for item in items:
        text = f"{item.title} {item.summary} {' '.join(item.tags)}".lower()
        if any(keyword in text for keyword in keywords):
            count += 1
    return count


def _write_secondary_pages(
    output_dir: Path,
    ai_items: list[SiteItem],
    tool_items: list[SiteItem],
    analytics_html: str,
) -> None:
    work_items = _latest_first(ai_items[:5])
    other_items = _latest_first(ai_items[5:10])
    tools = _latest_first(tool_items[:10])

    (output_dir / "work-skills").mkdir(parents=True, exist_ok=True)
    (output_dir / "tools").mkdir(parents=True, exist_ok=True)
    (output_dir / "items").mkdir(parents=True, exist_ok=True)

    (output_dir / "work-skills" / "index.html").write_text(
        _render_board_page(
            title="업무 AI 스킬 업데이트",
            subtitle="DBA, 네트워크, 서버 운영자가 업무에 적용할 수 있는 AI 도구와 자동화 업데이트입니다.",
            items=work_items,
            analytics_html=analytics_html,
            back_href="../",
        ),
        encoding="utf-8",
    )
    (output_dir / "tools" / "index.html").write_text(
        _render_board_page(
            title="Claude와 AI 도구 업데이트",
            subtitle="Claude, OpenAI, GitHub Copilot, Cursor 등 주요 AI 도구의 최신 업데이트입니다.",
            items=tools,
            analytics_html=analytics_html,
            back_href="../",
        ),
        encoding="utf-8",
    )

    for item in [*work_items, *other_items, *tools]:
        (output_dir / "items" / f"{_item_slug(item)}.html").write_text(
            _render_detail_page(item, analytics_html=analytics_html, back_href="../"),
            encoding="utf-8",
        )


def _render_board_page(
    title: str,
    subtitle: str,
    items: list[SiteItem],
    analytics_html: str,
    back_href: str,
) -> str:
    cards = "\n".join(
        (
            '<article class="board-row">'
            f'<div class="kicker">{escape(item.kind)} · {escape(item.source)}</div>'
            f'<h2><a href="../{escape(_detail_href(item))}">{escape(item.title)} '
            f'<span class="title-date">({_format_date(item.published)})</span></a></h2>'
            f'<p>{escape(_clip(item.summary, 280))}</p>'
            f"{_render_tags(item)}"
            "</article>"
        )
        for item in items
    )
    return _render_plain_page(
        title=title,
        analytics_html=analytics_html,
        body=f"""
        <a class="back-link" href="{escape(back_href)}">← 첫 화면</a>
        <header class="simple-header">
          <h1>{escape(title)}</h1>
          <p>{escape(subtitle)}</p>
        </header>
        <section class="board-list">{cards}</section>
        """,
    )


def _render_detail_page(item: SiteItem, analytics_html: str, back_href: str) -> str:
    detail_paragraphs = "".join(
        f"<p>{escape(paragraph.strip())}</p>"
        for paragraph in re.split(r"\n{2,}", item.detail)
        if paragraph.strip()
    )
    comparisons = _render_note_section("비교 설명", item.comparisons)
    glossary = _render_note_section("용어 풀이", item.glossary)
    return _render_plain_page(
        title=item.title,
        analytics_html=analytics_html,
        body=f"""
        <a class="back-link" href="{escape(back_href)}">← 첫 화면</a>
        <article class="detail">
          <div class="kicker">{escape(item.kind)} · {escape(item.source)}</div>
          <h1>{escape(item.title)} <span class="title-date">({_format_date(item.published)})</span></h1>
          <p class="summary">{escape(item.summary)}</p>
          <section>
            <h2>상세 설명</h2>
            {detail_paragraphs}
          </section>
          <section>
            <h2>키포인트</h2>
            {_render_key_points(item)}
          </section>
          {comparisons}
          {glossary}
          {_render_tags(item)}
          <p><a class="source-link" href="{escape(item.url)}">원문 보기</a></p>
        </article>
        """,
    )


def _render_note_section(title: str, notes: tuple[str, ...]) -> str:
    if not notes:
        return ""
    items = "".join(f"<li>{escape(note)}</li>" for note in notes)
    return f"""
          <section>
            <h2>{escape(title)}</h2>
            <ol class="note-list">{items}</ol>
          </section>
    """


def _render_plain_page(title: str, analytics_html: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · AI Master Times</title>
  {analytics_html}
  <style>
    body {{
      margin: 0;
      background: #f7f3ea;
      color: #111111;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
    }}
    a {{ color: inherit; text-underline-offset: 3px; }}
    .page {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }}
    .back-link {{
      display: inline-block;
      margin-bottom: 18px;
      font: 700 14px/1.4 Arial, "Noto Sans KR", sans-serif;
    }}
    .simple-header, .detail {{
      border-top: 3px solid #222222;
      padding-top: 18px;
    }}
    h1 {{
      font-size: clamp(34px, 6vw, 64px);
      line-height: 1.02;
      margin: 0 0 12px;
      letter-spacing: 0;
    }}
    h2 {{
      border-bottom: 2px solid #222222;
      font-size: 24px;
      margin: 28px 0 12px;
      padding-bottom: 8px;
    }}
    .title-date {{
      color: #5b5b5b;
      font: 700 15px/1.35 Arial, "Noto Sans KR", sans-serif;
      white-space: nowrap;
    }}
    p {{
      font-size: 17px;
      line-height: 1.75;
      margin: 10px 0;
    }}
    .board-list {{
      display: grid;
      gap: 0;
      margin-top: 24px;
      border-top: 1px solid #222222;
    }}
    .board-row {{
      border-bottom: 1px solid #d8d2c4;
      padding: 18px 0;
    }}
    .board-row h2 {{
      border: 0;
      margin: 4px 0 8px;
      padding: 0;
      font-size: 26px;
    }}
    .kicker {{
      color: #8b1e16;
      font: 800 12px/1.4 Arial, "Noto Sans KR", sans-serif;
      text-transform: uppercase;
    }}
    .summary {{
      font-size: 19px;
    }}
    .key-points {{
      margin: 9px 0 0;
      padding-left: 20px;
      font: 15px/1.65 Arial, "Noto Sans KR", sans-serif;
    }}
    .note-list {{
      margin: 9px 0 0;
      padding-left: 22px;
      color: #2b2b2b;
      font: 15px/1.75 Arial, "Noto Sans KR", sans-serif;
    }}
    .note-list li {{
      border-bottom: 1px solid #e2dccf;
      padding: 7px 0;
    }}
    .points-label {{
      display: none;
    }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 12px;
    }}
    .tag {{
      border: 1px solid #d8d2c4;
      background: #fffaf0;
      padding: 3px 7px;
      font: 700 12px/1.3 Arial, "Noto Sans KR", sans-serif;
    }}
    .source-link {{
      display: inline-block;
      border: 1px solid #222222;
      padding: 9px 12px;
      text-decoration: none;
      font: 800 14px/1.3 Arial, "Noto Sans KR", sans-serif;
    }}
  </style>
</head>
<body>
  <main class="page">
    {body}
  </main>
</body>
</html>
"""


def _render_analytics(settings: Settings) -> str:
    provider = (settings.site_analytics_provider or "").strip().lower()
    analytics_id = (settings.site_analytics_id or "").strip()
    domain = (settings.site_analytics_domain or "").strip()

    if provider in {"ga4", "google", "google-analytics"} and analytics_id:
        safe_id = escape(analytics_id, quote=True)
        return textwrap.dedent(
            f"""
            <script async src="https://www.googletagmanager.com/gtag/js?id={safe_id}"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){{dataLayer.push(arguments);}}
              gtag('js', new Date());
              gtag('config', '{safe_id}');
            </script>
            """
        ).strip()

    if provider == "goatcounter" and analytics_id:
        safe_id = escape(analytics_id, quote=True)
        return (
            f'<script data-goatcounter="https://{safe_id}.goatcounter.com/count" '
            'async src="//gc.zgo.at/count.js"></script>'
        )

    if provider == "plausible" and domain:
        safe_domain = escape(domain, quote=True)
        return (
            f'<script defer data-domain="{safe_domain}" '
            'src="https://plausible.io/js/script.js"></script>'
        )

    return ""


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
        instructions = (
            "Return only a JSON array. Each item must contain title, summary, detail, key_points, tags, "
            "comparisons, and glossary. "
            "Titles and summaries must be Korean sentences. Product names such as OpenAI, "
            "Claude, Cursor, GitHub Copilot, Codex, Gartner, Endava, Harness, Warp, AWS, and Azure "
            "must stay in English. "
            "detail must be 2 to 4 Korean paragraphs that explain the item in more depth for a detail page. "
            "key_points must be an array of 2 or 3 concise Korean strings. tags must be an array of "
            "3 to 5 short Korean or product-name strings. comparisons must be an array of 0 to 3 Korean "
            "strings comparing the item with adjacent tools or approaches when useful. For Endava items, "
            "compare it with Harness Engineering if relevant: Endava is a consulting/transformation "
            "approach, while Harness is a DevOps/software delivery automation platform. glossary must be "
            "an array of 0 to 5 Korean strings formatted like 'Warp: ...' explaining difficult product "
            "names, acronyms, or jargon as footnote-style notes. Emphasize practical work skills, "
            "automation patterns, operational usage, and concrete tool adoption. Do not invent unsupported "
            "facts."
        )
        input_text = (
            f"Translate and rewrite these {context} items for a Korean newsletter site. "
            "Use natural Korean titles that preserve product and company names in English. "
            "Summaries must be one concise Korean sentence and must make clear what a DBA, "
            "network engineer, server operator, or technical mentor can do with it at work. "
            "Key points should explain: what changed, where it can be used in work, and what "
            "to watch before adoption. Add comparison notes when the item could be confused with "
            "another tool or vendor, and add glossary notes for difficult words such as Warp, Harness, "
            "Agent tasks REST API, CI/CD, SDK, or orchestration.\n\n"
            f"{source_block}"
        )
        localized = _parse_json_array(_generate_openai_text(client, model, instructions, input_text))
        if _has_untranslated_items(localized):
            localized = _repair_korean_translation(client, model, source_block, context)
    except Exception as exc:  # noqa: BLE001
        print(f"OpenAI localization failed for {context}: {exc}", file=sys.stderr)
        if _require_openai_localization():
            raise
        return [_fallback_korean_item(item) for item in items]

    if len(localized) != len(items):
        if _require_openai_localization():
            raise ValueError(
                f"OpenAI returned {len(localized)} localized items for {len(items)} source items."
            )
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
            detail=_safe_korean_field(
                localized_item.get("detail"),
                fallback="이 항목은 원문 링크에서 세부 내용을 확인한 뒤 업무 적용 가능성을 검토해 주세요.",
            ),
            source=_korean_source_name(item.source),
            kind=_korean_kind_name(item.kind),
            published=item.published,
            key_points=_safe_key_points(localized_item, item),
            tags=_safe_tags(localized_item, item),
            comparisons=_safe_comparisons(localized_item, item),
            glossary=_safe_glossary(localized_item, item),
        )
        for item, localized_item in zip(items, localized, strict=True)
    ]


def _repair_korean_translation(
    client: object,
    model: str,
    source_block: str,
    context: str,
) -> list[dict[str, object]]:
    instructions = (
        "Return only a JSON array. Each item must contain title, summary, detail, key_points, tags, "
        "comparisons, and glossary. "
        "Translate English article titles and summaries into Korean. Product names may "
        "remain in English, but English clauses or English explanatory sentences are not allowed. "
        "detail must be 2 to 4 Korean paragraphs. "
        "key_points must be an array of 2 or 3 concise Korean strings. tags must be an array of "
        "3 to 5 short Korean or product-name strings. comparisons must be 0 to 3 Korean strings. "
        "glossary must be 0 to 5 Korean strings formatted like 'Warp: ...'."
    )
    input_text = (
        f"The previous Korean localization for these {context} items contained untranslated "
        "English. Rewrite them again. Examples: "
        "'OpenAI named a Leader in enterprise coding agents by Gartner' should become "
        "'OpenAI, 가트너 엔터프라이즈 코딩 에이전트 분야 리더로 선정'. "
        "'OpenAI is named a leader...' should become a Korean sentence.\n\n"
        f"{source_block}"
    )
    return _parse_json_array(_generate_openai_text(client, model, instructions, input_text))


def _generate_openai_text(client: object, model: str, instructions: str, input_text: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI chat completions returned an empty response.")
        return content
    except Exception as exc:  # noqa: BLE001
        print(f"OpenAI chat completions failed, trying Responses API: {exc}", file=sys.stderr)
        if "timed out" in str(exc).lower():
            raise

    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_text,
    )
    return response.output_text


def _require_openai_localization() -> bool:
    return os.getenv("AIMSTLETTER_REQUIRE_OPENAI_LOCALIZATION") == "1"


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


def _safe_comparisons(localized_item: dict[str, object], original: DigestItem) -> tuple[str, ...]:
    notes = [
        _clean_visible_korean(note)
        for note in _coerce_string_list(localized_item.get("comparisons"))
        if note and not _looks_untranslated(note)
    ]
    notes.extend(_fallback_comparisons(original))
    return tuple(list(dict.fromkeys(notes))[:4])


def _safe_glossary(localized_item: dict[str, object], original: DigestItem) -> tuple[str, ...]:
    notes = [
        _clean_visible_korean(note)
        for note in _coerce_string_list(localized_item.get("glossary"))
        if note and not _looks_untranslated(note)
    ]
    notes.extend(_fallback_glossary(original))
    return tuple(list(dict.fromkeys(notes))[:6])


def _fallback_comparisons(item: DigestItem) -> list[str]:
    text = _item_text(item)
    comparisons: list[str] = []
    if "endava" in text:
        comparisons.append(
            "Endava는 특정 기능 하나라기보다 기업의 개발 문화와 전달 방식을 AI 중심으로 바꾸는 컨설팅·전환 접근에 가깝습니다."
        )
        comparisons.append(
            "Harness Engineering은 CI/CD, 배포, 테스트, 관측 같은 소프트웨어 전달 파이프라인을 자동화하는 플랫폼 성격이 강해 실무 적용 지점이 더 직접적입니다."
        )
        comparisons.append(
            "따라서 Endava는 '조직을 어떻게 AI 네이티브로 바꿀까'를 볼 때, Harness는 '배포·운영 자동화를 어떤 도구로 구현할까'를 볼 때 비교하면 좋습니다."
        )
    return comparisons


def _fallback_glossary(item: DigestItem) -> list[str]:
    text = _item_text(item)
    glossary: list[str] = []
    glossary_terms = (
        ("warp", "Warp: 터미널과 개발 워크플로우에 AI 기능을 결합한 개발자 도구입니다."),
        ("harness", "Harness: CI/CD, 배포, 테스트, 관측 등 소프트웨어 전달 과정을 자동화하는 DevOps 플랫폼입니다."),
        ("endava", "Endava: 기업의 소프트웨어 개발과 디지털 전환을 지원하는 IT 서비스·컨설팅 회사입니다."),
        ("agent tasks rest api", "Agent tasks REST API: AI 에이전트 작업을 프로그램 코드나 외부 시스템에서 호출·추적할 수 있게 하는 API 방식입니다."),
        ("ci/cd", "CI/CD: 코드 변경을 자동으로 빌드·테스트·배포하는 지속적 통합과 지속적 배포 절차입니다."),
        ("sdk", "SDK: 특정 플랫폼 기능을 애플리케이션에 쉽게 붙일 수 있도록 제공되는 개발 도구 모음입니다."),
        ("orchestration", "오케스트레이션: 여러 작업, 도구, 서비스를 순서와 조건에 맞게 묶어 자동 실행하는 방식입니다."),
        ("codex", "Codex: 코드 작성, 수정, 리뷰 같은 개발 작업을 돕는 OpenAI의 코딩 에이전트 계열 도구입니다."),
    )
    for keyword, note in glossary_terms:
        if keyword in text:
            glossary.append(note)
    return glossary


def _item_text(item: DigestItem) -> str:
    return f"{item.title} {item.summary} {item.source} {item.kind}".lower()


def _detail_href(item: SiteItem) -> str:
    return f"items/{_item_slug(item)}.html"


def _item_slug(item: SiteItem) -> str:
    title_slug = re.sub(r"[^a-z0-9가-힣]+", "-", item.title.lower()).strip("-")
    title_slug = title_slug[:48].strip("-") or "item"
    digest = hashlib.sha1(item.url.encode("utf-8")).hexdigest()[:10]
    return f"{title_slug}-{digest}"


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
    title = _fallback_display_title(item)
    summary = _fallback_display_summary(item)
    return SiteItem(
        title=title,
        summary=summary,
        detail=(
            f"{summary}\n\n"
            "현재 자동 한국어 재작성 단계가 지연되어 원문 기반의 간단한 안내로 표시합니다. "
            "출처 링크에서 발표 원문을 확인한 뒤 업무 적용 가능성, 도입 조건, 운영 리스크를 함께 검토하세요."
        ),
        source=_korean_source_name(item.source),
        kind=_korean_kind_name(item.kind),
        url=item.url,
        published=item.published,
        key_points=(
            "원문 제목과 요약을 기준으로 선별된 항목입니다.",
            "출처 링크에서 세부 변경 사항과 적용 조건을 확인하세요.",
        ),
        tags=tuple(_fallback_tags(item)[:5]),
        comparisons=tuple(_fallback_comparisons(item)),
        glossary=tuple(_fallback_glossary(item)),
    )


def _fallback_display_title(item: DigestItem) -> str:
    title = _clean_plain_text(item.title)
    source = _korean_source_name(item.source)
    if title:
        return f"{source}: {title}"
    return f"{source}에서 확인한 최신 업데이트"


def _fallback_display_summary(item: DigestItem) -> str:
    text = f"{item.title} {item.summary} {item.source}".lower()
    topic = _fallback_korean_topic(text)
    action = _fallback_korean_action(text)
    source = _korean_source_name(item.source)
    return f"{source}에 공개된 {topic} 관련 소식입니다. {action}"


def _fallback_korean_topic(text: str) -> str:
    topics = (
        (("copilot", "github", "coding"), "개발 도구와 코딩 자동화"),
        (("claude", "anthropic"), "Claude와 생성형 AI 도구"),
        (("openai", "codex", "gpt"), "OpenAI 도구와 AI 에이전트"),
        (("cursor", "warp"), "AI 개발 환경"),
        (("database", "sql", "query"), "데이터베이스 업무 AI 활용"),
        (("network", "latency", "traffic"), "네트워크 운영 AI 활용"),
        (("security", "vulnerability", "risk"), "보안과 리스크 관리"),
        (("server", "kubernetes", "cloud", "devops", "sre"), "서버 운영과 자동화"),
        (("agent", "workflow", "automation"), "AI 에이전트와 업무 자동화"),
        (("enterprise", "business", "customer"), "기업 업무 적용"),
    )
    for keywords, label in topics:
        if any(keyword in text for keyword in keywords):
            return label
    return "AI 업데이트"


def _fallback_korean_action(text: str) -> str:
    if any(keyword in text for keyword in ("release", "launch", "add", "support", "update")):
        return "새 기능이나 변경 사항이 업무 흐름에 어떤 영향을 주는지 확인해 보세요."
    if any(keyword in text for keyword in ("paper", "arxiv", "research", "study", "benchmark")):
        return "연구 결과가 실제 운영, 자동화, 의사결정 개선에 연결될 수 있는지 검토해 보세요."
    if any(keyword in text for keyword in ("security", "risk", "vulnerability", "incident")):
        return "도입 전 보안 영향과 운영 리스크를 함께 점검하는 것이 좋습니다."
    return "출처 링크에서 세부 내용을 확인하고 수업 토론이나 업무 적용 아이디어로 활용하세요."


def _clean_plain_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


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
