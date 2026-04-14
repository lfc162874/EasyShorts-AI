"""news pipeline

Revision ID: 20260414_0002
Revises: 20260414_0001
Create Date: 2026-04-14 00:10:00
"""

from alembic import op
import sqlalchemy as sa

from app.db.models.mixins import ID_TYPE

revision = "20260414_0002"
down_revision = "20260414_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "news_sources",
        sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("source_key", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default=sa.text("'RSS'")),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=False, server_default=sa.text("'en'")),
        sa.Column("fetch_interval_minutes", sa.Integer(), nullable=False, server_default=sa.text("360")),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("source_key", name="uq_news_sources_source_key"),
    )
    op.create_index("ix_news_sources_source_type", "news_sources", ["source_type"])
    op.create_index("ix_news_sources_is_enabled", "news_sources", ["is_enabled"])

    op.create_table(
        "news_fetch_records",
        sa.Column("id", ID_TYPE, primary_key=True, autoincrement=True),
        sa.Column("source_id", ID_TYPE, nullable=False),
        sa.Column("task_job_id", ID_TYPE, nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("fetch_mode", sa.String(length=32), nullable=False, server_default=sa.text("'MANUAL'")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("new_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("filtered_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_job_id"], ["task_jobs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_news_fetch_records_source_id", "news_fetch_records", ["source_id"])
    op.create_index("ix_news_fetch_records_status", "news_fetch_records", ["status"])
    op.create_index("ix_news_fetch_records_request_id", "news_fetch_records", ["request_id"])

    op.add_column("news", sa.Column("source_id", ID_TYPE, nullable=True))
    op.add_column("news", sa.Column("source_url", sa.String(length=500), nullable=True))
    op.add_column("news", sa.Column("dedup_hash", sa.String(length=128), nullable=True))
    op.add_column("news", sa.Column("category", sa.String(length=64), nullable=True))
    op.add_column(
        "news",
        sa.Column("hot_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "news",
        sa.Column("language", sa.String(length=16), nullable=False, server_default=sa.text("'en'")),
    )
    op.add_column("news", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("news", sa.Column("translated_title", sa.String(length=500), nullable=True))
    op.add_column("news", sa.Column("translated_content", sa.Text(), nullable=True))
    op.add_column("news", sa.Column("script", sa.Text(), nullable=True))
    op.add_column("news", sa.Column("tags", sa.JSON(), nullable=True))
    op.add_column("news", sa.Column("filter_reason", sa.Text(), nullable=True))
    op.add_column("news", sa.Column("raw_metadata", sa.JSON(), nullable=True))

    op.create_index("ix_news_source_id", "news", ["source_id"])
    op.create_index("ix_news_category", "news", ["category"])
    op.create_index("ix_news_dedup_hash", "news", ["dedup_hash"])
    op.create_foreign_key(
        "fk_news_source_id_news_sources",
        "news",
        "news_sources",
        ["source_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_news_source_id_news_sources", "news", type_="foreignkey")
    op.drop_index("ix_news_dedup_hash", table_name="news")
    op.drop_index("ix_news_category", table_name="news")
    op.drop_index("ix_news_source_id", table_name="news")
    op.drop_column("news", "raw_metadata")
    op.drop_column("news", "filter_reason")
    op.drop_column("news", "tags")
    op.drop_column("news", "script")
    op.drop_column("news", "translated_content")
    op.drop_column("news", "translated_title")
    op.drop_column("news", "summary")
    op.drop_column("news", "language")
    op.drop_column("news", "hot_score")
    op.drop_column("news", "category")
    op.drop_column("news", "dedup_hash")
    op.drop_column("news", "source_url")
    op.drop_column("news", "source_id")

    op.drop_index("ix_news_fetch_records_request_id", table_name="news_fetch_records")
    op.drop_index("ix_news_fetch_records_status", table_name="news_fetch_records")
    op.drop_index("ix_news_fetch_records_source_id", table_name="news_fetch_records")
    op.drop_table("news_fetch_records")

    op.drop_index("ix_news_sources_is_enabled", table_name="news_sources")
    op.drop_index("ix_news_sources_source_type", table_name="news_sources")
    op.drop_table("news_sources")
