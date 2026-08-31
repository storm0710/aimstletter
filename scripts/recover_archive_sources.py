from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import subprocess

from aimstletter.site import (
    _dedupe_items,
    _digest_from_existing_card_attrs,
    _html_attrs,
    _weekly_archive_entry,
    _write_week_source_items,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recover retryable source items from a Git archive page.")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--archive-path", required=True)
    parser.add_argument("--output-dir", default="public")
    parser.add_argument("--build-date", required=True)
    args = parser.parse_args()

    html_text = subprocess.run(
        ["git", "show", f"{args.revision}:{args.archive_path}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    ai_items = []
    tool_items = []
    for match in re.finditer(r'<button class="insight-card"[\s\S]*?</button>', html_text):
        attrs = _html_attrs(match.group(0))
        item = _digest_from_existing_card_attrs(attrs)
        if not item.title or not item.url:
            continue
        if "arxiv.org" in item.url:
            item = replace(item, kind="paper")
        elif any(domain in item.url for domain in ("openai.com/", "about.fb.com/")):
            item = replace(item, kind="news")
        if item.kind == "tool":
            tool_items.append(item)
        else:
            ai_items.append(item)

    kst = timezone(timedelta(hours=9), name="KST")
    build_at = datetime.fromisoformat(args.build_date).replace(hour=8, tzinfo=kst)
    archive_entry = _weekly_archive_entry(build_at)
    _write_week_source_items(
        Path(args.output_dir),
        archive_entry,
        _dedupe_items(ai_items),
        _dedupe_items(tool_items),
        build_at,
    )
    print(f"Recovered {len(ai_items)} AI and {len(tool_items)} tool source items for {args.build_date}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
