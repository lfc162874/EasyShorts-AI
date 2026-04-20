from __future__ import annotations

from app.agents.agentscope_runtime import run_structured_agent_sync
from app.agents.common import build_highlights, contains_chinese, extract_keywords, normalize_whitespace, summarize_text
from app.agents.context import AgentExecutionContext
from app.agents.structured_models import SummaryStructuredOutput


def _build_optimized_title(news_title: str, translated_title: str | None, keywords: list[str]) -> str:
    if translated_title and translated_title.strip():
        return normalize_whitespace(translated_title)
    if contains_chinese(news_title):
        return normalize_whitespace(news_title)
    if keywords:
        return f"{keywords[0]} | {news_title}"
    return normalize_whitespace(news_title)


def _build_summary_user_prompt(
    context: AgentExecutionContext,
    hotspot_result: dict[str, object],
    classification_result: dict[str, object],
) -> str:
    news = context.news
    return "\n".join(
        [
            "请根据下面这条 AI 新闻生成优化标题、中文摘要和要点，只输出结构化结果，不要额外解释。",
            f"标题：{news.title}",
            f"来源：{news.source}",
            f"分类：{classification_result.get('category') or news.category or '未分类'}",
            f"热度分值：{hotspot_result.get('score', news.hot_score)}",
            f"标签：{', '.join(classification_result.get('tags') or []) or '无'}",
            f"原始摘要：{news.summary or '无'}",
            "正文：",
            news.content or "",
        ]
    )


def run_summary_agent(
    context: AgentExecutionContext,
    hotspot_result: dict[str, object],
    classification_result: dict[str, object],
) -> dict[str, object]:
    runtime = context.runtime
    if runtime is not None:
        agent_result = run_structured_agent_sync(
            runtime=runtime,
            agent_name="SummaryAgent",
            system_prompt=context.prompt_bundle.get("agent_summary_prompt", ""),
            user_prompt=_build_summary_user_prompt(context, hotspot_result, classification_result),
            structured_model=SummaryStructuredOutput,
        )
        if agent_result is not None:
            return {
                **agent_result,
                "model_name": context.model_name,
                "prompt_version": context.prompt_version,
            }

    news = context.news
    text = news.content or news.summary or news.title
    keywords = list(classification_result.get("keywords") or extract_keywords(f"{news.title} {text}"))
    summary = summarize_text(text)
    highlights = build_highlights(text, keywords)
    optimized_title = _build_optimized_title(news.title, news.translated_title, keywords)
    if not summary:
        summary = normalize_whitespace(news.summary or news.title)
    if len(highlights) < 3:
        highlights.append(f"标题：{optimized_title}")

    return {
        "title": optimized_title,
        "summary": summary,
        "highlights": highlights[:4],
        "model_name": context.model_name,
        "prompt_version": context.prompt_version,
        "source_summary": normalize_whitespace(news.summary or "")[:180],
    }
