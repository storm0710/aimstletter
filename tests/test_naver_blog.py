from __future__ import annotations

from pathlib import Path

from aimstletter.naver_blog import markdown_to_naver_html


def test_markdown_to_naver_html_converts_digest_structure() -> None:
    markdown = "\n".join(
        [
            "# AI마스터 주간 AI 업데이트",
            "",
            "## 상위 5개: DBA/네트워크/서버 직군 관련 AI 스킬",
            "",
            "- **유형:** 논문 (Original Title)",
            "- **링크:** https://example.com/paper",
        ]
    )

    html = markdown_to_naver_html(markdown)

    assert "<h1>AI마스터 주간 AI 업데이트</h1>" in html
    assert "<h2>상위 5개: DBA/네트워크/서버 직군 관련 AI 스킬</h2>" in html
    assert "<strong>유형:</strong> 논문 (Original Title)" in html
    assert '<a href="https://example.com/paper"' in html


def test_weekly_github_issue_workflow_publishes_to_storm0710_blog_on_monday() -> None:
    workflow = Path(".github/workflows/weekly-github-issue.yml").read_text(encoding="utf-8")

    assert "07:00 every Monday in Asia/Seoul" in workflow
    assert 'cron: "0 22 * * 0"' in workflow
    assert "NAVER_BLOG_ID: ${{ vars.NAVER_BLOG_ID || 'storm0710' }}" in workflow
    assert "NAVER_BLOG_USERNAME: ${{ secrets.NAVER_BLOG_USERNAME || 'storm0710' }}" in workflow
    assert "NAVER_BLOG_API_PASSWORD: ${{ secrets.NAVER_BLOG_API_PASSWORD }}" in workflow
    assert "python -m aimstletter.naver_blog" in workflow
    assert "AI마스터 주간 AI 업데이트" in workflow
