from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
import textwrap

from openai import OpenAI

from aimstletter.fetchers import DigestItem


def compose_digest(
    items: list[DigestItem],
    channel_label: str,
    openai_api_key: str | None,
    openai_model: str,
    azure_openai_endpoint: str | None = None,
    azure_openai_api_key: str | None = None,
    azure_openai_deployment: str = "gpt-5-mini",
    output_format: str = "slack",
) -> str:
    if not items:
        return _empty_digest(channel_label, output_format)

    fallback = _compose_rule_based(items, channel_label, output_format)
    if not openai_api_key and not azure_openai_api_key:
        return fallback

    try:
        generated = _compose_with_openai(
            items=items,
            channel_label=channel_label,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            azure_openai_endpoint=azure_openai_endpoint,
            azure_openai_api_key=azure_openai_api_key,
            azure_openai_deployment=azure_openai_deployment,
            output_format=output_format,
        )
        if output_format == "github" and not _looks_like_github_digest(generated):
            return fallback
        return generated
    except Exception as exc:  # noqa: BLE001
        return f"{fallback}\n\n_참고: OpenAI 요약 생성 실패로 기본 요약을 사용했습니다: {exc}_"


def _empty_digest(channel_label: str, output_format: str) -> str:
    if output_format == "github":
        return f"# {channel_label} 주간 AI 업데이트\n\n이번 주 기준으로 공유할 새 항목을 찾지 못했습니다."
    return f"*{channel_label} 주간 AI 업데이트*\n이번 주 기준으로 공유할 새 항목을 찾지 못했습니다."


def _compose_rule_based(items: list[DigestItem], channel_label: str, output_format: str) -> str:
    kst = timezone(timedelta(hours=9), name="KST")
    today = datetime.now(UTC).astimezone(kst).strftime("%Y-%m-%d")
    if output_format == "github":
        return _compose_github_markdown(items, channel_label, today)

    lines = [
        f"*{channel_label} 주간 AI 업데이트*",
        f"_기준일: {today} KST_",
        "",
        "이번 주 멘토링에서 바로 이야기해볼 만한 AI 동향과 논문입니다.",
        "",
    ]
    for index, item in enumerate(items, start=1):
        summary = item.summary[:240].rstrip()
        if len(item.summary) > 240:
            summary += "..."
        hook = "논문" if item.kind == "paper" else "동향"
        lines.extend(
            [
                f"*{index}. {item.title}*",
                f"- 유형: {hook} | 출처: {item.source}",
                f"- 핵심: {summary or '요약 정보 없음'}",
                "- 멘토링 질문: 이 흐름을 어떤 고객 문제나 수익 모델로 바꿀 수 있을까요?",
                f"- 링크: {item.url}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def _compose_github_markdown(items: list[DigestItem], channel_label: str, today: str) -> str:
    lines = [
        f"# {channel_label} 주간 AI 업데이트",
        "",
        f"- 기준일: {today} KST",
        "- 목적: AI마스터 과정에서 AI로 비즈니스 모델을 개발할 때 참고할 만한 최신 동향과 논문 공유",
        "- 활용법: 각 항목을 고객 문제, 반복 업무 자동화, 수익 모델 관점에서 토론해보면 좋습니다.",
        "",
    ]
    for index, item in enumerate(items, start=1):
        summary = item.summary[:360].rstrip()
        if len(item.summary) > 360:
            summary += "..."
        hook = "논문" if item.kind == "paper" else "동향"
        lines.extend(
            [
                f"## {index}. {item.title}",
                "",
                f"- **유형:** {hook}",
                f"- **출처:** {item.source}",
                f"- **핵심:** {summary or '요약 정보 없음'}",
                "- **비즈니스 관점:** 이 흐름을 실제 고객 문제, 반복 업무, 운영 효율, 또는 신규 수익 모델과 연결해 볼 수 있습니다.",
                "- **멘토링 질문:** 이 흐름을 어떤 고객 문제나 수익 모델로 바꿀 수 있을까요?",
                f"- **링크:** {item.url}",
                "",
            ]
        )
    lines.extend(
        [
            "## 이번 주 토론 제안",
            "",
            "1. 이 흐름 중 가장 빠르게 유료화할 수 있는 고객 문제는 무엇인가?",
            "2. AI가 단순 답변이 아니라 업무 절차를 수행할 때 필요한 신뢰 장치는 무엇인가?",
            "3. 작은 기업이나 초기 팀이 매달 비용을 낼 만한 AI 업무 대행 패키지는 무엇인가?",
        ]
    )
    return "\n".join(lines).strip()


def _compose_with_openai(
    items: list[DigestItem],
    channel_label: str,
    openai_api_key: str | None,
    openai_model: str,
    azure_openai_endpoint: str | None,
    azure_openai_api_key: str | None,
    azure_openai_deployment: str,
    output_format: str,
) -> str:
    client, model = _make_client(
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        azure_openai_endpoint=azure_openai_endpoint,
        azure_openai_api_key=azure_openai_api_key,
        azure_openai_deployment=azure_openai_deployment,
    )
    source_block = "\n\n".join(
        textwrap.dedent(
            f"""
            [{index}]
            title: {item.title}
            source: {item.source}
            type: {item.kind}
            url: {item.url}
            summary: {item.summary}
            """
        ).strip()
        for index, item in enumerate(items, start=1)
    )
    response = client.responses.create(
        model=model,
        instructions=_format_instructions(output_format),
        input=_format_prompt(channel_label, output_format, source_block),
    )
    return response.output_text.strip()


def _format_instructions(output_format: str) -> str:
    base = (
        "You write concise Korean digests for assistant mentors in an AI business model "
        "development course. Keep it practical, specific, and discussion-oriented. "
        "Do not invent facts. Preserve every source URL."
    )
    if output_format == "github":
        return (
            f"{base} Return clean GitHub-flavored Markdown only. Use a polished newsletter "
            "structure with clear headings, short paragraphs, and scannable bullets."
        )
    return f"{base} Return Slack mrkdwn only."


def _looks_like_github_digest(text: str) -> bool:
    required_markers = (
        "# AI마스터 주간 AI 업데이트",
        "## 1.",
        "- **유형:**",
        "- **비즈니스 관점:**",
        "## 이번 주 토론 제안",
    )
    return all(marker in text for marker in required_markers)


def _format_prompt(channel_label: str, output_format: str, source_block: str) -> str:
    if output_format == "github":
        return (
            f"Create a Korean GitHub Issue body for the {channel_label} weekly AI update.\n\n"
            "Use exactly this structure:\n"
            f"# {channel_label} 주간 AI 업데이트\n\n"
            "- 기준일: use today's KST date\n"
            "- 목적: AI마스터 과정에서 AI로 비즈니스 모델을 개발할 때 참고할 만한 최신 동향과 논문 공유\n"
            "- 활용법: 각 항목을 고객 문제, 반복 업무 자동화, 수익 모델 관점에서 토론하도록 안내\n\n"
            "For each source item, create a section like:\n"
            "## 1. Korean title or translated title\n\n"
            "- **유형:** 논문 or 동향\n"
            "- **출처:** source name\n"
            "- **핵심:** 2 concise Korean sentences\n"
            "- **비즈니스 관점:** 1 practical Korean sentence about product, customer, market, workflow, or revenue\n"
            "- **멘토링 질문:** 1 discussion question in Korean\n"
            "- **링크:** source URL\n\n"
            "End with:\n"
            "## 이번 주 토론 제안\n\n"
            "Include 3 to 4 numbered discussion questions.\n\n"
            "Formatting rules:\n"
            "- Use Markdown headings, not plain numbered paragraphs.\n"
            "- Use bold Korean labels exactly as shown above.\n"
            "- Keep every item compact, but readable.\n"
            "- Do not include a preamble outside the Markdown issue body.\n\n"
            f"Source items:\n\n{source_block}"
        )

    return (
        f"Create a Korean Slack message for the {channel_label} channel using these items. "
        "For each item include: title, why it matters for AI business model development, "
        "one mentoring discussion question, and the source URL. Keep under 900 Korean words.\n\n"
        f"{source_block}"
    )


def _make_client(
    openai_api_key: str | None,
    openai_model: str,
    azure_openai_endpoint: str | None,
    azure_openai_api_key: str | None,
    azure_openai_deployment: str,
) -> tuple[OpenAI, str]:
    if azure_openai_api_key:
        if not azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required when AZURE_OPENAI_API_KEY is set.")
        endpoint = azure_openai_endpoint.rstrip("/")
        return OpenAI(
            api_key=azure_openai_api_key,
            base_url=f"{endpoint}/openai/v1/",
        ), azure_openai_deployment

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when Azure OpenAI is not configured.")

    return OpenAI(api_key=openai_api_key), openai_model
