from __future__ import annotations

from dataclasses import dataclass

from app.db.models.business import News
from app.agents.runtime import AgentRuntime


@dataclass(slots=True)
class AgentExecutionContext:
    news: News
    model_name: str
    prompt_version: str
    prompt_bundle: dict[str, str]
    config: dict[str, object]
    runtime: AgentRuntime | None = None
    force: bool = False
