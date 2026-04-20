from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import ConfigValueType
from app.db.models.system import SystemConfig

AGENT_CONFIG_CATEGORY = "agent"
AGENT_PROMPT_CATEGORY = "prompt"
DEFAULT_AGENT_SUPPORTED_MODELS = ["qwen3.5-plus", "qwen-max", "deepseek-v3"]
DEFAULT_AGENT_DEFAULT_PROVIDER = "dashscope"
DEFAULT_AGENT_PROMPT_VERSION = "v1"
DEFAULT_AGENT_PUSH_CHANNELS = ["email", "feishu"]

PROMPT_KEY_TO_FILENAME = {
    "agent_hotspot_prompt": "hotspot_agent.md",
    "agent_classification_prompt": "classification_agent.md",
    "agent_summary_prompt": "summary_agent.md",
    "agent_enrichment_prompt": "enrichment_agent.md",
    "agent_push_planner_prompt": "push_planner_agent.md",
    "agent_digest_prompt": "digest_agent.md",
}


def _load_config_value(db: Session, category: str, config_key: str, default: str | None = None) -> str | None:
    config = db.scalar(
        select(SystemConfig).where(
            SystemConfig.category == category,
            SystemConfig.config_key == config_key,
            SystemConfig.is_enabled.is_(True),
        )
    )
    if config is None:
        return default
    return config.config_value


def _parse_json_or_csv(value: str | list[str] | None, default: list[str]) -> list[str]:
    if value is None:
        return list(default)
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items or list(default)
    raw = value.strip()
    if not raw:
        return list(default)
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            items = [str(item).strip() for item in parsed if str(item).strip()]
            if items:
                return items
    return [item.strip() for item in raw.split(",") if item.strip()] or list(default)


def _normalize_supported_models(default_model_name: str, supported_models: list[str]) -> list[str]:
    normalized = [item.strip() for item in supported_models if item.strip()]
    if default_model_name and default_model_name not in normalized:
        normalized.insert(0, default_model_name)
    seen: set[str] = set()
    ordered: list[str] = []
    for model_name in normalized:
        if model_name in seen:
            continue
        seen.add(model_name)
        ordered.append(model_name)
    return ordered


def _load_prompt_file(prompt_key: str) -> str:
    filename = PROMPT_KEY_TO_FILENAME.get(prompt_key)
    if filename is None:
        return ""
    prompt_path = Path(__file__).resolve().parents[1] / "agents" / "prompts" / filename
    if not prompt_path.exists():
        return ""
    return prompt_path.read_text(encoding="utf-8").strip()


def get_agent_prompt_bundle(db: Session) -> dict[str, str]:
    prompts: dict[str, str] = {}
    for prompt_key, filename in PROMPT_KEY_TO_FILENAME.items():
        config_value = _load_config_value(db, AGENT_PROMPT_CATEGORY, prompt_key)
        prompts[prompt_key] = (config_value or _load_prompt_file(prompt_key) or filename).strip()
    return prompts


def get_agent_config(db: Session) -> dict[str, Any]:
    default_model_name = (
        _load_config_value(db, AGENT_CONFIG_CATEGORY, "default_model_name", settings.agent_default_model_name)
        or settings.agent_default_model_name
    )
    supported_models = _parse_json_or_csv(
        _load_config_value(db, AGENT_CONFIG_CATEGORY, "supported_models"),
        list(settings.agent_supported_models) or list(DEFAULT_AGENT_SUPPORTED_MODELS),
    )
    supported_models = _normalize_supported_models(default_model_name, supported_models)
    provider = (
        _load_config_value(db, AGENT_CONFIG_CATEGORY, "default_provider", settings.agent_default_provider)
        or settings.agent_default_provider
    )
    prompt_version = (
        _load_config_value(db, AGENT_CONFIG_CATEGORY, "prompt_version", settings.agent_prompt_version)
        or settings.agent_prompt_version
    )
    push_channels = _parse_json_or_csv(
        _load_config_value(db, AGENT_CONFIG_CATEGORY, "push_channels"),
        list(DEFAULT_AGENT_PUSH_CHANNELS),
    )
    hot_threshold_raw = _load_config_value(db, "parameter", "news_hot_threshold", "35") or "35"
    try:
        hot_threshold = int(hot_threshold_raw)
    except ValueError:
        hot_threshold = 35

    return {
        "default_model_name": default_model_name,
        "supported_models": supported_models,
        "default_provider": provider,
        "prompt_version": prompt_version,
        "push_channels": push_channels,
        "hot_threshold": hot_threshold,
        "prompts": get_agent_prompt_bundle(db),
    }


def get_agent_model_options(db: Session) -> list[dict[str, Any]]:
    config = get_agent_config(db)
    default_model_name = config["default_model_name"]
    options: list[dict[str, Any]] = []
    for model_name in config["supported_models"]:
        options.append(
            {
                "value": model_name,
                "label": _build_model_label(model_name),
                "is_default": model_name == default_model_name,
            }
        )
    if not options:
        options.append(
            {
                "value": default_model_name,
                "label": _build_model_label(default_model_name),
                "is_default": True,
            }
        )
    return options


def update_agent_config(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    default_model_name = str(payload.get("default_model_name") or settings.agent_default_model_name).strip()
    supported_models = payload.get("supported_models")
    if supported_models is None:
        supported_models_list = _normalize_supported_models(default_model_name, list(settings.agent_supported_models))
    else:
        supported_models_list = _normalize_supported_models(
            default_model_name,
            _parse_json_or_csv(supported_models, list(settings.agent_supported_models)),
        )

    provider = str(payload.get("default_provider") or settings.agent_default_provider).strip() or settings.agent_default_provider
    prompt_version = str(payload.get("prompt_version") or settings.agent_prompt_version).strip() or settings.agent_prompt_version
    push_channels = payload.get("push_channels")
    push_channels_list = _parse_json_or_csv(push_channels, list(DEFAULT_AGENT_PUSH_CHANNELS))

    configs = [
        {
            "category": AGENT_CONFIG_CATEGORY,
            "config_key": "default_model_name",
            "config_value": default_model_name,
            "value_type": ConfigValueType.STRING.value,
            "description": "Agent 智能处理默认模型名称",
            "is_secret": False,
            "is_enabled": True,
        },
        {
            "category": AGENT_CONFIG_CATEGORY,
            "config_key": "supported_models",
            "config_value": json.dumps(supported_models_list, ensure_ascii=False),
            "value_type": ConfigValueType.JSON.value,
            "description": "Agent 支持的模型列表",
            "is_secret": False,
            "is_enabled": True,
        },
        {
            "category": AGENT_CONFIG_CATEGORY,
            "config_key": "default_provider",
            "config_value": provider,
            "value_type": ConfigValueType.STRING.value,
            "description": "Agent 默认模型提供方",
            "is_secret": False,
            "is_enabled": True,
        },
        {
            "category": AGENT_CONFIG_CATEGORY,
            "config_key": "prompt_version",
            "config_value": prompt_version,
            "value_type": ConfigValueType.STRING.value,
            "description": "Agent 提示词版本",
            "is_secret": False,
            "is_enabled": True,
        },
        {
            "category": AGENT_CONFIG_CATEGORY,
            "config_key": "push_channels",
            "config_value": json.dumps(push_channels_list, ensure_ascii=False),
            "value_type": ConfigValueType.JSON.value,
            "description": "Agent 默认推送渠道",
            "is_secret": False,
            "is_enabled": True,
        },
    ]

    for item in configs:
        config = db.scalar(
            select(SystemConfig).where(
                SystemConfig.category == item["category"],
                SystemConfig.config_key == item["config_key"],
            )
        )
        if config is None:
            config = SystemConfig(**item)
        else:
            for field, value in item.items():
                setattr(config, field, value)
        db.add(config)
    db.commit()

    return get_agent_config(db)


def _build_model_label(model_name: str) -> str:
    labels = {
        "qwen3.5-plus": "通义千问 3.5 Plus",
        "qwen-max": "通义千问 Max",
        "deepseek-v3": "DeepSeek V3",
        "deepseek-r1": "DeepSeek R1",
    }
    return labels.get(model_name, model_name)
