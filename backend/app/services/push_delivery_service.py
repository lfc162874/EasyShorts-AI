from __future__ import annotations

import json
import smtplib
import ssl
import time
from dataclasses import dataclass, field
from email.message import EmailMessage
from urllib import error as urllib_error
from urllib import request as urllib_request

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.common import normalize_whitespace
from app.core.logging import get_logger
from app.db.models.system import SystemConfig

logger = get_logger(__name__)


@dataclass(slots=True)
class PushDeliveryConfig:
    delivery_retry_count: int = 3
    delivery_timeout_seconds: int = 10
    webhook_url: str | None = None
    webhook_headers: dict[str, str] = field(default_factory=dict)
    channel_webhook_urls: dict[str, str] = field(default_factory=dict)
    email_smtp_host: str | None = None
    email_smtp_port: int = 587
    email_from: str | None = None
    email_to: list[str] = field(default_factory=list)
    email_username: str | None = None
    email_password: str | None = None
    email_use_tls: bool = True
    email_use_ssl: bool = False
    email_subject_prefix: str = "[EasyShorts]"


@dataclass(slots=True)
class PushDeliveryResult:
    channel: str
    success: bool
    simulated: bool
    delivery_mode: str
    message: str
    attempts: int = 0
    endpoint: str | None = None
    response_status: int | None = None
    response_body: str | None = None
    error_message: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "success": self.success,
            "simulated": self.simulated,
            "delivery_mode": self.delivery_mode,
            "message": self.message,
            "attempts": self.attempts,
            "endpoint": self.endpoint,
            "response_status": self.response_status,
            "response_body": self.response_body,
            "error_message": self.error_message,
        }


def _parse_bool(value: str | bool | None, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_int(value: str | int | None, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _parse_list(value: str | list[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [normalize_whitespace(str(item)) for item in value if normalize_whitespace(str(item))]
    raw = str(value).strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [normalize_whitespace(str(item)) for item in parsed if normalize_whitespace(str(item))]
    return [normalize_whitespace(item) for item in raw.split(",") if normalize_whitespace(item)]


def _parse_headers(value: str | None) -> dict[str, str]:
    if value is None:
        return {}
    raw = value.strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    headers: dict[str, str] = {}
    for key, item in parsed.items():
        normalized_key = normalize_whitespace(str(key))
        normalized_value = normalize_whitespace(str(item))
        if normalized_key and normalized_value:
            headers[normalized_key] = normalized_value
    return headers


def _load_config_values(db: Session) -> dict[str, str]:
    configs = db.scalars(
        select(SystemConfig).where(SystemConfig.category == "push", SystemConfig.is_enabled.is_(True))
    ).all()
    return {config.config_key: config.config_value for config in configs}


def load_push_delivery_config(db: Session) -> PushDeliveryConfig:
    values = _load_config_values(db)
    channel_webhook_urls = {
        "webhook": normalize_whitespace(values.get("webhook_url") or ""),
        "feishu": normalize_whitespace(values.get("feishu_webhook_url") or values.get("webhook_url") or ""),
        "wechat_work": normalize_whitespace(values.get("wechat_work_webhook_url") or values.get("webhook_url") or ""),
        "dingding": normalize_whitespace(values.get("dingding_webhook_url") or values.get("webhook_url") or ""),
        "dingtalk": normalize_whitespace(values.get("dingtalk_webhook_url") or values.get("dingding_webhook_url") or values.get("webhook_url") or ""),
        "slack": normalize_whitespace(values.get("slack_webhook_url") or values.get("webhook_url") or ""),
        "telegram": normalize_whitespace(values.get("telegram_webhook_url") or values.get("webhook_url") or ""),
    }
    return PushDeliveryConfig(
        delivery_retry_count=_parse_int(values.get("delivery_retry_count"), 3),
        delivery_timeout_seconds=_parse_int(values.get("delivery_timeout_seconds"), 10),
        webhook_url=normalize_whitespace(values.get("webhook_url") or "") or None,
        webhook_headers=_parse_headers(values.get("webhook_headers")),
        channel_webhook_urls={key: value for key, value in channel_webhook_urls.items() if value},
        email_smtp_host=normalize_whitespace(values.get("email_smtp_host") or "") or None,
        email_smtp_port=_parse_int(values.get("email_smtp_port"), 587),
        email_from=normalize_whitespace(values.get("email_from") or "") or None,
        email_to=_parse_list(values.get("email_to")),
        email_username=normalize_whitespace(values.get("email_username") or "") or None,
        email_password=normalize_whitespace(values.get("email_password") or "") or None,
        email_use_tls=_parse_bool(values.get("email_use_tls"), True),
        email_use_ssl=_parse_bool(values.get("email_use_ssl"), False),
        email_subject_prefix=normalize_whitespace(values.get("email_subject_prefix") or "[EasyShorts]") or "[EasyShorts]",
    )


def _build_channel_payload(channel: str, context: dict[str, object]) -> dict[str, object]:
    text = normalize_whitespace(str(context.get("message_text") or ""))
    title = normalize_whitespace(str(context.get("title") or "AI 热点推送"))
    summary = normalize_whitespace(str(context.get("summary") or ""))
    payload = dict(context.get("payload") or {})

    if channel == "webhook":
        return {
            **payload,
            "title": title,
            "summary": summary,
            "message_text": text,
        }
    if channel == "feishu":
        return {"msg_type": "text", "content": {"text": f"{title}\n\n{text}".strip()}}
    if channel in {"wechat_work", "dingding", "dingtalk"}:
        return {"msgtype": "text", "text": {"content": f"{title}\n\n{text}".strip()}}
    if channel == "slack":
        return {"text": f"{title}\n\n{text}".strip()}
    if channel == "telegram":
        return {"text": f"{title}\n\n{text}".strip()}
    return payload


def _http_post_json(
    url: str,
    payload: dict[str, object],
    *,
    headers: dict[str, str],
    timeout_seconds: int,
    retry_count: int,
) -> tuple[int, str, int]:
    body = json.dumps(jsonable_encoder(payload), ensure_ascii=False).encode("utf-8")
    request_headers = {"Content-Type": "application/json", **headers}
    last_error: Exception | None = None
    for attempt in range(1, max(1, retry_count) + 1):
        try:
            request = urllib_request.Request(url, data=body, headers=request_headers, method="POST")
            with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
                response_body = response.read().decode("utf-8", errors="ignore")
                return response.getcode() or 200, response_body, attempt
        except Exception as exc:  # pragma: no cover - network failure path is exercised in integration
            last_error = exc
            if attempt < retry_count:
                time.sleep(min(0.5 * (2 ** (attempt - 1)), 2.0))
    assert last_error is not None
    raise last_error


def _deliver_webhook_channel(
    *,
    channel: str,
    context: dict[str, object],
    config: PushDeliveryConfig,
) -> PushDeliveryResult:
    endpoint = config.channel_webhook_urls.get(channel) or config.webhook_url
    if not endpoint:
        return PushDeliveryResult(
            channel=channel,
            success=True,
            simulated=True,
            delivery_mode="simulated",
            message=f"未配置 {channel} Webhook，已模拟推送",
            attempts=0,
        )

    payload = _build_channel_payload(channel, context)
    try:
        response_status, response_body, attempts = _http_post_json(
            endpoint,
            payload,
            headers=config.webhook_headers,
            timeout_seconds=config.delivery_timeout_seconds,
            retry_count=config.delivery_retry_count,
        )
        return PushDeliveryResult(
            channel=channel,
            success=True,
            simulated=False,
            delivery_mode="real",
            message=f"已发送到 {channel}",
            attempts=attempts,
            endpoint=endpoint,
            response_status=response_status,
            response_body=response_body[:2000] if response_body else None,
        )
    except Exception as exc:
        logger.exception("push webhook delivery failed for channel=%s endpoint=%s", channel, endpoint)
        return PushDeliveryResult(
            channel=channel,
            success=False,
            simulated=False,
            delivery_mode="real",
            message=f"{channel} 推送失败",
            attempts=max(1, config.delivery_retry_count),
            endpoint=endpoint,
            error_message=str(exc),
        )


def _deliver_email_channel(
    *,
    context: dict[str, object],
    config: PushDeliveryConfig,
) -> PushDeliveryResult:
    if not config.email_smtp_host or not config.email_from or not config.email_to:
        return PushDeliveryResult(
            channel="email",
            success=True,
            simulated=True,
            delivery_mode="simulated",
            message="邮件 SMTP 未配置完整，已模拟推送",
            attempts=0,
        )

    title = normalize_whitespace(str(context.get("title") or "AI 热点推送"))
    text = normalize_whitespace(str(context.get("message_text") or ""))
    message = EmailMessage()
    message["Subject"] = f"{config.email_subject_prefix} {title}".strip()
    message["From"] = config.email_from
    message["To"] = ", ".join(config.email_to)
    message.set_content(text or title)

    timeout_seconds = max(1, config.delivery_timeout_seconds)
    last_error: Exception | None = None
    for attempt in range(1, max(1, config.delivery_retry_count) + 1):
        try:
            if config.email_use_ssl:
                with smtplib.SMTP_SSL(config.email_smtp_host, config.email_smtp_port, timeout=timeout_seconds) as server:
                    if config.email_username and config.email_password:
                        server.login(config.email_username, config.email_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(config.email_smtp_host, config.email_smtp_port, timeout=timeout_seconds) as server:
                    if config.email_use_tls:
                        server.starttls(context=ssl.create_default_context())
                    if config.email_username and config.email_password:
                        server.login(config.email_username, config.email_password)
                    server.send_message(message)
            return PushDeliveryResult(
                channel="email",
                success=True,
                simulated=False,
                delivery_mode="real",
                message="邮件已发送",
                attempts=attempt,
            )
        except Exception as exc:  # pragma: no cover - network failure path is exercised in integration
            last_error = exc
            if attempt < config.delivery_retry_count:
                time.sleep(min(0.5 * (2 ** (attempt - 1)), 2.0))

    assert last_error is not None
    logger.exception("push email delivery failed")
    return PushDeliveryResult(
        channel="email",
        success=False,
        simulated=False,
        delivery_mode="real",
        message="邮件推送失败",
        attempts=max(1, config.delivery_retry_count),
        error_message=str(last_error),
    )


def deliver_push_channel(
    *,
    channel: str,
    context: dict[str, object],
    config: PushDeliveryConfig,
) -> PushDeliveryResult:
    normalized_channel = normalize_whitespace(channel).lower()
    if normalized_channel == "email":
        return _deliver_email_channel(context=context, config=config)
    if normalized_channel in {"webhook", "feishu", "wechat_work", "dingding", "dingtalk", "slack", "telegram"}:
        return _deliver_webhook_channel(channel=normalized_channel, context=context, config=config)
    return PushDeliveryResult(
        channel=normalized_channel or channel,
        success=False,
        simulated=False,
        delivery_mode="real",
        message=f"不支持的推送渠道：{normalized_channel or channel}",
        attempts=0,
        error_message=f"unsupported channel: {normalized_channel or channel}",
    )
