from __future__ import annotations

from app.agents.agentscope_runtime import run_structured_agent_sync
from app.agents.common import extract_keywords, infer_category
from app.agents.context import AgentExecutionContext
from app.agents.structured_models import ClassificationStructuredOutput


def _build_classification_user_prompt(context: AgentExecutionContext, hotspot_result: dict[str, object]) -> str:
    news = context.news
    return "\n".join(
        [
            "请为下面这条 AI 新闻输出分类、标签和关键词，只输出结构化结果，不要额外解释。",
            f"标题：{news.title}",
            f"来源：{news.source}",
            f"分类：{news.category or '未分类'}",
            f"热度分值：{hotspot_result.get('score', news.hot_score)}",
            f"热点判断：{hotspot_result.get('is_hot')}",
            f"摘要：{news.summary or '无'}",
            "正文：",
            news.content or "",
        ]
    )


def run_classification_agent(context: AgentExecutionContext, hotspot_result: dict[str, object]) -> dict[str, object]:
    runtime = context.runtime
    if runtime is not None:
        agent_result = run_structured_agent_sync(
            runtime=runtime,
            agent_name="ClassificationAgent",
            system_prompt=context.prompt_bundle.get("agent_classification_prompt", ""),
            user_prompt=_build_classification_user_prompt(context, hotspot_result),
            structured_model=ClassificationStructuredOutput,
        )
        if agent_result is not None:
            return {
                **agent_result,
                "model_name": context.model_name,
                "prompt_version": context.prompt_version,
            }

    news = context.news
    text = f"{news.title} {news.content or ''}"
    category = infer_category(news.title, news.content or "", news.category)
    keyword_candidates = extract_keywords(text)
    tags: list[str] = []
    for candidate in [category, news.source, *(news.tags or []), *keyword_candidates]:
        if candidate and candidate not in tags:
            tags.append(candidate)
        if len(tags) >= 5:
            break
    return {
        "category": category,
        "tags": tags[:5],
        "keywords": keyword_candidates[:6],
        "topic_hint": category,
        "model_name": context.model_name,
        "prompt_version": context.prompt_version,
        "hot_score": hotspot_result.get("score", news.hot_score),
    }
