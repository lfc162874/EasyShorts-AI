from __future__ import annotations

import asyncio
import os
from functools import lru_cache
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.agents.runtime import AgentRuntime

logger = get_logger(__name__)

try:  # pragma: no cover - optional runtime dependency
    import agentscope as _agentscope  # type: ignore
    from agentscope.agent import ReActAgent  # type: ignore
    from agentscope.formatter import DashScopeChatFormatter, OpenAIChatFormatter  # type: ignore
    from agentscope.memory import InMemoryMemory  # type: ignore
    from agentscope.message import Msg  # type: ignore
    from agentscope.model import DashScopeChatModel, OpenAIChatModel  # type: ignore
    from agentscope.tool import Toolkit  # type: ignore
except ImportError:  # pragma: no cover - fallback when dependency is missing
    _agentscope = None
    ReActAgent = None
    DashScopeChatFormatter = None
    OpenAIChatFormatter = None
    InMemoryMemory = None
    Msg = None
    DashScopeChatModel = None
    OpenAIChatModel = None
    Toolkit = None

_AGENTSCOPE_INITIALIZED = False
StructuredModelT = TypeVar("StructuredModelT", bound=BaseModel)


def agentscope_installed() -> bool:
    return _agentscope is not None


def _resolve_backend(runtime: AgentRuntime) -> str:
    provider = (runtime.provider or runtime.default_provider or "").strip().lower()
    model_name = runtime.model_name.strip().lower()
    if provider in {"dashscope", "qwen"} or model_name.startswith("qwen"):
        return "dashscope"
    if provider in {"openai", "azure"} or model_name.startswith("gpt"):
        return "openai"
    return "rule_based"


def _resolve_dashscope_api_key() -> str | None:
    return settings.dashscope_api_key or os.getenv("DASHSCOPE_API_KEY")


def _resolve_openai_api_key() -> str | None:
    return settings.openai_api_key or os.getenv("OPENAI_API_KEY")


def _resolve_openai_base_url() -> str | None:
    return settings.openai_base_url or os.getenv("OPENAI_BASE_URL")


def can_use_agentscope(runtime: AgentRuntime) -> bool:
    if not agentscope_installed():
        return False
    backend = _resolve_backend(runtime)
    if backend == "dashscope":
        return bool(_resolve_dashscope_api_key())
    if backend == "openai":
        return bool(_resolve_openai_api_key())
    return False


def _ensure_agentscope_initialized() -> None:
    global _AGENTSCOPE_INITIALIZED
    if _AGENTSCOPE_INITIALIZED or not agentscope_installed():
        return
    try:  # pragma: no cover - library side effect
        _agentscope.init(
            project="EasyShorts AI Backend",
            name="Agent Intelligent Processing",
            logging_level="INFO",
        )
    except Exception as exc:  # pragma: no cover - best effort initialization
        logger.info("agentscope init skipped: %s", exc)
    _AGENTSCOPE_INITIALIZED = True


@lru_cache(maxsize=16)
def _get_dashscope_model(model_name: str, api_key: str):
    if DashScopeChatModel is None:  # pragma: no cover - dependency guard
        return None
    return DashScopeChatModel(model_name=model_name, api_key=api_key, stream=False)


@lru_cache(maxsize=16)
def _get_openai_model(model_name: str, api_key: str, base_url: str | None):
    if OpenAIChatModel is None:  # pragma: no cover - dependency guard
        return None
    client_kwargs: dict[str, Any] = {}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAIChatModel(
        model_name=model_name,
        api_key=api_key,
        stream=False,
        client_type="openai",
        client_kwargs=client_kwargs or None,
    )


def _build_model(runtime: AgentRuntime):
    backend = _resolve_backend(runtime)
    if backend == "dashscope":
        api_key = _resolve_dashscope_api_key()
        if not api_key:
            return None
        return _get_dashscope_model(runtime.model_name, api_key)
    if backend == "openai":
        api_key = _resolve_openai_api_key()
        if not api_key:
            return None
        return _get_openai_model(runtime.model_name, api_key, _resolve_openai_base_url())
    return None


def _build_formatter(backend: str):
    if backend == "dashscope" and DashScopeChatFormatter is not None:
        return DashScopeChatFormatter()
    if backend == "openai" and OpenAIChatFormatter is not None:
        return OpenAIChatFormatter()
    return None


async def run_structured_agent(
    *,
    runtime: AgentRuntime,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    structured_model: type[StructuredModelT],
    max_iters: int = 3,
) -> dict[str, object] | None:
    if not can_use_agentscope(runtime):
        return None
    _ensure_agentscope_initialized()

    backend = _resolve_backend(runtime)
    model = _build_model(runtime)
    formatter = _build_formatter(backend)
    if model is None or formatter is None or ReActAgent is None or Msg is None or Toolkit is None or InMemoryMemory is None:
        return None

    try:
        agent = ReActAgent(
            name=agent_name,
            sys_prompt=system_prompt,
            model=model,
            formatter=formatter,
            toolkit=Toolkit(),
            memory=InMemoryMemory(),
            parallel_tool_calls=False,
            max_iters=max_iters,
        )
        response = await agent(
            Msg(name="user", content=user_prompt, role="user"),
            structured_model=structured_model,
        )
        metadata = getattr(response, "metadata", None) or {}
        if not metadata:
            logger.warning("agentscope structured output is empty for agent %s", agent_name)
            return None
        parsed = structured_model.model_validate(metadata)
        return parsed.model_dump()
    except Exception as exc:  # pragma: no cover - external model/runtime errors
        logger.warning("agentscope step %s failed, falling back to deterministic logic: %s", agent_name, exc)
        return None


def run_structured_agent_sync(
    *,
    runtime: AgentRuntime,
    agent_name: str,
    system_prompt: str,
    user_prompt: str,
    structured_model: type[StructuredModelT],
    max_iters: int = 3,
) -> dict[str, object] | None:
    try:
        return asyncio.run(
            run_structured_agent(
                runtime=runtime,
                agent_name=agent_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                structured_model=structured_model,
                max_iters=max_iters,
            )
        )
    except RuntimeError as exc:
        if "asyncio.run()" in str(exc):
            logger.warning("agentscope step %s skipped because the event loop is already running", agent_name)
            return None
        raise
