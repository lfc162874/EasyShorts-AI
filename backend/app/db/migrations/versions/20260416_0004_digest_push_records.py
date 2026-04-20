"""digest reports and push records

Revision ID: 20260416_0004
Revises: 20260416_0003
Create Date: 2026-04-16 01:20:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from app.db.models.mixins import ID_TYPE

revision = "20260416_0004"
down_revision = "20260416_0003"
branch_labels = None
depends_on = None


def _table_exists(bind, table_name: str) -> bool:
    return inspect(bind).has_table(table_name)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "digest_reports"):
        op.create_table(
            "digest_reports",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("report_type", sa.String(length=32), nullable=False, server_default=sa.text("'DAILY'")),
            sa.Column("report_date", sa.Date(), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("highlights", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'DRAFT'")),
            sa.Column("topic_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("model_name", sa.String(length=128), nullable=False),
            sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default=sa.text("'v1'")),
            sa.Column("run_id", ID_TYPE, nullable=True),
            sa.Column("task_job_id", ID_TYPE, nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.ForeignKeyConstraint(["task_job_id"], ["task_jobs.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("report_type", "report_date", name="uq_digest_reports_type_date"),
        )
        op.create_index("ix_digest_reports_status", "digest_reports", ["status"])
        op.create_index("ix_digest_reports_report_type", "digest_reports", ["report_type"])
        op.create_index("ix_digest_reports_report_date", "digest_reports", ["report_date"])
        op.create_index("ix_digest_reports_run_id", "digest_reports", ["run_id"])

    if not _table_exists(bind, "push_records"):
        op.create_table(
            "push_records",
            sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
            sa.Column("plan_id", ID_TYPE, nullable=True),
            sa.Column("digest_id", ID_TYPE, nullable=True),
            sa.Column("topic_id", ID_TYPE, nullable=True),
            sa.Column("channel", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
            sa.Column("request_id", sa.String(length=64), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("result", sa.JSON(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.ForeignKeyConstraint(["plan_id"], ["push_plans.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["digest_id"], ["digest_reports.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["topic_id"], ["hot_topics.id"], ondelete="SET NULL"),
        )
        op.create_index("ix_push_records_status", "push_records", ["status"])
        op.create_index("ix_push_records_channel", "push_records", ["channel"])
        op.create_index("ix_push_records_plan_id", "push_records", ["plan_id"])
        op.create_index("ix_push_records_digest_id", "push_records", ["digest_id"])
        op.create_index("ix_push_records_topic_id", "push_records", ["topic_id"])
        op.create_index("ix_push_records_request_id", "push_records", ["request_id"])


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "push_records"):
        op.drop_index("ix_push_records_request_id", table_name="push_records")
        op.drop_index("ix_push_records_topic_id", table_name="push_records")
        op.drop_index("ix_push_records_digest_id", table_name="push_records")
        op.drop_index("ix_push_records_plan_id", table_name="push_records")
        op.drop_index("ix_push_records_channel", table_name="push_records")
        op.drop_index("ix_push_records_status", table_name="push_records")
        op.drop_table("push_records")

    if _table_exists(bind, "digest_reports"):
        op.drop_index("ix_digest_reports_run_id", table_name="digest_reports")
        op.drop_index("ix_digest_reports_report_date", table_name="digest_reports")
        op.drop_index("ix_digest_reports_report_type", table_name="digest_reports")
        op.drop_index("ix_digest_reports_status", table_name="digest_reports")
        op.drop_table("digest_reports")
