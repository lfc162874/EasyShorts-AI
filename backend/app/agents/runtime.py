from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.agent_config_service import get_agent_config

logger = get_logger(__name__)

try:  # pragma: no cover - optional dependency in local dev
    import agentscope as _agentscope  # type: ignore
except ImportError:  # pragma: no cover - fallback when dependency is not installed
    _agentscope = None


@dataclass(slots=True)
class AgentRuntime:
    model_name: str
    provider: str
    default_provider: str
    prompt_version: str
    supported_models: list[str]
    push_channels: list[str]
    hot_threshold: int
    prompt_bundle: dict[str, str]

    @property
    def has_agentscope(self) -> bool:
        return _agentscope is not None

    def describe(self) -> dict[str, object]:
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "default_provider": self.default_provider,
            "prompt_version": self.prompt_version,
            "supported_models": self.supported_models,
            "push_channels": self.push_channels,
            "hot_threshold": self.hot_threshold,
            "has_agentscope": self.has_agentscope,
        }


def _resolve_provider(model_name: str, default_provider: str) -> str:
    provider = (default_provider or "").strip().lower()
    model_name = model_name.strip().lower()
    if provider in {"dashscope", "qwen"} or model_name.startswith("qwen"):
        return "dashscope"
    if provider in {"openai", "azure"} or model_name.startswith("gpt"):
        return "openai"
    return "rule_based"


def build_agent_runtime(db: Session, requested_model_name: str | None = None) -> AgentRuntime:
    config = get_agent_config(db)
    default_model_name = str(config["default_model_name"])
    model_name = (requested_model_name or default_model_name).strip() or default_model_name
    if model_name not in config["supported_models"]:
        logger.info("model %s not in supported models, accept it for runtime compatibility", model_name)
    default_provider = str(config["default_provider"])
    return AgentRuntime(
        model_name=model_name,
        provider=_resolve_provider(model_name, default_provider),
        default_provider=default_provider,
        prompt_version=str(config["prompt_version"]),
        supported_models=list(config["supported_models"]),
        push_channels=list(config["push_channels"]),
        hot_threshold=int(config["hot_threshold"]),
        prompt_bundle=dict(config["prompts"]),
    )
