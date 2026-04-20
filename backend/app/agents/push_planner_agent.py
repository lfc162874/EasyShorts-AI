from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.agents.agentscope_runtime import run_structured_agent_sync
from app.agents.common import infer_priority, merge_channels, recommend_channels
from app.agents.context import AgentExecutionContext
from app.agents.structured_models import PushPlanStructuredOutput


def _build_push_plan_user_prompt(
    context: AgentExecutionContext,
    hotspot_result: dict[str, object],
    classification_result: dict[str, object],
    summary_result: dict[str, object],
) -> str:
    news = context.news
    return "\n".join(
        [
            "请根据下面这条 AI 新闻和分析结果给出推送计划，只输出结构化结果，不要额外解释。",
            f"标题：{summary_result.get('title') or news.title}",
            f"来源：{news.source}",
            f"分类：{classification_result.get('category') or news.category or '未分类'}",
            f"热度分值：{hotspot_result.get('score') or news.hot_score}",
            f"热点判断：{hotspot_result.get('is_hot')}",
            f"摘要：{summary_result.get('summary') or news.summary or '无'}",
            f"建议渠道：{', '.join(context.config.get('push_channels') or []) or '无'}",
        ]
    )


def run_push_planner_agent(
    context: AgentExecutionContext,
    hotspot_result: dict[str, object],
    classification_result: dict[str, object],
    summary_result: dict[str, object],
) -> dict[str, object]:
    runtime = context.runtime
    if runtime is not None:
        agent_result = run_structured_agent_sync(
            runtime=runtime,
            agent_name="PushPlannerAgent",
            system_prompt=context.prompt_bundle.get("agent_push_planner_prompt", ""),
            user_prompt=_build_push_plan_user_prompt(context, hotspot_result, classification_result, summary_result),
            structured_model=PushPlanStructuredOutput,
        )
        if agent_result is not None:
            priority = str(agent_result.get("priority") or infer_priority(int(hotspot_result.get("score") or context.news.hot_score or 0)))
            agent_result["channels"] = merge_channels(agent_result.get("channels") or [], recommend_channels(priority))
            return {
                **agent_result,
                "model_name": context.model_name,
                "prompt_version": context.prompt_version,
            }

    score = int(hotspot_result.get("score") or context.news.hot_score or 0)
    category = str(classification_result.get("category") or context.news.category or "行业动态")
    is_hot = bool(hotspot_result.get("is_hot"))
    push_now = is_hot and score >= max(int(context.config["hot_threshold"]), 35) + 10
    if category in {"AI Agent", "大模型", "开源生态"} and score >= max(int(context.config["hot_threshold"]), 35):
        push_now = True

    priority = infer_priority(score)
    push_type = "IMMEDIATE" if push_now else "DIGEST"
    channels = merge_channels(context.config.get("push_channels") or [], recommend_channels(priority))
    planned_at = datetime.now(UTC) if push_now else datetime.now(UTC) + timedelta(hours=6)

    return {
        "push_now": push_now,
        "priority": priority,
        "push_type": push_type,
        "channels": channels,
        "planned_at": planned_at.isoformat(),
        "reason": f"热度评分 {score}，分类 {category}，推送策略 {push_type}",
        "model_name": context.model_name,
        "prompt_version": context.prompt_version,
        "title": summary_result.get("title") or context.news.title,
    }
