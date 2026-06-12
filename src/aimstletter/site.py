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
    kst = timezone(timedelta(hours=9), name="KST")
    now = datetime.now(UTC).astimezone(kst)

    week_start, week_end = _weekly_window(now)
    raw_feed_items = fetch_recent_items(settings.feeds, settings.lookback_days)
    raw_tool_items = fetch_recent_items(settings.tool_feeds, 21)
    source_items = _dedupe_items(
        [
            *_items_in_window(raw_feed_items, week_start, week_end),
            *_items_in_window(raw_tool_items, week_start, week_end),
        ]
    )
    skill_items = _rank_work_skill_updates(source_items, 5)
    skill_urls = {item.url for item in skill_items}
    other_source_items = [item for item in source_items if item.url not in skill_urls]
    ai_items = [*skill_items, *_latest_digest_items(rank_items(other_source_items, 12), 5)]
    tool_items = _rank_tool_updates(_items_in_window(raw_tool_items, week_start, week_end), 10)
    ai_items = _localize_items(ai_items, settings, "DBA, 네트워크, 서버 운영자가 업무에 적용할 AI 스킬 업데이트")
    tool_items = _localize_items(tool_items, settings, "인공지능 도구 업데이트")
    archive_entry = _weekly_archive_entry(now)
    archive_entries = _collect_archive_entries(output_dir, archive_entry)
    html = render_homepage(
        ai_items,
        tool_items,
        analytics_html=_render_analytics(settings),
        archive_entries=archive_entries,
        current_archive_entry=archive_entry,
        now=now,
    )

    path = output_dir / "index.html"
    path.write_text(html, encoding="utf-8")
    _write_weekly_archive(output_dir, archive_entry, html)
    _refresh_archive_navigation(output_dir, archive_entries)
    _write_secondary_pages(output_dir, ai_items, tool_items, _render_analytics(settings))
    return path


def render_homepage(
    ai_items: list[SiteItem],
    tool_items: list[SiteItem],
    analytics_html: str = "",
    archive_entries: list[dict[str, object]] | None = None,
    current_archive_entry: dict[str, object] | None = None,
    now: datetime | None = None,
) -> str:
    kst = timezone(timedelta(hours=9), name="KST")
    today_dt = now.astimezone(kst) if now else datetime.now(UTC).astimezone(kst)
    today = today_dt.strftime("%Y년 %m월 %d일")
    infra_items = _latest_first(ai_items[:5])
    other_items = _latest_first(ai_items[5:10])
    latest_tool_items = _latest_first(tool_items[:10])
    return _render_dashboard_homepage(
        today=today,
        infra_items=infra_items,
        other_items=other_items,
        latest_tool_items=latest_tool_items,
        analytics_html=analytics_html,
        archive_entries=archive_entries or [],
        current_archive_entry=current_archive_entry,
    )


def _weekly_window(day: datetime) -> tuple[datetime, datetime]:
    kst = timezone(timedelta(hours=9), name="KST")
    day_kst = day.astimezone(kst)
    tuesday_offset = (day_kst.weekday() - 1) % 7
    week_end = (day_kst - timedelta(days=tuesday_offset)).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )
    week_start = (week_end - timedelta(days=6)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return week_start, week_end


def _items_in_window(
    items: list[DigestItem],
    start: datetime,
    end: datetime,
) -> list[DigestItem]:
    kst = timezone(timedelta(hours=9), name="KST")
    return [item for item in items if start <= item.published.astimezone(kst) <= end]


def _period_label(start: datetime, end: datetime) -> str:
    return f"{start:%Y-%m-%d}~{end:%Y-%m-%d} 데이터"


def _archive_week_window(year: int, month: int, week: int) -> tuple[datetime, datetime]:
    kst = timezone(timedelta(hours=9), name="KST")
    anchor_day = min(((week - 1) * 7) + 3, 28)
    return _weekly_window(datetime(year, month, anchor_day, 12, tzinfo=kst))


def _weekly_archive_entry(day: datetime) -> dict[str, object]:
    week = ((day.day - 1) // 7) + 1
    start, end = _weekly_window(day)
    return {
        "year": day.year,
        "month": day.month,
        "week": week,
        "href": f"archive/{day.year}/{day.month:02d}/week-{week}/",
        "period_start": start.date().isoformat(),
        "period_end": end.date().isoformat(),
        "period_label": _period_label(start, end),
    }


def _collect_archive_entries(
    output_dir: Path,
    current_entry: dict[str, object],
) -> list[dict[str, object]]:
    entries: dict[tuple[int, int, int], dict[str, object]] = {}
    archive_root = output_dir / "archive"
    if archive_root.exists():
        for path in archive_root.glob("*/*/week-*/index.html"):
            try:
                year = int(path.parts[-4])
                month = int(path.parts[-3])
                week = int(path.parts[-2].replace("week-", ""))
            except (ValueError, IndexError):
                continue
            start, end = _archive_week_window(year, month, week)
            entries[(year, month, week)] = {
                "year": year,
                "month": month,
                "week": week,
                "href": f"archive/{year}/{month:02d}/week-{week}/",
                "period_start": start.date().isoformat(),
                "period_end": end.date().isoformat(),
                "period_label": _period_label(start, end),
            }
    key = (
        int(current_entry["year"]),
        int(current_entry["month"]),
        int(current_entry["week"]),
    )
    entries[key] = current_entry
    return [entries[key] for key in sorted(entries, reverse=True)]


def _write_weekly_archive(
    output_dir: Path,
    archive_entry: dict[str, object],
    html: str,
) -> None:
    archive_dir = (
        output_dir
        / "archive"
        / str(archive_entry["year"])
        / f"{int(archive_entry['month']):02d}"
        / f"week-{archive_entry['week']}"
    )
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived_html = html.replace("<head>", '<head>\n  <base href="../../../../">', 1)
    archive_dir.joinpath("index.html").write_text(archived_html, encoding="utf-8")


def _refresh_archive_navigation(output_dir: Path, entries: list[dict[str, object]]) -> None:
    archive_root = output_dir / "archive"
    if not entries or not archive_root.exists():
        return
    entries_by_href = {str(entry["href"]).rstrip("/") + "/": entry for entry in entries}
    for path in archive_root.glob("*/*/week-*/index.html"):
        try:
            year = int(path.parts[-4])
            month = int(path.parts[-3])
            week = int(path.parts[-2].replace("week-", ""))
        except (ValueError, IndexError):
            continue
        href = f"archive/{year}/{month:02d}/week-{week}/"
        current_entry = entries_by_href.get(href, {"year": year, "month": month, "week": week, "href": href})
        html = path.read_text(encoding="utf-8")
        updated = re.sub(
            r'<aside class="archive-nav" aria-label="주간 아카이브">[\s\S]*?</aside>',
            _render_archive_nav(entries, current_entry=current_entry),
            html,
            count=1,
        )
        if updated != html:
            path.write_text(updated, encoding="utf-8")
    return

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


def _archive_entry_key(entry: dict[str, object] | None) -> tuple[int, int, int]:
    if not entry:
        return (0, 0, 0)
    return (int(entry["year"]), int(entry["month"]), int(entry["week"]))


def _previous_archive_entry(
    entries: list[dict[str, object]],
    current_entry: dict[str, object] | None,
) -> dict[str, object] | None:
    if not entries or not current_entry:
        return None
    current_key = _archive_entry_key(current_entry)
    ordered = sorted(entries, key=_archive_entry_key)
    previous = [entry for entry in ordered if _archive_entry_key(entry) < current_key]
    return previous[-1] if previous else None


def _render_archive_nav(
    entries: list[dict[str, object]],
    current_entry: dict[str, object] | None = None,
) -> str:
    if not entries:
        return ""
    grouped: dict[int, dict[int, list[dict[str, object]]]] = {}
    for entry in entries:
        year = int(entry["year"])
        month = int(entry["month"])
        grouped.setdefault(year, {}).setdefault(month, []).append(entry)

    years = []
    current_key = _archive_entry_key(current_entry) if current_entry else max(
        _archive_entry_key(entry) for entry in entries
    )
    for year in sorted(grouped, reverse=True):
        months = []
        for month in sorted(grouped[year], reverse=True):
            links = []
            for entry in sorted(grouped[year][month], key=lambda item: int(item["week"])):
                entry_key = (year, month, int(entry["week"]))
                current_class = ' class="is-current"' if entry_key == current_key else ""
                links.append(
                    f'<a{current_class} data-archive-link '
                    f'href="{escape(str(entry["href"]))}">'
                    f'{month:02d}월 {int(entry["week"])}째주</a>'
                )
            months.append(f'<div class="archive-month">{"".join(links)}</div>')
        years.append(
            f'<details class="archive-year-group" open>'
            f'<summary class="archive-year">{year}년</summary>'
            f'{"".join(months)}'
            f'</details>'
        )
    return (
        '<aside class="archive-nav" aria-label="주간 아카이브">'
        '<input class="archive-search" data-archive-search type="search" '
        'placeholder="검색어를 입력하세요..." aria-label="Archive 검색">'
        '<div class="archive-panel">'
        '<div class="archive-title">Archive</div>'
        + "".join(years)
        + "</div>"
        + '<div class="archive-resize" role="separator" aria-orientation="vertical" '
        + 'aria-label="Archive 너비 조절" tabindex="0"></div>'
        + "</aside>"
    )


def _render_editorial_homepage(
    today: str,
    infra_items: list[SiteItem],
    other_items: list[SiteItem],
    latest_tool_items: list[SiteItem],
    analytics_html: str,
    archive_entries: list[dict[str, object]] | None = None,
    current_archive_entry: dict[str, object] | None = None,
) -> str:
    all_items = [*infra_items, *other_items, *latest_tool_items]
    lead_item = (infra_items or other_items or latest_tool_items)[0] if all_items else None
    lead_summary = lead_item.summary if lead_item else "이번 주 AI 업무 업데이트를 선별해 보여줍니다."
    insight_cards = _render_smart_insight_cards(all_items)
    logo_roll = _render_logo_roll()
    archive_html = _render_archive_nav(archive_entries or [], current_entry=current_archive_entry)
    previous_archive = _previous_archive_entry(archive_entries or [], current_archive_entry)
    previous_week_button = (
        f'<a class="week-button" href="{escape(str(previous_archive["href"]))}">Previous Week</a>'
        if previous_archive
        else ""
    )
    period_label = str(current_archive_entry.get("period_label", "")) if current_archive_entry else ""
    date_label = f"{escape(today)} · {escape(period_label)}" if period_label else escape(today)
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
      --archive-width: 228px;
      --archive-gap: 64px;
    }}
    .page-shell {{
      position: relative;
    }}
    .archive-nav {{
      position: static;
      width: var(--archive-width);
      min-width: 180px;
      max-width: 380px;
      color: #111;
      font-size: 14px;
      line-height: 1.35;
      margin: 18px 0 18px;
    }}
    .archive-search {{
      height: 38px;
      width: 100%;
      display: block;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      color: #8a8a8a;
      background: rgba(255,255,255,.78);
      font-size: 12px;
      margin-bottom: 10px;
      outline: 0;
    }}
    .archive-search:focus {{
      border-color: #2f7fc0;
      box-shadow: 0 0 0 2px rgba(47,127,192,.12);
    }}
    .archive-panel {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,.78);
      min-height: 360px;
    }}
    .archive-title {{
      display: flex;
      gap: 8px;
      align-items: center;
      min-height: 42px;
      padding: 0 12px;
      border-bottom: 1px solid var(--line);
      font-size: 14px;
      font-weight: 800;
    }}
    .archive-title::before {{
      content: "";
      width: 10px;
      height: 12px;
      border-radius: 2px;
      border: 1px solid #777;
      background: #111;
      flex: 0 0 auto;
    }}
    .archive-year {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 12px 12px 6px;
      color: #555;
      font-size: 13px;
      cursor: pointer;
      list-style: none;
      user-select: none;
    }}
    .archive-year::-webkit-details-marker {{
      display: none;
    }}
    .archive-year::after {{
      content: "";
      width: 6px;
      height: 6px;
      border-right: 1px solid currentColor;
      border-bottom: 1px solid currentColor;
      color: #777;
      margin-left: 8px;
      transform: rotate(0deg);
      transition: transform .16s ease;
    }}
    .archive-year-group:not([open]) .archive-year::after {{
      transform: rotate(-45deg);
    }}
    .archive-year-group[open] .archive-year::after {{
      transform: rotate(45deg);
    }}
    .archive-month {{
      display: grid;
      gap: 0;
      font-size: 13px;
    }}
    .archive-month a {{
      display: block;
      padding: 11px 12px 11px 26px;
      color: #111;
      text-decoration: none;
      border-top: 1px solid rgba(0,0,0,.05);
    }}
    .archive-month a.is-current {{
      background: #2f7fc0;
      color: #fff;
      font-weight: 800;
    }}
    .archive-resize {{
      display: none;
    }}
    @media (min-width: 1100px) {{
      .page-shell {{
        width: min(960px, calc(100% - var(--archive-width) - var(--archive-gap) - 34px));
        margin-left: calc(var(--archive-width) + var(--archive-gap));
        margin-right: 32px;
      }}
      .archive-nav {{
        position: absolute;
        left: calc((var(--archive-width) + var(--archive-gap)) * -1);
        top: 76px;
        margin: 0;
        overflow: visible;
      }}
      .archive-resize {{
        position: absolute;
        top: 0;
        right: -10px;
        display: block;
        width: 12px;
        height: 100%;
        cursor: col-resize;
        touch-action: none;
      }}
      .archive-resize::after {{
        content: "";
        position: absolute;
        top: 48px;
        right: 4px;
        width: 2px;
        height: calc(100% - 48px);
        border-radius: 2px;
        background: transparent;
      }}
      .archive-resize:hover::after,
      .archive-resize:focus-visible::after,
      .archive-nav.is-resizing .archive-resize::after {{
        background: #2f7fc0;
      }}
    }}
    .archive-insight-mode .hero,
    .archive-insight-mode .logo-roll {{
      display: none;
    }}
    .archive-insight-mode .insights {{
      padding-top: 64px;
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
      gap: 8px;
    }}
    .week-button {{
      min-height: 32px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0 14px;
      border: 1px solid #111111;
      color: #111111;
      border-radius: 4px;
      font-weight: 800;
      font-size: 12px;
      background: #ffffff;
    }}
    .week-button:hover,
    .week-button:focus-visible {{
      background: #111111;
      color: #ffffff;
      outline: 0;
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
      min-height: 560px;
      display: grid;
      grid-template-rows: auto 1fr auto;
      padding: 70px 0 0;
    }}
    .hero h1 {{
      max-width: none;
      margin: 0;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(34px, 7vw, 92px);
      line-height: .98;
      font-weight: 700;
      letter-spacing: 0;
      white-space: nowrap;
      text-align: center;
    }}
    .hero h1 a {{
      color: inherit;
      text-decoration: none;
    }}
    .hero-image {{
      align-self: end;
      margin-top: 42px;
      overflow: hidden;
      border-radius: 20px;
      min-height: clamp(170px, 19vw, 230px);
      background:
        linear-gradient(rgba(0,0,0,.028) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,.024) 1px, transparent 1px),
        #f7f7f4;
      background-size: 34px 34px;
      border: 1px solid var(--line);
      padding: clamp(18px, 2.4vw, 30px);
    }}
    .talent-card {{
      min-width: 0;
    }}
    .talent-logo {{
      display: inline-flex;
      gap: 6px;
      align-items: baseline;
      font-family: Arial, "Noto Sans KR", sans-serif;
      font-size: clamp(18px, 1.9vw, 26px);
      font-weight: 900;
      letter-spacing: -.01em;
    }}
    .talent-logo .sk {{ color: #e21424; }}
    .talent-logo .ax {{ color: #ff8200; }}
    .talent-headline {{
      display: flex;
      align-items: baseline;
      gap: clamp(14px, 2.3vw, 30px);
      margin-top: 4px;
      min-width: 0;
    }}
    .talent-title {{
      margin: 0;
      color: #4f5f9a;
      font-family: Arial, "Noto Sans KR", sans-serif;
      font-size: clamp(34px, 4.35vw, 58px);
      line-height: .98;
      font-weight: 900;
      letter-spacing: 0;
      white-space: nowrap;
    }}
    .talent-dash {{
      color: #111;
      font-family: Arial, "Noto Sans KR", sans-serif;
      font-size: clamp(24px, 3.3vw, 44px);
      line-height: 1;
      font-weight: 900;
      white-space: nowrap;
    }}
    .talent-copy {{
      margin: 0;
      color: #111;
      font-family: "Noto Sans KR", Arial, sans-serif;
      font-size: clamp(18px, 2.15vw, 29px);
      line-height: 1.22;
      font-weight: 900;
      letter-spacing: 0;
      white-space: nowrap;
    }}
    .criteria-card {{
      margin-top: clamp(24px, 2.8vw, 34px);
    }}
    .criteria-card h2 {{
      margin: 0 0 12px;
      color: #111;
      font-family: "Noto Sans KR", Arial, sans-serif;
      font-size: clamp(16px, 1.55vw, 21px);
      line-height: 1.18;
      letter-spacing: 0;
      font-weight: 800;
    }}
    .criteria-card ul {{
      margin: 0;
      padding-left: 1.05em;
      display: grid;
      grid-template-columns: repeat(2, minmax(260px, 1fr));
      column-gap: clamp(24px, 4vw, 58px);
      row-gap: 7px;
      color: #111;
      font-family: "Noto Sans KR", Arial, sans-serif;
      font-size: clamp(13px, 1.35vw, 18px);
      line-height: 1.32;
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
    .tool-directory {{
      padding: 46px 0 56px;
      border-bottom: 1px solid var(--line);
    }}
    .tool-directory-header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(220px, 360px);
      gap: 28px;
      align-items: end;
      margin-bottom: 24px;
    }}
    .tool-directory h2 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(26px, 3vw, 42px);
      line-height: 1.05;
      letter-spacing: 0;
    }}
    .tool-directory-header p {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.65;
    }}
    .tool-list-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      border-top: 1px solid var(--line);
      border-left: 1px solid var(--line);
    }}
    .ai-tool-card {{
      min-height: 178px;
      padding: 18px;
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 18px;
    }}
    .ai-tool-card h3 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(20px, 2vw, 28px);
      line-height: 1.02;
      letter-spacing: 0;
    }}
    .ai-tool-card p {{
      margin: 8px 0 0;
      color: #565656;
      font-size: 13px;
      line-height: 1.58;
    }}
    .tool-meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .tool-chip {{
      border: 1px solid var(--line);
      background: #fff;
      padding: 4px 7px;
      color: #111;
      font-size: 11px;
      font-weight: 800;
      line-height: 1.25;
    }}
    .tool-action {{
      display: inline-block;
      margin-top: 12px;
      border: 1px solid #222;
      padding: 7px 9px;
      color: #111;
      font-size: 12px;
      font-weight: 800;
      line-height: 1.3;
      text-decoration: none;
    }}
    .tool-action:hover,
    .tool-action:focus-visible {{
      background: #111;
      color: #fff;
      outline: 0;
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
      display: flex;
      flex-direction: column;
      gap: 14px;
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
      margin: 0;
      flex: 0 0 auto;
    }}
    .card-heading {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 10px;
      flex-wrap: wrap;
    }}
    .card-title {{
      display: inline;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: 22px;
      letter-spacing: 0;
      font-weight: 700;
    }}
    .topic-badge {{
      display: inline-flex;
      align-items: center;
      min-height: 18px;
      border-radius: 999px;
      background: #ffe1ef;
      color: #b73572;
      padding: 0 8px;
      font-family: Arial, "Noto Sans KR", sans-serif;
      font-size: 10px;
      font-weight: 900;
      line-height: 1;
      letter-spacing: 0;
      white-space: nowrap;
    }}
    .topic-badge.trend {{
      background: #e7f2ff;
      color: #4772a6;
    }}
    .topic-badge.sub {{
      background: #fff0f7;
      color: #a84a77;
      border: 1px solid #ffd4e6;
    }}
    .topic-badge.trend + .topic-badge.sub {{
      background: #eef6ff;
      color: #5d7fa8;
      border-color: #d8e8fa;
    }}
    .insight-grid.has-selection .card-heading {{
      margin-bottom: 6px;
    }}
    .insight-grid.has-selection .card-title {{
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
    .detail-title-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }}
    .insight-detail h3 {{
      margin: 0;
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
    .detail-criteria {{
      margin: 24px 0 0;
      border-top: 1px solid rgba(0,0,0,.12);
      padding-top: 12px;
      color: #444;
      font-size: 13px;
      line-height: 1.55;
      max-width: 620px;
    }}
    .detail-source {{
      display: inline-block;
      margin-top: 10px;
      color: #111;
      font-size: 12px;
      font-weight: 800;
      line-height: 1.45;
      overflow-wrap: anywhere;
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
    .detail-footnotes {{
      display: grid;
      gap: 6px;
      margin: 8px 0 0;
      padding: 12px 0 0 18px;
      border-top: 1px solid rgba(0,0,0,.12);
      color: #565656;
      font-size: 12px;
      line-height: 1.55;
      max-width: 620px;
    }}
    .detail-footnotes-title {{
      display: block;
      margin: 22px 0 0;
      color: #111;
      font-size: 12px;
      font-weight: 900;
      line-height: 1.4;
    }}
    .detail-footnotes-title[hidden] {{
      display: none;
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
      .archive-nav {{ position: static; width: auto; padding: 20px 0 0; }}
      .archive-panel {{ min-height: auto; }}
      .archive-title {{ font-size: 14px; }}
      .archive-year {{ padding: 10px 12px 5px; font-size: 13px; }}
      .archive-month {{ font-size: 13px; }}
      .hero {{ min-height: auto; padding-top: 48px; }}
      .hero-image {{ border-radius: 14px; padding: 20px; }}
      .talent-headline {{ flex-wrap: wrap; gap: 6px 12px; }}
      .talent-dash {{ display: none; }}
      .talent-title,
      .talent-copy {{ white-space: normal; }}
      .criteria-card {{ margin-top: 24px; }}
      .criteria-card ul {{ grid-template-columns: 1fr; }}
      .intro-row,
      .tool-directory-header,
      .insight-grid {{
        grid-template-columns: 1fr;
      }}
      .tool-list-grid {{ grid-template-columns: 1fr; }}
      .insight-list,
      .insight-grid.has-selection,
      .insight-grid.has-selection .insight-list {{ grid-template-columns: 1fr; }}
      .insight-grid.has-selection {{ display: block; }}
      .insight-grid.has-selection .insight-list {{ display: block; }}
      .insight-detail {{
        position: static;
        min-height: 360px;
        margin: 14px 0 22px 36px;
        padding: 24px;
        width: calc(100% - 36px);
      }}
      .insight-grid.has-selection .insight-detail {{ display: flex; }}
      .insight-detail h3 {{ font-size: clamp(30px, 12vw, 44px); }}
      .date {{ text-align: left; }}
      .insight-card {{ min-height: 210px; }}
      .insight-grid.has-selection .insight-card {{ min-height: 112px; }}
      .footer {{ align-items: flex-start; flex-direction: column; gap: 12px; padding: 22px 0; }}
    }}
  </style>
</head>
<body>
  <main class="page page-shell">
    {archive_html}
    <header class="nav">
      <a class="brand" href="./">AI MASTER TIMES</a>
      <nav class="nav-links" aria-label="Primary">
        <a href="#insights">업무 AI</a>
        <a href="ai-tools/">AI 도구</a>
      </nav>
      <div class="nav-actions">
        {previous_week_button}
        <a class="button" href="#insights">Read This Week</a>
      </div>
    </header>
    <section class="hero" aria-label="Hero">
      <h1><a href="./" aria-label="AI MASTER TIMES 첫 화면으로 이동">AI MASTER TIMES</a></h1>
      <section class="hero-image" aria-label="AI Talent Lab pass criteria">
        <div class="talent-card">
          <div class="talent-logo"><span class="sk">SK</span><span class="ax">AX</span></div>
          <div class="talent-headline">
            <div class="talent-title">AI Talent Lab</div>
            <div class="talent-dash">-</div>
            <p class="talent-copy">당신의 AI 역량을 성장시켜보세요</p>
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
        <div class="date">{date_label} · curated weekly for AI Master teams</div>
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
  <script>
    (() => {{
      const shell = document.querySelector(".page-shell");
      const archive = document.querySelector(".archive-nav");
      const handle = document.querySelector(".archive-resize");
      if (!shell || !archive || !handle) return;

      const storageKey = "aimstletter.archiveWidth";
      const minWidth = 180;
      const maxWidth = 380;

      const setWidth = (value) => {{
        const width = Math.max(minWidth, Math.min(maxWidth, Math.round(value)));
        shell.style.setProperty("--archive-width", `${{width}}px`);
        handle.setAttribute("aria-valuenow", String(width));
        return width;
      }};

      const savedWidth = Number(window.localStorage.getItem(storageKey));
      if (Number.isFinite(savedWidth) && savedWidth > 0) {{
        setWidth(savedWidth);
      }}

      const startResize = (event) => {{
        if (!window.matchMedia("(min-width: 1100px)").matches) return;
        event.preventDefault();
        archive.classList.add("is-resizing");
        const startX = event.clientX;
        const startWidth = archive.getBoundingClientRect().width;

        const onMove = (moveEvent) => {{
          const width = setWidth(startWidth + moveEvent.clientX - startX);
          window.localStorage.setItem(storageKey, String(width));
        }};

        const onUp = () => {{
          archive.classList.remove("is-resizing");
          window.removeEventListener("pointermove", onMove);
          window.removeEventListener("pointerup", onUp);
        }};

        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
      }};

      handle.setAttribute("aria-valuemin", String(minWidth));
      handle.setAttribute("aria-valuemax", String(maxWidth));
      handle.addEventListener("pointerdown", startResize);
      handle.addEventListener("keydown", (event) => {{
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        const step = event.shiftKey ? 24 : 12;
        const currentWidth = archive.getBoundingClientRect().width;
        const width = setWidth(currentWidth + (event.key === "ArrowRight" ? step : -step));
        window.localStorage.setItem(storageKey, String(width));
      }});

      const search = document.querySelector("[data-archive-search]");
      const archiveLinks = Array.from(document.querySelectorAll("[data-archive-link]"));
      const smartInsightLinks = Array.from(document.querySelectorAll('a[href="#insights"]'));
      const insightCards = Array.from(document.querySelectorAll("[data-insight-card]"));
      const insightDetail = document.querySelector(".insight-detail");
      const insights = document.querySelector("#insights");
      const normalize = (value) => (value || "").toLowerCase().replace(/\\s+/g, " ").trim();

      const showArchiveInsights = (scroll = true) => {{
        shell.classList.add("archive-insight-mode");
        if (scroll && insights) {{
          insights.scrollIntoView({{ block: "start" }});
        }}
      }};

      const cardMatches = (card, query) => {{
        const text = normalize([
          card.dataset.number,
          card.dataset.title,
          card.dataset.category,
          card.dataset.subcategory,
          card.dataset.body,
          card.dataset.detail,
          card.dataset.meta,
          card.dataset.points,
          card.dataset.tags,
          card.textContent,
        ].join(" "));
        return !query || text.includes(query);
      }};

      const selectFirstVisibleCard = () => {{
        const firstVisible = insightCards.find((card) => !card.hidden);
        if (insightDetail) insightDetail.hidden = !firstVisible;
        if (firstVisible) firstVisible.click();
      }};

      const clearInsightSelection = () => {{
        insightCards.forEach((card) => card.classList.remove("is-active"));
        if (insightDetail) insightDetail.hidden = true;
      }};

      archiveLinks.forEach((link) => {{
        link.addEventListener("click", (event) => {{
          const target = new URL(link.href, window.location.href);
          if (target.origin === window.location.origin && target.pathname === window.location.pathname) {{
            event.preventDefault();
            window.history.pushState(null, "", "#insights");
            showArchiveInsights();
            clearInsightSelection();
          }} else {{
            window.sessionStorage.setItem("aimstletter.archiveInsightsOnly", "1");
          }}
        }});
      }});

      smartInsightLinks.forEach((link) => {{
        link.addEventListener("click", (event) => {{
          event.preventDefault();
          shell.classList.remove("archive-insight-mode");
          window.history.pushState(null, "", "#insights");
          if (insights) insights.scrollIntoView({{ block: "start" }});
          selectFirstVisibleCard();
        }});
      }});

      if (search) {{
        search.addEventListener("input", () => {{
          const query = normalize(search.value);
          archiveLinks.forEach((link) => {{
            link.hidden = Boolean(query) && !normalize(link.textContent).includes(query);
          }});
          insightCards.forEach((card) => {{
            card.hidden = !cardMatches(card, query);
          }});
          if (query) showArchiveInsights(false);
          clearInsightSelection();
        }});
      }}

      if (
        window.location.hash === "#insights" ||
        window.sessionStorage.getItem("aimstletter.archiveInsightsOnly") === "1"
      ) {{
        window.sessionStorage.removeItem("aimstletter.archiveInsightsOnly");
        showArchiveInsights(false);
        clearInsightSelection();
      }}
    }})();
  </script>
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
    archive_entries: list[dict[str, object]] | None = None,
    current_archive_entry: dict[str, object] | None = None,
) -> str:
    return _render_editorial_homepage(
        today,
        infra_items,
        other_items,
        latest_tool_items,
        analytics_html,
        archive_entries=archive_entries or [],
        current_archive_entry=current_archive_entry,
    )

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


def _smart_insight_category(index: int) -> str:
    trend_indexes = {4, 6, 7, 11, 13}
    return "동향" if index in trend_indexes else "기술"


def _smart_insight_subcategory(index: int) -> str:
    labels = (
        "AI 인프라",
        "풀스택",
        "AI 인프라",
        "프론트엔드",
        "SDLC",
        "백엔드",
        "운영",
        "배포",
        "백엔드",
        "품질평가",
        "백엔드",
        "관측",
        "보안",
        "조직지식",
    )
    return labels[index] if index < len(labels) else "기타"


def _smart_insight_source_url(index: int) -> str:
    urls = (
        "https://www.anthropic.com/research/building-effective-agents",
        "https://stitch.withgoogle.com/",
        "https://www.anthropic.com/engineering/writing-tools-for-agents",
        "https://www.prisma.io/docs/orm",
        "https://developer.harness.io/docs/continuous-delivery/",
        "https://docs.langchain.com/langgraph-platform/",
        "https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview",
        "https://vercel.com/docs",
        "https://docs.litellm.ai/docs/simple_proxy",
        "https://developers.openai.com/api/docs/guides/evals",
        "https://docs.llamaindex.ai/",
        "https://opentelemetry.io/docs/",
        "https://developer.hashicorp.com/vault/docs",
        "https://docs.github.com/en/issues",
    )
    return urls[index] if index < len(urls) else ""



def _smart_insight_category(item: SiteItem) -> str:
    if item.kind in {"paper", "논문"}:
        return "논문"
    if "도구" in item.kind or item.kind == "tool":
        return "도구"
    return "동향"


def _smart_insight_subcategory(item: SiteItem) -> str:
    return item.tags[0] if item.tags else item.source


def _render_smart_insight_cards(items: list[SiteItem]) -> str:
    entries = []
    for index, item in enumerate(items):
        title = _clip(item.title, 78)
        body = _clip(item.summary, 150)
        detail = item.detail or item.summary
        points = item.key_points or (item.summary,)
        footnotes = item.glossary
        meta = f"{item.source} · {item.kind} · {_format_date(item.published)}"
        tags = item.tags
        criteria = "선별기준 : 해당 주간 수집 데이터에서 날짜, 출처, 업무 적용 가능성을 기준으로 선별된 실제 업데이트입니다."
        source_url = item.url
        category = _smart_insight_category(item)
        subcategory = _smart_insight_subcategory(item)
        entries.append((index + 1, title, body, detail, meta, points, tags, criteria, source_url, category, subcategory, footnotes))

    if not entries:
        return ""

    cards = []
    for (number, title, body, detail, meta, points, tags, criteria, source_url, category, subcategory, footnotes) in entries:
        badge_class = " trend" if category == "동향" else ""
        cards.append(
            '<button class="insight-card" type="button" '
            f'data-insight-card data-number="{number}" '
            f'data-title="{escape(title, quote=True)}" '
            f'data-category="{escape(category, quote=True)}" '
            f'data-subcategory="{escape(subcategory, quote=True)}" '
            f'data-body="{escape(body, quote=True)}" '
            f'data-detail="{escape(_clip(detail, 700), quote=True)}" '
            f'data-meta="{escape(meta, quote=True)}" '
            f'data-points="{escape(json.dumps(list(points[:4]), ensure_ascii=False), quote=True)}" '
            f'data-tags="{escape(json.dumps(list(tags[:6]), ensure_ascii=False), quote=True)}" '
            f'data-criteria="{escape(criteria, quote=True)}" '
            f'data-footnotes="{escape(json.dumps(list(footnotes[:5]), ensure_ascii=False), quote=True)}" '
            f'data-source="{escape(source_url, quote=True)}">'
            '<span><span class="card-heading">'
            f'<span class="card-icon">{number}</span>'
            f'<span class="card-title">{escape(title)}</span>'
            f'<span class="topic-badge{badge_class}">{escape(category)}</span>'
            f'<span class="topic-badge sub">{escape(subcategory)}</span>'
            f'</span><p>{escape(body)}</p></span>'
            '</button>'
        )

    (first_number, first_title, first_body, first_detail, first_meta, first_points, first_tags, first_criteria, first_source_url, first_category, first_subcategory, first_footnotes) = entries[0]
    first_badge_class = " trend" if first_category == "동향" else ""
    return (
        '<div class="insight-list">'
        + "\n".join(cards)
        + "</div>"
        + '<article class="insight-detail" aria-live="polite">'
        + "<div>"
        + f'<div class="detail-number" data-insight-number>{first_number}</div>'
        + f'<div class="detail-meta" data-insight-meta>{escape(first_meta)}</div>'
        + '<div class="detail-title-row">'
        + f'<h3 data-insight-title>{escape(first_title)}</h3>'
        + f'<span class="topic-badge{first_badge_class}" data-insight-category>{escape(first_category)}</span>'
        + f'<span class="topic-badge sub" data-insight-subcategory>{escape(first_subcategory)}</span>'
        + '</div>'
        + f'<p class="detail-summary" data-insight-body>{escape(first_body)}</p>'
        + f'<p class="detail-copy" data-insight-detail>{escape(_clip(first_detail, 700))}</p>'
        + '<ul class="detail-points" data-insight-points>'
        + "".join(f"<li>{escape(point)}</li>" for point in first_points[:4])
        + "</ul>"
        + '<div class="detail-footnotes-title" data-insight-footnotes-title'
        + (" hidden" if not first_footnotes else "")
        + ">단어 설명</div>"
        + '<ol class="detail-footnotes" data-insight-footnotes>'
        + "".join(f"<li>{escape(note)}</li>" for note in first_footnotes[:5])
        + "</ol>"
        + f'<p class="detail-criteria" data-insight-criteria>{escape(first_criteria)}</p>'
        + f'<a class="detail-source" data-insight-source href="{escape(first_source_url or "#")}" target="_blank" rel="noopener noreferrer"'
        + (" hidden" if not first_source_url else "")
        + f'>{escape(first_source_url)}</a>'
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
  const category = document.querySelector('[data-insight-category]');
  const subcategory = document.querySelector('[data-insight-subcategory]');
  const body = document.querySelector('[data-insight-body]');
  const detail = document.querySelector('[data-insight-detail]');
  const meta = document.querySelector('[data-insight-meta]');
  const points = document.querySelector('[data-insight-points]');
  const tags = document.querySelector('[data-insight-tags]');
  const footnotes = document.querySelector('[data-insight-footnotes]');
  const footnotesTitle = document.querySelector('[data-insight-footnotes-title]');
  const criteria = document.querySelector('[data-insight-criteria]');
  const source = document.querySelector('[data-insight-source]');
  const grid = document.querySelector('[data-insight-grid]');
  const detailPanel = document.querySelector('.insight-detail');
  const insightList = document.querySelector('.insight-list');
  const mobileQuery = window.matchMedia('(max-width: 760px)');
  if (!buttons.length || !number || !title || !category || !subcategory || !body || !detail || !meta || !points || !tags || !footnotes || !footnotesTitle || !criteria || !source || !grid || !detailPanel || !insightList) return;

  const placeDetailPanel = (button) => {
    if (mobileQuery.matches) {
      button.insertAdjacentElement('afterend', detailPanel);
    } else {
      grid.appendChild(detailPanel);
    }
  };

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      grid.classList.add('has-selection');
      buttons.forEach((item) => item.classList.remove('is-active'));
      button.classList.add('is-active');
      placeDetailPanel(button);
      number.textContent = button.dataset.number || '';
      title.textContent = button.dataset.title || '';
      category.textContent = button.dataset.category || '';
      category.classList.toggle('trend', button.dataset.category === '동향');
      subcategory.textContent = button.dataset.subcategory || '';
      body.textContent = button.dataset.body || '';
      detail.textContent = button.dataset.detail || '';
      meta.textContent = button.dataset.meta || '';
      criteria.textContent = button.dataset.criteria || '';
      const sourceUrl = button.dataset.source || '';
      source.textContent = sourceUrl;
      source.hidden = !sourceUrl;
      if (sourceUrl && source instanceof HTMLAnchorElement) source.href = sourceUrl;

      let pointItems = [];
      let tagItems = [];
      let footnoteItems = [];
      try { pointItems = JSON.parse(button.dataset.points || '[]'); } catch (error) { pointItems = []; }
      try { tagItems = JSON.parse(button.dataset.tags || '[]'); } catch (error) { tagItems = []; }
      try { footnoteItems = JSON.parse(button.dataset.footnotes || '[]'); } catch (error) { footnoteItems = []; }
      footnotesTitle.hidden = footnoteItems.length === 0;
      points.replaceChildren(...pointItems.map((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        return li;
      }));
      footnotes.replaceChildren(...footnoteItems.map((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        return li;
      }));
      tags.replaceChildren(...tagItems.map((item) => {
        const tag = document.createElement('span');
        tag.className = 'detail-tag';
        tag.textContent = '#' + item;
        return tag;
      }));
    });
  });

  mobileQuery.addEventListener('change', () => {
    const active = document.querySelector('[data-insight-card].is-active');
    if (active instanceof HTMLElement) {
      placeDetailPanel(active);
    } else if (!mobileQuery.matches) {
      grid.appendChild(detailPanel);
    } else {
      insightList.appendChild(detailPanel);
    }
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
    if index == 0:
        return (
            "AI 실행을 업무에 붙이기 위한 운영 계층입니다. 모델 호출, 도구 사용, 권한, "
            "검증, 기록을 한 흐름으로 묶어 안전하게 반복 실행하도록 설계합니다."
        )
    if index % 2 == 0 and item:
        return f"{fallback} 이번 주 관련 신호: {_clip(item.summary, 110)}"
    return fallback


def _smart_insight_detail(
    index: int,
    item: SiteItem | None,
    fallback: str,
) -> tuple[str, tuple[str, ...]]:
    if index == 0:
        return (
            "하네스 엔지니어링은 AI 모델의 답변을 실제 업무 실행으로 연결하기 위한 운영 설계입니다. "
            "프롬프트만 잘 쓰는 것을 넘어, 모델이 어떤 도구를 호출하고 어떤 조건에서 실행되며 "
            "어떤 로그와 검증을 남기는지까지 관리합니다.",
            (
                "1. 하네스 엔지니어링이란? 모델, 도구, 데이터, 권한, 검증 로직을 묶어 AI 작업을 반복 가능한 실행 흐름으로 만드는 방식입니다.",
                "2. 프롬프트 엔지니어링과의 차이점: 프롬프트 엔지니어링이 모델 입력을 다듬는 일이라면, 하네스 엔지니어링은 실행 환경과 통제 장치를 설계하는 일입니다.",
                "3. 주요 구성 요소: 입력 스키마, 도구 호출 규칙, 권한 경계, 평가 기준, 감사 로그, 실패 시 재시도와 롤백 정책입니다.",
            ),
        )
    if item:
        return item.detail, item.key_points
    return fallback, ()


def _smart_insight_blueprint() -> tuple[tuple[str, str], ...]:
    return (
        ("Harness Engineering", "AI가 답을 내는 것에서 끝나지 않고, 실제 업무 도구를 안전하게 실행하도록 돕는 운영 방식입니다."),
        ("AI Product Builder Stack", "아이디어를 화면, 데이터베이스, 로그인, 배포까지 이어서 빠르게 시험해 볼 수 있는 AI 제품 제작 도구 묶음입니다."),
        ("Agent Harness", "AI 에이전트가 아무 도구나 바로 실행하지 못하게, 중간에서 확인하고 허락한 작업만 실행하게 만드는 안전 구조입니다."),
        ("Design System to Backend", "디자인 규칙과 데이터 구조를 함께 맞춰서, 예쁜 화면이 실제 서비스 기능과 자연스럽게 연결되게 하는 방식입니다."),
        ("AI Software Delivery", "AI를 코드 작성뿐 아니라 테스트, 보안 확인, 배포, 운영 점검까지 넓게 쓰는 개발 전달 방식입니다."),
        ("Workflow and Data Layer", "AI 작업을 한 번의 질문으로 끝내지 않고, 저장·검색·재시도까지 가능한 업무 흐름으로 만드는 기반입니다."),
        ("Production Agent Guardrails", "실제 서비스에서 AI 에이전트가 실수해도 큰 문제가 나지 않도록 권한, 기록, 승인 단계를 두는 안전장치입니다."),
        ("Deployable AI App Path", "AI로 만든 아이디어를 사용자가 접속할 수 있는 앱으로 배포하기까지의 제작 순서입니다."),
        ("Model Gateway and Routing", "여러 AI 모델을 한 곳에서 불러 쓰고, 비용이나 성능에 따라 알맞은 모델을 고르는 운영 계층입니다."),
        ("AI Evaluation Stack", "AI 답변이 좋아졌는지 나빠졌는지 느낌이 아니라 테스트와 점수로 확인하는 평가 체계입니다."),
        ("RAG and Knowledge Backend", "사내 문서나 수업 자료를 AI가 찾아보고 근거로 사용할 수 있게 만드는 지식 검색 백엔드입니다."),
        ("Observability and Incident AI", "AI 기능에서 오류, 느려짐, 비용 증가가 생겼을 때 원인을 빨리 찾도록 돕는 관측 체계입니다."),
        ("Secure Secrets and Policy", "API 키와 권한 규칙을 따로 관리해 AI와 서버가 필요한 정보에만 접근하게 하는 보안 방식입니다."),
        ("Team Knowledge Workflow", "팀의 이슈, 회의 내용, 릴리즈 노트를 AI가 다시 활용할 수 있도록 정리하는 지식 관리 흐름입니다."),
    )


def _smart_insight_body(index: int, item: SiteItem | None, fallback: str) -> str:
    return fallback


def _smart_insight_detail(
    index: int,
    item: SiteItem | None,
    fallback: str,
) -> tuple[str, tuple[str, ...]]:
    explainers: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "하네스 엔지니어링은 AI가 말로만 답하는 단계에서 벗어나 실제 업무를 안전하게 실행하도록 만드는 설계입니다. 예를 들어 AI가 보고서를 만들거나 배포 명령을 실행해야 한다면, 어떤 도구를 쓸 수 있는지, 누가 허락해야 하는지, 실패하면 어떻게 되돌릴지를 미리 정합니다.",
            (
                "AI가 사용할 도구 목록과 실행 조건을 미리 정하면 반복 업무를 자동화하기 쉽습니다.",
                "실행 기록과 승인 단계를 남기면 사고가 났을 때 원인을 추적할 수 있습니다.",
                "업무 적용 예: 보고서 생성, 배포 점검, 고객 문의 분류, 장애 대응 초안 작성.",
            ),
        ),
        (
            "AI Product Builder Stack은 AI 제품을 만들 때 필요한 도구들을 한 줄로 연결해 보는 관점입니다. 화면을 빠르게 만들고, 데이터를 저장하고, 로그인과 배포까지 붙이면 아이디어를 실제로 써볼 수 있는 작은 제품으로 바꿀 수 있습니다.",
            (
                "화면 제작 도구만 쓰면 시안에서 멈추지만, 백엔드와 배포를 붙이면 실제 사용 테스트가 가능합니다.",
                "수업이나 사내 파일럿에서는 작게 만들고 빠르게 피드백을 받는 데 유용합니다.",
                "업무 적용 예: 신청 폼, 사내 FAQ 봇, 간단한 대시보드, 데이터 입력 도구.",
            ),
        ),
        (
            "Agent Harness는 AI 에이전트와 실제 시스템 사이에 두는 안전한 중간 계층입니다. AI가 직접 서버나 데이터베이스를 만지지 않고, 하네스가 입력을 확인한 뒤 허용된 도구만 실행하게 합니다.",
            (
                "에이전트가 실수로 위험한 명령을 실행하는 일을 줄일 수 있습니다.",
                "결과 검증과 에러 처리를 한 곳에서 관리하면 운영하기 편합니다.",
                "업무 적용 예: 티켓 처리, 데이터 조회, 반복 점검, 자동 알림 생성.",
            ),
        ),
        (
            "Design System to Backend는 화면 디자인 규칙과 데이터 구조를 함께 관리하는 방식입니다. AI가 만든 화면이 보기만 좋은 시안으로 끝나지 않고, 실제 데이터 입력과 API 호출까지 자연스럽게 이어지게 합니다.",
            (
                "디자인 규칙을 문서화하면 AI가 매번 다른 스타일로 화면을 만드는 문제를 줄입니다.",
                "데이터 구조를 함께 정하면 폼, 표, 상세 화면이 실제 기능과 맞습니다.",
                "업무 적용 예: 관리자 화면, 고객 정보 입력, 리포트 페이지, 승인 워크플로.",
            ),
        ),
        (
            "AI Software Delivery는 AI를 코드 작성에만 쓰지 않고, 테스트와 배포, 보안 점검, 운영 확인까지 연결하는 방식입니다. 실제 서비스는 코드를 만드는 것보다 안전하게 출시하고 계속 관리하는 일이 더 중요하기 때문입니다.",
            (
                "AI가 테스트 실패 원인을 요약하거나 배포 전 체크리스트를 만들 수 있습니다.",
                "출시 후 오류와 비용을 함께 확인하면 운영 품질을 높일 수 있습니다.",
                "업무 적용 예: 자동 테스트, 보안 스캔, 배포 승인, 장애 보고서 초안.",
            ),
        ),
        (
            "Workflow and Data Layer는 AI 작업을 한 번의 답변으로 끝내지 않고, 여러 단계의 업무 흐름으로 운영하기 위한 기반입니다. 긴 작업을 나누고, 중간 상태를 저장하고, 실패하면 다시 시도하게 만들 수 있습니다.",
            (
                "작업 상태를 저장하면 중간에 실패해도 처음부터 다시 시작하지 않아도 됩니다.",
                "문서 검색과 데이터 저장을 붙이면 AI가 이전 정보를 이어서 사용할 수 있습니다.",
                "업무 적용 예: 정기 보고서 생성, 신청 처리, 문서 검색, 고객 상담 흐름.",
            ),
        ),
        (
            "Production Agent Guardrails는 실제 서비스에서 AI 에이전트가 정해진 범위 안에서만 행동하게 만드는 안전 체계입니다. AI가 틀릴 수 있다는 전제를 두고 권한, 승인, 기록, 되돌리기 방법을 준비합니다.",
            (
                "위험한 작업은 사람 승인 후 실행하게 만들 수 있습니다.",
                "기록을 남기면 누가 어떤 명령을 실행했는지 확인할 수 있습니다.",
                "업무 적용 예: 결제 변경, 배포 승인, 고객 데이터 수정, 보안 알림 처리.",
            ),
        ),
        (
            "Deployable AI App Path는 아이디어를 실제 접속 가능한 AI 앱으로 만드는 순서입니다. 디자인, 코드, 서버, 데이터베이스, 배포 주소까지 이어져야 다른 사람이 직접 써볼 수 있습니다.",
            (
                "프로토타입에서 끝내지 않고 배포까지 가야 실제 피드백을 받을 수 있습니다.",
                "작은 앱이라도 로그인, 데이터 저장, 오류 확인을 준비하면 더 오래 쓸 수 있습니다.",
                "업무 적용 예: 수업용 실습 앱, 사내 도구, 예약 폼, 간단한 챗봇.",
            ),
        ),
        (
            "Model Gateway and Routing은 여러 AI 모델을 한 창구에서 관리하는 방식입니다. 요청이 쉬운지 어려운지, 비용을 줄여야 하는지에 따라 알맞은 모델로 보내는 길잡이 역할을 합니다.",
            (
                "한 모델에 장애가 나면 다른 모델로 바꿔 보내는 fallback을 만들 수 있습니다.",
                "요청별 비용과 품질을 기록하면 운영 판단이 쉬워집니다.",
                "업무 적용 예: 고객 문의 분류는 저렴한 모델, 복잡한 분석은 성능 좋은 모델 사용.",
            ),
        ),
        (
            "AI Evaluation Stack은 AI 답변 품질을 느낌이 아니라 테스트와 점수로 확인하는 체계입니다. 프롬프트를 바꾼 뒤 답변이 더 좋아졌는지, 예전보다 실수가 늘었는지를 비교할 수 있습니다.",
            (
                "자주 틀리는 질문 목록을 만들어 두면 수정 효과를 반복해서 확인할 수 있습니다.",
                "출시 전후의 답변 품질을 비교하면 조용한 품질 하락을 잡을 수 있습니다.",
                "업무 적용 예: 챗봇 답변 평가, 문서 검색 정확도 확인, 프롬프트 변경 테스트.",
            ),
        ),
        (
            "RAG and Knowledge Backend는 사내 문서와 지식을 AI가 찾아보고 답변 근거로 쓰게 만드는 구조입니다. AI가 기억만으로 답하지 않고, 실제 문서에서 관련 내용을 검색해 답변하도록 돕습니다.",
            (
                "근거 문서를 함께 보여주면 사용자가 답변을 더 쉽게 검증할 수 있습니다.",
                "규정, 매뉴얼, 수업 자료처럼 자주 찾아보는 문서에 특히 유용합니다.",
                "업무 적용 예: 사내 규정 Q&A, 기술 문서 검색, 교육 자료 챗봇.",
            ),
        ),
        (
            "Observability and Incident AI는 AI 기능이 왜 느려졌는지, 왜 틀린 답을 했는지, 비용이 왜 늘었는지 추적하는 운영 체계입니다. 문제가 생겼을 때 원인을 빠르게 좁히는 데 도움이 됩니다.",
            (
                "AI 호출 기록과 서버 오류를 함께 보면 문제 원인을 찾기 쉽습니다.",
                "비용과 지연 시간을 같이 보면 어떤 기능을 개선해야 할지 보입니다.",
                "업무 적용 예: 장애 알림 요약, 느린 요청 분석, 비용 급증 원인 찾기.",
            ),
        ),
        (
            "Secure Secrets and Policy는 AI 앱이 쓰는 비밀번호 같은 키와 권한 규칙을 안전하게 관리하는 방식입니다. 코드 안에 중요한 값을 넣지 않고, 누가 어떤 정보에 접근할 수 있는지 따로 정합니다.",
            (
                "API 키를 코드에 직접 넣지 않으면 유출 위험을 줄일 수 있습니다.",
                "정책 규칙을 분리하면 에이전트가 필요한 권한만 쓰게 만들 수 있습니다.",
                "업무 적용 예: 키 관리, 접근 권한 설정, 보안 감사 기록, 정책 검사.",
            ),
        ),
        (
            "Team Knowledge Workflow는 팀의 대화, 이슈, 문서, 릴리즈 기록을 AI가 다시 사용할 수 있게 정리하는 방식입니다. 흩어진 정보를 모으면 새 팀원이 맥락을 빨리 파악하고, AI도 더 정확하게 도울 수 있습니다.",
            (
                "이슈와 회의 내용을 요약하면 나중에 같은 질문을 반복하지 않아도 됩니다.",
                "릴리즈 기록을 정리하면 어떤 기능이 언제 바뀌었는지 추적하기 쉽습니다.",
                "업무 적용 예: 회의 요약, 이슈 정리, 릴리즈 노트 작성, 온보딩 자료 생성.",
            ),
        ),
    )
    if index < len(explainers):
        return explainers[index]
    return fallback, item.key_points if item else ()


def _smart_insight_footnotes(index: int) -> tuple[str, ...]:
    footnotes: tuple[tuple[str, ...], ...] = (
        (
            "하네스: AI와 실제 도구 사이에서 실행 순서, 권한, 검증을 관리하는 중간 장치입니다.",
            "프롬프트: AI에게 원하는 답을 얻기 위해 입력하는 지시문입니다.",
            "롤백: 문제가 생겼을 때 이전 상태로 되돌리는 작업입니다.",
        ),
        (
            "스택: 제품을 만들 때 함께 쓰는 도구와 기술의 묶음입니다.",
            "백엔드: 화면 뒤에서 데이터 저장, 로그인, 계산, API 처리를 담당하는 서버 영역입니다.",
            "배포: 만든 서비스를 다른 사람이 접속할 수 있는 환경에 올리는 일입니다.",
        ),
        (
            "에이전트: 목표를 받고 스스로 여러 단계를 수행하는 AI 프로그램입니다.",
            "스키마: 입력과 출력의 형식을 미리 정해 둔 규칙입니다.",
            "권한: 어떤 사용자나 프로그램이 무엇을 할 수 있는지 정한 허용 범위입니다.",
        ),
        (
            "디자인 시스템: 색, 글자, 버튼, 여백 같은 화면 규칙을 모아 둔 기준입니다.",
            "API: 프로그램끼리 데이터를 주고받기 위해 정한 약속입니다.",
            "데이터 모델: 서비스에서 저장해야 할 정보의 구조입니다.",
        ),
        (
            "SDLC: 소프트웨어를 계획, 개발, 테스트, 배포, 운영하는 전체 과정입니다.",
            "CI/CD: 코드 변경을 자동으로 테스트하고 배포하는 개발 절차입니다.",
            "보안 스캔: 코드나 설정에 위험한 부분이 있는지 자동으로 검사하는 작업입니다.",
        ),
        (
            "워크플로: 여러 작업을 순서대로 연결한 업무 흐름입니다.",
            "벡터 저장소: 문서의 의미를 숫자로 바꿔 저장하고 비슷한 내용을 찾는 저장소입니다.",
            "재시도 정책: 실패한 작업을 언제, 몇 번 다시 실행할지 정한 규칙입니다.",
        ),
        (
            "가드레일: AI가 위험한 행동을 하지 않도록 세운 제한 규칙입니다.",
            "감사 로그: 누가 언제 무엇을 했는지 확인할 수 있게 남긴 기록입니다.",
            "승인 절차: 중요한 작업 전에 사람이 확인하고 허락하는 단계입니다.",
        ),
        (
            "프로토타입: 아이디어를 빠르게 확인하기 위해 만든 초기 버전입니다.",
            "호스팅: 웹사이트나 앱을 인터넷에서 접속할 수 있게 운영하는 일입니다.",
            "인증: 사용자가 누구인지 확인하는 로그인 절차입니다.",
        ),
        (
            "게이트웨이: 여러 서비스로 가는 요청을 한 곳에서 받아 나누어 보내는 입구입니다.",
            "라우팅: 조건에 따라 요청을 알맞은 목적지로 보내는 일입니다.",
            "fallback: 기본 방법이 실패했을 때 쓰는 대체 방법입니다.",
        ),
        (
            "평가 데이터셋: AI 답변을 시험하기 위해 미리 준비한 질문과 정답 묶음입니다.",
            "회귀 테스트: 수정 후 예전에 되던 기능이 망가지지 않았는지 확인하는 테스트입니다.",
            "RAG: AI가 외부 문서를 검색해 근거를 붙여 답하게 하는 방식입니다.",
        ),
        (
            "임베딩: 문장이나 문서의 의미를 숫자 배열로 바꾸는 기술입니다.",
            "벡터 검색: 단어가 완전히 같지 않아도 의미가 비슷한 내용을 찾는 검색 방식입니다.",
            "출처 추적: 답변이 어떤 문서나 근거에서 나왔는지 확인하는 방식입니다.",
        ),
        (
            "관측: 서비스가 어떻게 동작하는지 로그와 지표로 살펴보는 일입니다.",
            "메트릭: 응답 시간, 오류 수, 비용처럼 숫자로 측정하는 값입니다.",
            "트레이스: 요청 하나가 시스템 안에서 지나간 경로를 따라가는 기록입니다.",
        ),
        (
            "시크릿: API 키나 비밀번호처럼 외부에 노출되면 안 되는 값입니다.",
            "정책: 어떤 조건에서 접근을 허용하거나 막을지 정한 규칙입니다.",
            "감사: 보안과 규칙 준수 여부를 나중에 확인하는 과정입니다.",
        ),
        (
            "이슈: 해야 할 일이나 버그를 기록하고 추적하는 작업 단위입니다.",
            "릴리즈 노트: 새 버전에서 무엇이 바뀌었는지 정리한 문서입니다.",
            "온보딩: 새 사람이 팀이나 도구에 적응하도록 돕는 과정입니다.",
        ),
    )
    return footnotes[index] if index < len(footnotes) else ()


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


def _render_ai_tool_directory() -> str:
    groups = (
        (
            "개발·코딩 에이전트",
            "코드 작성, 리팩터링, 리뷰, 테스트 보조처럼 개발 작업을 직접 돕는 도구입니다.",
            (
                ("Codex", "코드 작성, 수정, 리뷰, 테스트 보조에 쓰는 AI 코딩 에이전트입니다.", ("코딩", "리뷰", "자동화"), "https://developers.openai.com/codex/cli"),
                ("Claude Code", "터미널과 코드베이스 안에서 Claude를 실행해 기능 구현과 리팩터링을 진행하는 도구입니다.", ("코딩", "리팩터링", "터미널"), "https://code.claude.com/docs/en/desktop-quickstart"),
                ("Cursor", "에디터 안에서 코드 이해, 생성, 수정, 대화형 개발을 함께 수행하는 AI 코드 편집기입니다.", ("IDE", "코드 생성", "맥락 이해"), "https://cursor.com/download"),
                ("GitHub Copilot", "IDE와 GitHub 작업 흐름에서 코드 추천, PR 보조, 이슈 처리를 돕는 개발 도구입니다.", ("IDE", "PR", "협업"), "https://github.com/features/copilot"),
                ("Windsurf", "프로젝트 맥락을 읽고 여러 파일을 함께 수정하는 AI 개발 환경입니다.", ("개발환경", "멀티파일", "에이전트"), "https://windsurf.com/"),
            ),
        ),
        (
            "앱 제작·프로토타입",
            "아이디어를 빠르게 화면, 기능, 배포 가능한 앱으로 바꾸는 제작 도구입니다.",
            (
                ("Antigravity", "아이디어를 앱 화면과 기능 흐름으로 빠르게 실험해 볼 때 참고할 수 있는 AI 개발 도구입니다.", ("앱 제작", "프로토타입", "실험"), "https://antigravity.google/"),
                ("Replit", "브라우저에서 코드 작성, 실행, 배포까지 이어서 실습용 앱을 빠르게 만들 수 있는 플랫폼입니다.", ("웹 IDE", "실습", "배포"), "https://replit.com/desktop"),
                ("Lovable", "자연어 설명으로 웹 앱 초안과 UI 흐름을 빠르게 만들어 보는 제품 제작 도구입니다.", ("웹앱", "UI", "프로토타입"), "https://lovable.dev/"),
                ("Bolt", "프론트엔드와 간단한 풀스택 프로토타입을 브라우저에서 빠르게 생성하는 도구입니다.", ("프론트엔드", "풀스택", "프로토타입"), "https://bolt.new/"),
            ),
        ),
        (
            "디자인·UI",
            "화면 초안, 컴포넌트, 인터랙션을 만들고 개발 코드로 이어가기 좋은 도구입니다.",
            (
                ("v0", "UI 컴포넌트와 화면 초안을 빠르게 만들고 코드로 이어가기 좋은 디자인·개발 보조 도구입니다.", ("UI", "컴포넌트", "디자인"), "https://v0.app/"),
                ("Figma Make", "디자인 아이디어를 인터랙션이 있는 화면 초안으로 발전시킬 때 활용할 수 있는 도구입니다.", ("디자인", "화면", "인터랙션"), "https://www.figma.com/make/"),
            ),
        ),
        (
            "터미널·명령 자동화",
            "명령 실행, 코드 탐색, 문서 요약처럼 터미널 중심 업무를 돕는 도구입니다.",
            (
                ("Gemini CLI", "터미널에서 Gemini를 호출해 코드 탐색, 명령 보조, 문서 요약에 활용할 수 있는 도구입니다.", ("터미널", "검색", "요약"), "https://github.com/google-gemini/gemini-cli"),
                ("Warp", "터미널 작업에 AI 명령 보조와 워크플로 자동화를 붙여 반복 작업을 줄이는 도구입니다.", ("터미널", "명령", "자동화"), "https://www.warp.dev/"),
            ),
        ),
        (
            "지식·문서·검색",
            "사내 문서, 지식 검색, 회의 정리처럼 정보 흐름을 다루는 업무에 맞는 도구입니다.",
            (
                ("Notion AI", "문서 정리, 회의 요약, 지식 검색을 한 작업 공간 안에서 처리하는 문서형 AI 도구입니다.", ("문서", "요약", "지식관리"), "https://www.notion.com/product/ai"),
                ("Perplexity", "출처 기반 검색과 요약으로 빠르게 리서치하고 근거 링크를 확인하는 AI 검색 도구입니다.", ("검색", "리서치", "출처"), "https://www.perplexity.ai/"),
                ("Glean", "회사 내부 문서와 업무 시스템을 검색해 필요한 지식을 찾아주는 엔터프라이즈 검색 도구입니다.", ("사내검색", "지식", "업무"), "https://www.glean.com/"),
            ),
        ),
        (
            "운영·협업",
            "배포, 이슈, 팀 협업, 업무 자동화처럼 실제 운영 흐름에 붙이기 좋은 도구입니다.",
            (
                ("Linear", "이슈, 로드맵, 제품 개발 흐름을 정리하고 AI로 업무 맥락을 보조하는 협업 도구입니다.", ("이슈", "로드맵", "협업"), "https://linear.app/"),
                ("Zapier", "여러 업무 도구를 연결해 반복 작업과 알림 흐름을 자동화하는 노코드 자동화 도구입니다.", ("자동화", "연동", "업무흐름"), "https://zapier.com/"),
                ("n8n", "업무 자동화 워크플로를 직접 구성하고 AI 노드를 연결해 운영 흐름을 만드는 도구입니다.", ("워크플로", "자동화", "AI 노드"), "https://n8n.io/"),
            ),
        ),
    )

    sections = []
    for group_name, group_summary, tools in groups:
        cards = []
        for name, summary, chips, url in tools:
            chip_html = "".join(f'<span class="tool-chip">{escape(chip)}</span>' for chip in chips)
            cards.append(
                '<article class="ai-tool-card">'
                "<div>"
                f"<h3>{escape(name)}</h3>"
                f"<p>{escape(summary)}</p>"
                "</div>"
                "<div>"
                f'<div class="tool-meta-row">{chip_html}</div>'
                f'<a class="tool-action" href="{escape(url, quote=True)}" '
                'target="_blank" rel="noopener noreferrer">공식 다운로드/시작</a>'
                "</div>"
                "</article>"
            )
        sections.append(
            '<section class="tool-category">'
            f'<header class="tool-category-header"><h2>{escape(group_name)}</h2>'
            f'<p>{escape(group_summary)}</p></header>'
            f'<div class="tool-list-grid">{"".join(cards)}</div>'
            "</section>"
        )
    return "".join(sections)

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
    tools = _latest_first(tool_items)

    (output_dir / "work-skills").mkdir(parents=True, exist_ok=True)
    (output_dir / "tools").mkdir(parents=True, exist_ok=True)
    (output_dir / "ai-tools").mkdir(parents=True, exist_ok=True)
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
    (output_dir / "ai-tools" / "index.html").write_text(
        _render_ai_tools_page(analytics_html=analytics_html, back_href="../"),
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


def _render_ai_tools_page(analytics_html: str, back_href: str) -> str:
    return _render_plain_page(
        title="AI 활용 도구",
        analytics_html=analytics_html,
        body=f"""
        <a class="back-link" href="{escape(back_href)}">← 첫 화면</a>
        <header class="simple-header tool-page-header">
          <div class="kicker">AI 도구</div>
          <h1>AI 활용 도구</h1>
          <p>코딩, 앱 제작, 문서 정리, 디자인, 자동화처럼 실제 결과물을 만드는 데 활용할 수 있는 도구 목록입니다. 비슷한 업무 영역끼리 묶어 빠르게 비교할 수 있게 정리했습니다.</p>
        </header>
        {_render_ai_tool_directory()}
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
          <p><a class="source-link" href="{escape(item.url)}" target="_blank" rel="noopener noreferrer">원문 보기</a></p>
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
      background: #ffffff;
      color: #111111;
      font-family: Arial, "Noto Sans KR", sans-serif;
    }}
    a {{ color: inherit; text-underline-offset: 3px; }}
    .page {{
      width: min(1180px, calc(100% - 34px));
      margin: 0 auto;
      padding: 24px 0 48px;
    }}
    .back-link {{
      display: inline-block;
      margin-bottom: 18px;
      font: 700 14px/1.4 Arial, "Noto Sans KR", sans-serif;
    }}
    .simple-header, .detail {{
      border-top: 1px solid #e8e8e4;
      padding-top: 18px;
    }}
    h1 {{
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(34px, 6vw, 64px);
      line-height: 1.02;
      margin: 0 0 12px;
      letter-spacing: 0;
    }}
    h2 {{
      border-bottom: 1px solid #e8e8e4;
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
    .tool-page-header {{
      margin-bottom: 28px;
    }}
    .tool-category {{
      margin-top: 32px;
    }}
    .tool-category-header {{
      display: grid;
      grid-template-columns: minmax(180px, 280px) minmax(0, 1fr);
      gap: 24px;
      align-items: end;
      border-top: 1px solid #111111;
      padding-top: 16px;
      margin-bottom: 12px;
    }}
    .tool-category-header h2 {{
      border: 0;
      margin: 0;
      padding: 0;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(22px, 2.4vw, 32px);
      white-space: nowrap;
      word-break: keep-all;
    }}
    .tool-category-header p {{
      margin: 0;
      color: #5d6470;
      font: 14px/1.65 Arial, "Noto Sans KR", sans-serif;
    }}
    .tool-list-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      border-top: 1px solid #e8e8e4;
      border-left: 1px solid #e8e8e4;
      margin-top: 0;
    }}
    .ai-tool-card {{
      min-height: 178px;
      padding: 18px;
      border-right: 1px solid #e8e8e4;
      border-bottom: 1px solid #e8e8e4;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 18px;
    }}
    .ai-tool-card h3 {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Noto Serif KR", serif;
      font-size: clamp(20px, 2vw, 28px);
      line-height: 1.02;
      letter-spacing: 0;
    }}
    .ai-tool-card p {{
      margin: 8px 0 0;
      color: #5d6470;
      font: 13px/1.58 Arial, "Noto Sans KR", sans-serif;
    }}
    .tool-meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .tool-chip {{
      border: 1px solid #d7dde6;
      background: #f7f9fb;
      padding: 4px 7px;
      color: #111111;
      font: 800 11px/1.25 Arial, "Noto Sans KR", sans-serif;
    }}
    .tool-action {{
      display: inline-block;
      margin-top: 12px;
      border: 1px solid #222222;
      padding: 7px 9px;
      color: #111111;
      font: 800 12px/1.3 Arial, "Noto Sans KR", sans-serif;
      text-decoration: none;
    }}
    .tool-action:hover,
    .tool-action:focus-visible {{
      background: #111111;
      color: #ffffff;
      outline: 0;
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
      border: 1px solid #d7dde6;
      background: #ffffff;
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
    @media (max-width: 860px) {{
      .tool-category-header {{
        grid-template-columns: 1fr;
        gap: 8px;
      }}
      .tool-list-grid {{
        grid-template-columns: 1fr;
      }}
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
            "detail must be 2 to 4 Korean paragraphs that a Korean high-school student can understand. "
            "Use short sentences, explain why the item matters, and include practical examples rather "
            "than abstract vendor language. "
            "key_points must be exactly 3 concise Korean strings. Each string should start with "
            "'1. 왜 필요한가요?', '2. 핵심 구성 요소:', and '3. 기존 방식과의 차이점:' or an item-specific equivalent. "
            "Do not tell readers to check source links in summary, detail, or key_points. tags must be an array of "
            "3 to 5 short Korean or product-name strings. comparisons must be an array of 0 to 3 Korean "
            "strings comparing the item with adjacent tools or approaches when useful. For Endava items, "
            "compare it with Harness Engineering if relevant: Endava is a consulting/transformation "
            "approach, while Harness is a DevOps/software delivery automation platform. glossary must be "
            "an array of 0 to 5 Korean strings formatted like 'Warp: ...' explaining difficult product "
            "names, acronyms, or jargon as footnote-style notes for readers who may be seeing the "
            "terms for the first time. Emphasize practical work skills, "
            "automation patterns, operational usage, and concrete tool adoption. Do not invent unsupported "
            "facts."
        )
        input_text = (
            f"Translate and rewrite these {context} items for a Korean newsletter site. "
            "Use natural Korean titles that preserve product and company names in English. "
            "Summaries must be one concise Korean sentence and must make clear what a DBA, "
            "network engineer, server operator, or technical mentor can do with it at work. "
            "Key points should explain in plain Korean: what changed, where it can be used in work, and what "
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
                fallback="이번 업데이트가 어떤 업무 문제를 줄이고 어떤 자동화 흐름에 붙을 수 있는지 간단히 정리했습니다.",
            ),
            detail=_safe_korean_field(
                localized_item.get("detail"),
                fallback="이번 업데이트는 업무 자동화, 운영 안정성, 검수 흐름 중 어디에 적용할 수 있는지 빠르게 판단하기 위한 항목입니다.",
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
        "key_points must be exactly 3 concise Korean strings. Each string should start with "
        "'1. 왜 필요한가요?', '2. 핵심 구성 요소:', and '3. 기존 방식과의 차이점:' or an item-specific equivalent. "
        "Do not tell readers to check source links in summary, detail, or key_points. tags must be an array of "
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
    return _fallback_three_line_summary(original)


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
    points = _fallback_three_line_summary(item)
    return SiteItem(
        title=title,
        summary=summary,
        detail=summary,
        source=_korean_source_name(item.source),
        kind=_korean_kind_name(item.kind),
        url=item.url,
        published=item.published,
        key_points=points,
        tags=tuple(_fallback_tags(item)[:5]),
        comparisons=tuple(_fallback_comparisons(item)),
        glossary=tuple(_fallback_glossary(item)),
    )


def _fallback_three_line_summary(item: DigestItem) -> tuple[str, str, str]:
    text = _item_text(item)
    if any(keyword in text for keyword in ("temporal", "durable execution")):
        return (
            "1. 왜 필요한가요? 오래 걸리는 AI 작업이 중간에 실패해도 재시도와 복구를 안정적으로 처리하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 워크플로 상태 저장, 재시도 정책, 작업 큐, 실행 이력 추적입니다.",
            "3. 일반 자동화와의 차이점: 한 번 실행하고 끝나는 스크립트가 아니라 실패와 지연을 전제로 계속 이어지는 운영 흐름입니다.",
        )
    if any(keyword in text for keyword in ("copilot", "coding agent")):
        return (
            "1. 왜 필요한가요? 반복되는 코드 수정, PR 보조, 저장소 작업을 개발자가 매번 직접 처리하지 않도록 줄여줍니다.",
            "2. 핵심 구성 요소: 코드 맥락 이해, 변경안 생성, 테스트·PR 흐름 연결, 리뷰 보조입니다.",
            "3. 기존 코드 자동완성과의 차이점: 한 줄 추천을 넘어 이슈 해결 흐름 전체를 대신 진행하는 방향입니다.",
        )
    if any(keyword in text for keyword in ("claude code", "terminal workflow")):
        return (
            "1. 왜 필요한가요? 터미널에서 코드 탐색, 수정, 리팩터링을 끊기지 않고 이어가기 위해 필요합니다.",
            "2. 핵심 구성 요소: 코드베이스 읽기, 명령 실행 보조, 파일 수정, 변경 내용 설명입니다.",
            "3. 채팅형 AI와의 차이점: 답변만 받는 것이 아니라 작업 폴더 안에서 실제 개발 흐름을 함께 수행합니다.",
        )
    if any(keyword in text for keyword in ("codex", "agent workflows")):
        return (
            "1. 왜 필요한가요? 코드 변경, 테스트, 리뷰 준비를 한 번의 업무 흐름으로 묶기 위해 필요합니다.",
            "2. 핵심 구성 요소: 저장소 이해, 파일 편집, 테스트 실행, 변경 요약과 PR 준비입니다.",
            "3. 단순 코드 생성과의 차이점: 코드를 쓰는 데서 끝나지 않고 검증과 전달 단계까지 포함합니다.",
        )
    if any(keyword in text for keyword in ("langgraph", "workflow layer")):
        return (
            "1. 왜 필요한가요? 여러 단계로 움직이는 AI 에이전트의 상태와 분기 흐름을 안정적으로 관리하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 그래프 기반 단계 정의, 상태 저장, 도구 호출, 재개 가능한 실행입니다.",
            "3. 단순 프롬프트 체인과의 차이점: 순서대로 호출하는 수준을 넘어 조건 분기와 상태 관리가 중심입니다.",
        )
    if any(keyword in text for keyword in ("n8n", "workflow automation")):
        return (
            "1. 왜 필요한가요? 여러 업무 도구와 AI 호출을 연결해 반복 작업을 자동으로 처리하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 트리거, 노드, 조건 분기, 외부 서비스 연동, AI 처리 단계입니다.",
            "3. 수동 업무와의 차이점: 사람이 복사하고 확인하던 절차를 규칙화해 반복 실행할 수 있습니다.",
        )
    if any(keyword in text for keyword in ("vercel", "deployment")):
        return (
            "1. 왜 필요한가요? AI 앱을 빠르게 공개하고 프론트엔드와 서버 기능을 함께 운영하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 배포 파이프라인, 서버리스 실행, 환경 변수, 프리뷰 배포입니다.",
            "3. 로컬 실행과의 차이점: 내 컴퓨터가 아니라 사용자가 접속할 수 있는 운영 환경에서 검증합니다.",
        )
    if any(keyword in text for keyword in ("datadog", "observability")):
        return (
            "1. 왜 필요한가요? AI 기능의 비용, 지연, 오류, 품질 문제를 운영 중에 빠르게 찾기 위해 필요합니다.",
            "2. 핵심 구성 요소: 로그, 메트릭, 트레이스, 알림, 대시보드입니다.",
            "3. 일반 모니터링과의 차이점: 모델 호출과 응답 품질 같은 AI 특화 신호까지 함께 봅니다.",
        )
    if any(keyword in text for keyword in ("prompt", "workflow migration")):
        return (
            "1. 왜 필요한가요? 한 번 쓰고 버리는 프롬프트를 반복 가능한 업무 절차로 바꾸기 위해 필요합니다.",
            "2. 핵심 구성 요소: 입력 양식, 승인 단계, 실행 기록, 결과 검수 기준입니다.",
            "3. 프롬프트 엔지니어링과의 차이점: 좋은 문장을 만드는 것보다 업무가 끝까지 굴러가게 만드는 데 초점이 있습니다.",
        )
    if any(keyword in text for keyword in ("database", "supabase", "guardrail")):
        return (
            "1. 왜 필요한가요? AI가 데이터베이스를 다룰 때 실수로 위험한 조회나 변경을 하지 않게 하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 읽기 전용 권한, 스키마 범위 제한, 쿼리 검토, 감사 로그입니다.",
            "3. 일반 DB 도구와의 차이점: 사람이 직접 쿼리하는 상황보다 AI의 자동 실행 위험을 더 강하게 통제합니다.",
        )
    if any(keyword in text for keyword in ("qdrant", "knowledge search", "vector")):
        return (
            "1. 왜 필요한가요? 내부 문서와 지식을 AI가 근거와 함께 찾아 쓰게 만들기 위해 필요합니다.",
            "2. 핵심 구성 요소: 벡터 저장소, 문서 임베딩, 검색 랭킹, 출처 표시입니다.",
            "3. 일반 검색과의 차이점: 키워드 일치보다 의미가 가까운 정보를 찾아 답변 맥락으로 씁니다.",
        )
    if any(keyword in text for keyword in ("release note", "github")):
        return (
            "1. 왜 필요한가요? 이슈, 커밋, PR에 흩어진 변경 내용을 릴리즈 설명으로 빠르게 정리하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 변경 내역 수집, 영향 범위 요약, 검수 문구, 게시 전 승인입니다.",
            "3. 수동 작성과의 차이점: 개발 기록을 자동으로 묶어 초안을 만들고 사람은 정확도만 다듬습니다.",
        )
    if any(keyword in text for keyword in ("spreadsheet", "microsoft")):
        return (
            "1. 왜 필요한가요? 반복되는 표 계산, 요약, 보고서 준비 시간을 줄이기 위해 필요합니다.",
            "2. 핵심 구성 요소: 데이터 정리, 수식 제안, 요약 생성, 보고서 초안 작성입니다.",
            "3. 기존 엑셀 작업과의 차이점: 사용자가 모든 수식과 설명을 직접 만들지 않아도 됩니다.",
        )
    if any(keyword in text for keyword in ("vault", "secret")):
        return (
            "1. 왜 필요한가요? AI 에이전트가 필요한 비밀값만 안전하게 쓰고 남용하지 못하게 하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 토큰 범위 제한, 비밀 저장소, 접근 정책, 사용 기록입니다.",
            "3. 일반 환경 변수와의 차이점: 저장만 하는 것이 아니라 누가 언제 무엇을 썼는지 통제합니다.",
        )
    if any(keyword in text for keyword in ("playwright", "design qa", "visual")):
        return (
            "1. 왜 필요한가요? AI가 만든 화면이 모바일·데스크톱에서 깨지지 않는지 빠르게 확인하기 위해 필요합니다.",
            "2. 핵심 구성 요소: 화면 캡처, 반응형 테스트, 클릭 흐름 검증, 시각 회귀 비교입니다.",
            "3. 눈으로 확인하는 방식과의 차이점: 반복 검사를 자동화해 수정 때마다 같은 기준으로 확인합니다.",
        )
    return (
        "1. 왜 필요한가요? 이번 업데이트가 실제 업무 흐름의 어떤 문제를 줄일 수 있는지 빠르게 판단하기 위해 필요합니다.",
        "2. 핵심 구성 요소: 적용 대상, 필요한 도구, 운영 조건, 검수 기준을 함께 확인하는 것입니다.",
        "3. 기존 방식과의 차이점: 단순 소식 전달이 아니라 업무에 붙일 수 있는 실행 단위로 정리합니다.",
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
    return "새 기능이나 변화가 어떤 업무 흐름에 붙을 수 있는지 빠르게 살펴보세요."


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
