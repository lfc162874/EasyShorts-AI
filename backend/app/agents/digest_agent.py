from __future__ import annotations

from datetime import date

from app.agents.agentscope_runtime import can_use_agentscope, run_structured_agent_sync
from app.agents.common import build_highlights, normalize_whitespace
from app.agents.runtime import AgentRuntime
from app.agents.structured_models import DigestStructuredOutput


def _topic_title(topic: dict[str, object]) -> str:
    return normalize_whitespace(str(topic.get("title") or topic.get("name") or "")) or "未命名热点"


def _topic_summary(topic: dict[str, object]) -> str:
    return normalize_whitespace(
        str(
            topic.get("summary")
            or topic.get("reason")
            or topic.get("output_summary")
            or topic.get("title")
            or ""
        )
    )


def _build_digest_user_prompt(
    topics: list[dict[str, object]],
    *,
    report_type: str,
    report_date: date | None,
) -> str:
    lines = [
        "请根据下面多条 AI 热点内容生成简报，只输出结构化结果，不要额外解释。",
        f"简报类型：{report_type}",
        f"简报日期：{report_date.isoformat() if report_date else '未知'}",
        f"热点数量：{len(topics)}",
        "热点列表：",
    ]
    for index, topic in enumerate(topics[:12], start=1):
        title = _topic_title(topic)
        category = normalize_whitespace(str(topic.get("category") or ""))
        score = topic.get("score")
        summary = _topic_summary(topic)
        lines.append(
            f"{index}. 标题：{title}；分类：{category or '未分类'}；热度：{score if score is not None else '未知'}；摘要：{summary or '无'}"
        )
    return "\n".join(lines)


def run_digest_agent(
    topics: list[dict[str, object]],
    *,
    model_name: str,
    prompt_version: str,
    report_type: str = "DAILY",
    report_date: date | None = None,
    runtime: AgentRuntime | None = None,
    system_prompt: str = "",
) -> dict[str, object]:
    if runtime is not None and can_use_agentscope(runtime):
        agent_result = run_structured_agent_sync(
            runtime=runtime,
            agent_name="DigestAgent",
            system_prompt=system_prompt,
            user_prompt=_build_digest_user_prompt(topics, report_type=report_type, report_date=report_date),
            structured_model=DigestStructuredOutput,
        )
        if agent_result is not None:
            return {
                **agent_result,
                "model_name": model_name,
                "prompt_version": prompt_version,
                "report_type": report_type,
                "report_date": report_date.isoformat() if report_date else None,
            }

    titles = [_topic_title(topic) for topic in topics if _topic_title(topic)]
    summaries = [_topic_summary(topic) for topic in topics if _topic_summary(topic)]
    digest_title = "AI 热点简报"
    if titles:
        digest_title = f"AI 热点简报 · {titles[0]}"
    digest_text = "；".join(summaries[:3]) if summaries else "今日暂无可汇总的热点。"
    highlights = build_highlights(digest_text, titles[:3])
    return {
        "title": digest_title,
        "summary": digest_text,
        "highlights": highlights,
        "topic_count": len(topics),
        "model_name": model_name,
        "prompt_version": prompt_version,
        "report_type": report_type,
        "report_date": report_date.isoformat() if report_date else None,
    }
