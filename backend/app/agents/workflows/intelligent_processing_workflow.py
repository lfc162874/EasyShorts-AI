from __future__ import annotations

from app.agents.classification_agent import run_classification_agent
from app.agents.enrichment_agent import run_enrichment_agent
from app.agents.hotspot_agent import run_hotspot_agent
from app.agents.push_planner_agent import run_push_planner_agent
from app.agents.summary_agent import run_summary_agent
from app.agents.context import AgentExecutionContext


def run_single_article_workflow(context: AgentExecutionContext) -> dict[str, object]:
    hotspot = run_hotspot_agent(context)
    result: dict[str, object] = {
        "hotspot": hotspot,
    }
    if not hotspot["is_hot"]:
        return result

    classification = run_classification_agent(context, hotspot)
    summary = run_summary_agent(context, hotspot, classification)
    enrichment = run_enrichment_agent(context, classification, summary)
    push_plan = run_push_planner_agent(context, hotspot, classification, summary)
    result.update(
        {
            "classification": classification,
            "summary": summary,
            "enrichment": enrichment,
            "push_plan": push_plan,
        }
    )
    return result
