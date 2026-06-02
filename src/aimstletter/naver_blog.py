from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
import re
import sys
import xmlrpc.client

from aimstletter.config import Settings

NAVER_BLOG_XMLRPC_ENDPOINT = "https://api.blog.naver.com/xmlrpc"


def post_markdown_to_naver_blog(
    title: str,
    markdown: str,
    settings: Settings,
    publish: bool = True,
) -> str:
    if not settings.naver_blog_id:
        raise ValueError("NAVER_BLOG_ID is required.")
    if not settings.naver_blog_username:
        raise ValueError("NAVER_BLOG_USERNAME is required.")
    if not settings.naver_blog_api_password:
        raise ValueError("NAVER_BLOG_API_PASSWORD is required.")

    html = markdown_to_naver_html(markdown)
    server = xmlrpc.client.ServerProxy(NAVER_BLOG_XMLRPC_ENDPOINT, allow_none=True)
    post = {
        "title": title,
        "description": html,
        "categories": ["AI마스터"],
    }
    return str(
        server.metaWeblog.newPost(
            settings.naver_blog_id,
            settings.naver_blog_username,
            settings.naver_blog_api_password,
            post,
            publish,
        )
    )


def markdown_to_naver_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html_lines: list[str] = []
    list_open = False

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            html_lines.append("</ul>")
            list_open = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            close_list()
            continue

        if line.startswith("# "):
            close_list()
            html_lines.append(f"<h1>{_inline_markdown(line[2:].strip())}</h1>")
        elif line.startswith("## "):
            close_list()
            html_lines.append(f"<h2>{_inline_markdown(line[3:].strip())}</h2>")
        elif line.startswith("- "):
            if not list_open:
                html_lines.append("<ul>")
                list_open = True
            html_lines.append(f"<li>{_inline_markdown(line[2:].strip())}</li>")
        elif re.match(r"^\d+\. ", line):
            close_list()
            html_lines.append(f"<p>{_inline_markdown(line)}</p>")
        else:
            close_list()
            html_lines.append(f"<p>{_inline_markdown(line)}</p>")

    close_list()
    return "\n".join(html_lines)


def _inline_markdown(text: str) -> str:
    escaped = escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"(https?://[^\s<]+)",
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped,
    )
    return escaped


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a generated digest Markdown file to Naver Blog.")
    parser.add_argument("--title", required=True, help="Naver Blog post title.")
    parser.add_argument("--body-file", required=True, help="Markdown file to publish.")
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Create the post as a draft when the API supports draft publishing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the converted Naver Blog HTML without publishing.",
    )
    args = parser.parse_args()

    settings = Settings.from_env()
    markdown = Path(args.body_file).read_text(encoding="utf-8")
    if args.dry_run:
        print(markdown_to_naver_html(markdown))
        return 0

    try:
        post_id = post_markdown_to_naver_blog(args.title, markdown, settings, publish=not args.draft)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to publish Naver Blog post: {exc}", file=sys.stderr)
        return 2

    print(f"Published Naver Blog post: {post_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
