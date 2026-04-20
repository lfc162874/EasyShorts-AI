"""agent intelligent processing

Revision ID: 20260416_0003
Revises: 20260414_0002
Create Date: 2026-04-16 00:20:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from app.db.models.mixins import ID_TYPE

revision = "20260416_0003"
down_revision = "20260414_0002"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return inspect(bind).has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "agent_runs"):
        op.create_table(
            "agent_runs",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("parent_run_id", ID_TYPE, nullable=True),
            sa.Column("task_job_id", ID_TYPE, nullable=True),
            sa.Column("run_type", sa.String(length=32), nullable=False),
            sa.Column("biz_type", sa.String(length=64), nullable=False),
            sa.Column("biz_id", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
            sa.Column("current_step", sa.String(length=64), nullable=True),
            sa.Column("model_name", sa.String(length=128), nullable=False),
            sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default=sa.text("'v1'")),
            sa.Column("input_summary", sa.Text(), nullable=True),
            sa.Column("output_summary", sa.Text(), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("triggered_by", ID_TYPE, nullable=True),
            sa.Column("request_id", sa.String(length=64), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["parent_run_id"], ["agent_runs.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["task_job_id"], ["task_jobs.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_agent_runs_status", "agent_runs", ["status"])
        op.create_index("ix_agent_runs_run_type", "agent_runs", ["run_type"])
        op.create_index("ix_agent_runs_biz_type", "agent_runs", ["biz_type"])
        op.create_index("ix_agent_runs_biz_id", "agent_runs", ["biz_id"])
        op.create_index("ix_agent_runs_request_id", "agent_runs", ["request_id"])

    if not _table_exists(bind, "agent_run_steps"):
        op.create_table(
            "agent_run_steps",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("run_id", ID_TYPE, nullable=False),
            sa.Column("step_code", sa.String(length=64), nullable=False),
            sa.Column("agent_name", sa.String(length=128), nullable=False),
            sa.Column("step_order", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
            sa.Column("model_name", sa.String(length=128), nullable=False),
            sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default=sa.text("'v1'")),
            sa.Column("input_summary", sa.Text(), nullable=True),
            sa.Column("output_summary", sa.Text(), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("run_id", "step_code", name="uq_agent_run_steps_run_step_code"),
        )
        op.create_index("ix_agent_run_steps_run_id", "agent_run_steps", ["run_id"])
        op.create_index("ix_agent_run_steps_status", "agent_run_steps", ["status"])
        op.create_index("ix_agent_run_steps_step_code", "agent_run_steps", ["step_code"])

    if not _table_exists(bind, "agent_run_artifacts"):
        op.create_table(
            "agent_run_artifacts",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("run_id", ID_TYPE, nullable=False),
            sa.Column("step_id", ID_TYPE, nullable=True),
            sa.Column("artifact_type", sa.String(length=64), nullable=False),
            sa.Column("artifact_key", sa.String(length=128), nullable=False),
            sa.Column("content_json", sa.JSON(), nullable=True),
            sa.Column("content_text", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["step_id"], ["agent_run_steps.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("run_id", "step_id", "artifact_key", name="uq_agent_run_artifacts_key"),
        )
        op.create_index("ix_agent_run_artifacts_run_id", "agent_run_artifacts", ["run_id"])
        op.create_index("ix_agent_run_artifacts_step_id", "agent_run_artifacts", ["step_id"])
        op.create_index("ix_agent_run_artifacts_artifact_type", "agent_run_artifacts", ["artifact_type"])

    if not _table_exists(bind, "hot_topics"):
        op.create_table(
            "hot_topics",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("topic_key", sa.String(length=128), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("category", sa.String(length=64), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=True),
            sa.Column("score", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("priority", sa.String(length=32), nullable=False, server_default=sa.text("'MEDIUM'")),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("trend", sa.String(length=64), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'ACTIVE'")),
            sa.Column("model_name", sa.String(length=128), nullable=False),
            sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default=sa.text("'v1'")),
            sa.Column("news_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("source_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("primary_news_id", ID_TYPE, nullable=True),
            sa.Column("extra", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["primary_news_id"], ["news.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("topic_key", name="uq_hot_topics_topic_key"),
        )
        op.create_index("ix_hot_topics_status", "hot_topics", ["status"])
        op.create_index("ix_hot_topics_category", "hot_topics", ["category"])
        op.create_index("ix_hot_topics_score", "hot_topics", ["score"])

    if not _table_exists(bind, "hot_topic_items"):
        op.create_table(
            "hot_topic_items",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("topic_id", ID_TYPE, nullable=False),
            sa.Column("news_id", ID_TYPE, nullable=False),
            sa.Column("source_id", ID_TYPE, nullable=True),
            sa.Column("weight", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["topic_id"], ["hot_topics.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["news_id"], ["news.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("topic_id", "news_id", name="uq_hot_topic_items_topic_news"),
        )
        op.create_index("ix_hot_topic_items_topic_id", "hot_topic_items", ["topic_id"])
        op.create_index("ix_hot_topic_items_news_id", "hot_topic_items", ["news_id"])
        op.create_index("ix_hot_topic_items_source_id", "hot_topic_items", ["source_id"])

    if not _table_exists(bind, "push_plans"):
        op.create_table(
            "push_plans",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("biz_type", sa.String(length=64), nullable=False),
            sa.Column("biz_id", sa.String(length=64), nullable=False),
            sa.Column("run_id", ID_TYPE, nullable=True),
            sa.Column("topic_id", ID_TYPE, nullable=True),
            sa.Column("push_now", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("priority", sa.String(length=32), nullable=False, server_default=sa.text("'LOW'")),
            sa.Column("push_type", sa.String(length=32), nullable=False, server_default=sa.text("'SCHEDULED'")),
            sa.Column("channels", sa.JSON(), nullable=True),
            sa.Column("planned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("model_name", sa.String(length=128), nullable=False),
            sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default=sa.text("'v1'")),
            sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("extra", sa.JSON(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["topic_id"], ["hot_topics.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_push_plans_status", "push_plans", ["status"])
        op.create_index("ix_push_plans_priority", "push_plans", ["priority"])
        op.create_index("ix_push_plans_biz_type", "push_plans", ["biz_type"])
        op.create_index("ix_push_plans_biz_id", "push_plans", ["biz_id"])


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "push_plans"):
        op.drop_index("ix_push_plans_biz_id", table_name="push_plans")
        op.drop_index("ix_push_plans_biz_type", table_name="push_plans")
        op.drop_index("ix_push_plans_priority", table_name="push_plans")
        op.drop_index("ix_push_plans_status", table_name="push_plans")
        op.drop_table("push_plans")

    if _table_exists(bind, "hot_topic_items"):
        op.drop_index("ix_hot_topic_items_source_id", table_name="hot_topic_items")
        op.drop_index("ix_hot_topic_items_news_id", table_name="hot_topic_items")
        op.drop_index("ix_hot_topic_items_topic_id", table_name="hot_topic_items")
        op.drop_table("hot_topic_items")

    if _table_exists(bind, "hot_topics"):
        op.drop_index("ix_hot_topics_score", table_name="hot_topics")
        op.drop_index("ix_hot_topics_category", table_name="hot_topics")
        op.drop_index("ix_hot_topics_status", table_name="hot_topics")
        op.drop_table("hot_topics")

    if _table_exists(bind, "agent_run_artifacts"):
        op.drop_index("ix_agent_run_artifacts_artifact_type", table_name="agent_run_artifacts")
        op.drop_index("ix_agent_run_artifacts_step_id", table_name="agent_run_artifacts")
        op.drop_index("ix_agent_run_artifacts_run_id", table_name="agent_run_artifacts")
        op.drop_table("agent_run_artifacts")

    if _table_exists(bind, "agent_run_steps"):
        op.drop_index("ix_agent_run_steps_step_code", table_name="agent_run_steps")
        op.drop_index("ix_agent_run_steps_status", table_name="agent_run_steps")
        op.drop_index("ix_agent_run_steps_run_id", table_name="agent_run_steps")
        op.drop_table("agent_run_steps")

    if _table_exists(bind, "agent_runs"):
        op.drop_index("ix_agent_runs_request_id", table_name="agent_runs")
        op.drop_index("ix_agent_runs_biz_id", table_name="agent_runs")
        op.drop_index("ix_agent_runs_biz_type", table_name="agent_runs")
        op.drop_index("ix_agent_runs_run_type", table_name="agent_runs")
        op.drop_index("ix_agent_runs_status", table_name="agent_runs")
        op.drop_table("agent_runs")
