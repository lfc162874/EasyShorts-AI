from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from types import SimpleNamespace
from datetime import date

from app.agents.runtime import build_agent_runtime
from app.agents.structured_models import HotspotStructuredOutput
from app.core.constants import NewsStatus
from app.db.base import Base
from app.db.models.agent import DigestReport, HotTopic, PushPlan, PushRecord
from app.db.models.business import News, NewsSource
from app.services.agent_run_service import create_agent_run_for_news, execute_agent_run, execute_push_plan
from app.services.agent_config_service import get_agent_config, get_agent_model_options, update_agent_config
from app.services.bootstrap_service import bootstrap_default_data
from app.services.digest_service import create_agent_run_for_digest, execute_digest_run, get_digest_report_detail, push_digest_report


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)()


def test_agent_config_defaults_and_model_options():
    with make_session() as db:
        bootstrap_default_data(db)

        config = get_agent_config(db)
        assert config["default_model_name"] == "qwen3.5-plus"
        assert config["supported_models"] == ["qwen3.5-plus", "qwen-max", "deepseek-v3"]
        assert config["default_provider"] == "dashscope"
        assert config["prompt_version"] == "v1"
        assert config["push_channels"] == ["email", "feishu"]
        assert config["hot_threshold"] == 35

        options = get_agent_model_options(db)
        assert options[0]["value"] == "qwen3.5-plus"
        assert options[0]["label"] == "通义千问 3.5 Plus"
        assert options[0]["is_default"] is True

        runtime = build_agent_runtime(db, requested_model_name="qwen-max")
        assert runtime.model_name == "qwen-max"
        assert runtime.provider == "dashscope"
        assert runtime.supported_models == ["qwen3.5-plus", "qwen-max", "deepseek-v3"]
        assert runtime.prompt_version == "v1"


def test_agent_config_can_be_updated():
    with make_session() as db:
        bootstrap_default_data(db)

        updated = update_agent_config(
            db,
            {
                "default_model_name": "deepseek-v3",
                "supported_models": ["deepseek-v3", "qwen3.5-plus"],
                "default_provider": "openai",
                "prompt_version": "v2",
                "push_channels": ["email"],
            },
        )

        assert updated["default_model_name"] == "deepseek-v3"
        assert updated["supported_models"] == ["deepseek-v3", "qwen3.5-plus"]
        assert updated["default_provider"] == "openai"
        assert updated["prompt_version"] == "v2"
        assert updated["push_channels"] == ["email"]


def test_execute_agent_run_creates_hot_topic_and_push_plan():
    with make_session() as db:
        bootstrap_default_data(db)

        source = NewsSource(
            source_key="agent_test_source",
            name="OpenAI Blog",
            source_type="MANUAL",
            url="https://example.com/openai/blog",
            category="模型发布",
            language="en",
            fetch_interval_minutes=60,
            is_enabled=True,
            extra={},
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        news = News(
            title="OpenAI launches a new agent model",
            content="OpenAI released a new agent model for coding, reasoning, and tool use. The model update and open source ecosystem impact are significant.",
            source=source.name,
            source_id=source.id,
            source_url=source.url,
            url="https://example.com/openai/blog/agent-model",
            status=NewsStatus.FILTERED.value,
            hot_score=48,
            language="en",
            summary="OpenAI released a new agent model.",
            translated_title=None,
            translated_content=None,
            script=None,
            tags=None,
            filter_reason=None,
            raw_metadata={},
        )
        db.add(news)
        db.commit()
        db.refresh(news)

        run = create_agent_run_for_news(
            db,
            news_id=news.id,
            model_name=None,
            force=False,
            triggered_by=1,
            request_id="req-agent",
        )
        executed = execute_agent_run(db, run.id)

        assert executed.status == "SUCCESS"
        assert executed.model_name == "qwen3.5-plus"
        assert executed.current_step == "push_planner"
        assert executed.result is not None
        assert executed.result["hot_topic"]["title"]
        assert executed.result["push_plan"]["biz_type"] == "hot_topic"

        topic = db.scalar(select(HotTopic).where(HotTopic.primary_news_id == news.id))
        plan = db.scalar(select(PushPlan).where(PushPlan.run_id == run.id))
        assert topic is not None
        assert topic.status == "ACTIVE"
        assert topic.model_name == "qwen3.5-plus"
        assert plan is not None
        assert plan.topic_id == topic.id
        assert plan.model_name == "qwen3.5-plus"

        executed_plan = execute_push_plan(db, plan.id)
        assert executed_plan.status == "EXECUTED"

        push_records = db.scalars(select(PushRecord).where(PushRecord.plan_id == plan.id)).all()
        assert push_records
        assert all(record.status == "SENT" for record in push_records)


def test_execute_digest_run_creates_report_and_push_plan():
    with make_session() as db:
        bootstrap_default_data(db)

        topic_one = HotTopic(
            topic_key="digest-topic-1",
            title="OpenAI 发布新的 Agent 框架",
            summary="OpenAI 发布新的 Agent 框架，支持多工具协作。",
            category="AI Agent",
            tags=["OpenAI", "Agent"],
            score=92,
            priority="HIGH",
            reason="高热度",
            trend="RISING",
            status="ACTIVE",
            model_name="qwen3.5-plus",
            prompt_version="v1",
            news_count=2,
            source_count=1,
            extra={},
        )
        topic_two = HotTopic(
            topic_key="digest-topic-2",
            title="DeepSeek 更新推理模型",
            summary="DeepSeek 更新推理模型与开源权重。",
            category="大模型",
            tags=["DeepSeek", "推理"],
            score=88,
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
        db.add_all([topic_one, topic_two])
        db.commit()
        db.refresh(topic_one)
        db.refresh(topic_two)

        run = create_agent_run_for_digest(
            db,
            report_type="DAILY",
            report_date=date(2026, 4, 16),
            topic_ids=[topic_one.id, topic_two.id],
            limit=10,
            model_name=None,
            force=False,
            triggered_by=1,
            request_id="req-digest",
        )
        executed = execute_digest_run(db, run.id)

        assert executed.status == "SUCCESS"
        assert executed.run_type == "digest"
        assert executed.result is not None
        assert executed.result["digest_report"]["title"]

        report = db.scalar(select(DigestReport).where(DigestReport.report_type == "DAILY"))
        assert report is not None
        assert report.status == "GENERATED"

        detail = get_digest_report_detail(db, report.id)
        assert len(detail["topics"]) == 2
        assert detail["push_plan"]["biz_type"] == "digest"

        pushed = push_digest_report(db, report.id, triggered_by=1, request_id="req-push")
        assert pushed["status"] == "PUBLISHED"
        assert pushed["push_plan"]["status"] == "EXECUTED"

        push_records = db.scalars(select(PushRecord).where(PushRecord.digest_id == report.id)).all()
        assert push_records
        assert all(record.status == "SENT" for record in push_records)


def test_agentscope_structured_runtime_bridge(monkeypatch):
    from app.agents import agentscope_runtime as runtime_mod

    class FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def __call__(self, msg, structured_model):
            return SimpleNamespace(
                metadata={
                    "is_hot": True,
                    "score": 88,
                    "priority": "HIGH",
                    "trend": "RISING",
                    "reason": "AgentScope structured output",
                    "keywords": ["OpenAI", "Agent"],
                }
            )

    runtime = SimpleNamespace(
        model_name="qwen3.5-plus",
        provider="dashscope",
        default_provider="dashscope",
    )

    monkeypatch.setattr(runtime_mod, "_AGENTSCOPE_INITIALIZED", True)
    monkeypatch.setattr(runtime_mod, "_resolve_dashscope_api_key", lambda: "fake-key")
    monkeypatch.setattr(runtime_mod, "ReActAgent", FakeAgent)
    monkeypatch.setattr(runtime_mod, "Toolkit", lambda: object())
    monkeypatch.setattr(runtime_mod, "InMemoryMemory", lambda: object())

    result = runtime_mod.run_structured_agent_sync(
        runtime=runtime,
        agent_name="HotspotAgent",
        system_prompt="system prompt",
        user_prompt="user prompt",
        structured_model=HotspotStructuredOutput,
    )

    assert result is not None
    assert result["is_hot"] is True
    assert result["score"] == 88
    assert result["priority"] == "HIGH"
    assert result["reason"] == "AgentScope structured output"
