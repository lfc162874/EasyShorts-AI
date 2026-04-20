from __future__ import annotations

from app.agents.agentscope_runtime import run_structured_agent_sync
from app.agents.common import build_application_scenarios, build_background, build_impact, build_technical_analysis, extract_keywords
from app.agents.context import AgentExecutionContext
from app.agents.structured_models import EnrichmentStructuredOutput


def _build_enrichment_user_prompt(
    context: AgentExecutionContext,
    classification_result: dict[str, object],
    summary_result: dict[str, object],
) -> str:
    news = context.news
    return "\n".join(
        [
            "请从背景、影响、技术解读和应用场景四个角度扩展下面这条 AI 新闻，只输出结构化结果，不要额外解释。",
            f"标题：{summary_result.get('title') or news.title}",
            f"来源：{news.source}",
            f"分类：{classification_result.get('category') or news.category or '未分类'}",
            f"标签：{', '.join(classification_result.get('tags') or []) or '无'}",
            f"热度分值：{summary_result.get('hot_score') or news.hot_score}",
            f"摘要：{summary_result.get('summary') or news.summary or '无'}",
            "正文：",
            news.content or "",
        ]
    )


def run_enrichment_agent(
    context: AgentExecutionContext,
    classification_result: dict[str, object],
    summary_result: dict[str, object],
) -> dict[str, object]:
    runtime = context.runtime
    if runtime is not None:
        agent_result = run_structured_agent_sync(
            runtime=runtime,
            agent_name="EnrichmentAgent",
            system_prompt=context.prompt_bundle.get("agent_enrichment_prompt", ""),
            user_prompt=_build_enrichment_user_prompt(context, classification_result, summary_result),
            structured_model=EnrichmentStructuredOutput,
        )
        if agent_result is not None:
            return {
                **agent_result,
                "model_name": context.model_name,
                "prompt_version": context.prompt_version,
            }

    news = context.news
    category = str(classification_result.get("category") or news.category or "行业动态")
    keywords = list(classification_result.get("keywords") or extract_keywords(f"{news.title} {news.content or ''}"))
    background = build_background(category, str(summary_result.get("title") or news.title), keywords)
    impact = build_impact(category, int(summary_result.get("hot_score") or news.hot_score or 0), keywords)
    technical_analysis = build_technical_analysis(category, keywords)
    scenarios = build_application_scenarios(category, keywords)

    return {
        "background": background,
        "impact": impact,
        "technical_analysis": technical_analysis,
        "application_scenarios": scenarios,
        "model_name": context.model_name,
        "prompt_version": context.prompt_version,
    }
