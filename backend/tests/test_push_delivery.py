from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import PushPlanStatus, PushPlanType, PushRecordStatus
from app.db.base import Base
from app.db.models.agent import HotTopic, PushPlan, PushRecord
from app.db.models.system import SystemConfig
from app.services.push_record_service import execute_push_plan_records


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)()


def test_execute_push_plan_records_can_deliver_webhook():
    captured_requests: list[dict[str, object]] = []

    class FakeResponse:
        def __init__(self, body: bytes = b'{"ok": true}', status: int = 200) -> None:
            self._body = body
            self._status = status

        def read(self) -> bytes:
            return self._body

        def getcode(self) -> int:
            return self._status

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:  # noqa: ANN001, ANN201 - context manager protocol
            return False

    def fake_urlopen(request, timeout=None):  # noqa: ANN001
        captured_requests.append(
            {
                "url": request.full_url,
                "data": json.loads((request.data or b"{}").decode("utf-8")),
                "headers": dict(request.header_items()),
                "timeout": timeout,
            }
        )
        return FakeResponse()

    with make_session() as db:
        topic = HotTopic(
            topic_key="webhook-topic",
            title="OpenAI 发布新的 Agent 工具链",
            summary="OpenAI 推出新的 Agent 工具链，支持更强的任务编排。",
            category="AI Agent",
            tags=["OpenAI", "Agent"],
            score=92,
            priority="HIGH",
            reason="高热度",
            trend="RISING",
            status="ACTIVE",
            model_name="qwen3.5-plus",
            prompt_version="v1",
            news_count=1,
            source_count=1,
            extra={},
        )
        db.add(topic)
        db.commit()
        db.refresh(topic)

        db.add(
            SystemConfig(
                category="push",
                config_key="webhook_url",
                config_value="https://example.com/push",
                value_type="STRING",
                description="测试 Webhook",
                is_secret=False,
                is_enabled=True,
            )
        )
        db.add(
            SystemConfig(
                category="push",
                config_key="delivery_retry_count",
                config_value="1",
                value_type="INTEGER",
                description="测试重试次数",
                is_secret=False,
                is_enabled=True,
            )
        )
        db.commit()

        plan = PushPlan(
            biz_type="hot_topic",
            biz_id=str(topic.id),
            run_id=None,
            topic_id=topic.id,
            push_now=True,
            priority="HIGH",
            push_type=PushPlanType.IMMEDIATE.value,
            channels=["webhook"],
            planned_at=datetime.now(UTC),
            status=PushPlanStatus.SCHEDULED.value,
            reason="测试推送",
            model_name="qwen3.5-plus",
            prompt_version="v1",
            extra={"title": "测试推送标题"},
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        with patch("app.services.push_delivery_service.urllib_request.urlopen", side_effect=fake_urlopen):
            records = execute_push_plan_records(
                db,
                plan,
                request_id="req-webhook",
                triggered_by=1,
            )

        assert len(records) == 1
        record = records[0]
        assert record.status == PushRecordStatus.SENT.value
        assert record.result is not None
        assert record.result["simulated"] is False
        assert record.result["response_status"] == 200

        stored_record = db.scalar(select(PushRecord).where(PushRecord.plan_id == plan.id))
        assert stored_record is not None
        assert stored_record.status == PushRecordStatus.SENT.value
        assert stored_record.payload is not None
        assert stored_record.payload["channel"] == "webhook"

        assert captured_requests
        captured = captured_requests[0]
        assert captured["url"] == "https://example.com/push"
        assert captured["data"]["title"] == "测试推送标题"
        assert "message_text" in captured["data"]
