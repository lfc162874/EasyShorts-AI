from __future__ import annotations

from app.agents.agentscope_runtime import run_structured_agent_sync
from app.agents.common import HOT_KEYWORDS, extract_keywords, infer_priority, infer_trend, normalize_whitespace
from app.agents.context import AgentExecutionContext
from app.agents.structured_models import HotspotStructuredOutput


def _build_hotspot_user_prompt(context: AgentExecutionContext) -> str:
    news = context.news
    return "\n".join(
        [
            "请判断下面这条 AI 新闻是否值得继续作为热点处理，只输出结构化结果，不要额外解释。",
            f"标题：{news.title}",
            f"来源：{news.source}",
            f"分类：{news.category or '未分类'}",
            f"热度分值：{news.hot_score}",
            f"语言：{news.language}",
            f"发布时间：{news.publish_time.isoformat() if news.publish_time else '未知'}",
            f"摘要：{news.summary or '无'}",
            "正文：",
            news.content or "",
        ]
    )


def run_hotspot_agent(context: AgentExecutionContext) -> dict[str, object]:
    runtime = context.runtime
    if runtime is not None:
        agent_result = run_structured_agent_sync(
            runtime=runtime,
            agent_name="HotspotAgent",
            system_prompt=context.prompt_bundle.get("agent_hotspot_prompt", ""),
            user_prompt=_build_hotspot_user_prompt(context),
            structured_model=HotspotStructuredOutput,
        )
        if agent_result is not None:
            return {
                **agent_result,
                "model_name": context.model_name,
                "prompt_version": context.prompt_version,
            }

    news = context.news
    text = f"{news.title} {news.content or ''}"
    keywords = extract_keywords(text)
    hot_score = int(news.hot_score or 0)
    if any(keyword.lower() in text.lower() for keyword in HOT_KEYWORDS):
        hot_score += 8
    if news.source and any(marker in news.source.lower() for marker in ("openai", "anthropic", "deepseek", "qwen", "modelscope")):
        hot_score += 5

    hot_score = min(hot_score, 100)
    is_hot = hot_score >= context.config["hot_threshold"] or news.status in {"FILTERED", "SCRIPT_READY"}
    reason_parts = [
        f"热度评分 {hot_score}",
        f"来源 {news.source}",
        f"关键词 {', '.join(keywords[:3])}" if keywords else "未命中显著关键词",
    ]
    if news.summary:
        reason_parts.append(f"已有摘要 {normalize_whitespace(news.summary)[:60]}")

    return {
        "is_hot": is_hot,
        "score": hot_score,
        "priority": infer_priority(hot_score),
        "trend": infer_trend(hot_score, title=news.title, content=news.content or ""),
        "reason": "；".join(reason_parts),
        "keywords": keywords[:5],
    }
