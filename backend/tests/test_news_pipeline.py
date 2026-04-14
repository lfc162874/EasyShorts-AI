from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import NewsFetchMode, NewsStatus
from app.db.base import Base
from app.db.models.business import News, NewsSource
from app.services.bootstrap_service import bootstrap_default_data
from app.services.news_service import generate_news_content, sync_news_source
from app.schemas.news import NewsGenerateRequest


def make_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)()


def test_sync_news_source_parses_and_generates_content(monkeypatch):
    sample_rss = """
    <rss version="2.0">
      <channel>
        <title>OpenAI Blog</title>
        <item>
          <title>OpenAI releases a new reasoning model</title>
          <link>https://openai.com/blog/reasoning-model</link>
          <guid>https://openai.com/blog/reasoning-model</guid>
          <pubDate>Tue, 14 Apr 2026 08:00:00 GMT</pubDate>
          <description><![CDATA[OpenAI shipped a model that improves reasoning across coding and math tasks.]]></description>
        </item>
        <item>
          <title>OpenAI releases a new reasoning model</title>
          <link>https://openai.com/blog/reasoning-model</link>
          <guid>https://openai.com/blog/reasoning-model</guid>
          <pubDate>Tue, 14 Apr 2026 08:00:00 GMT</pubDate>
          <description><![CDATA[OpenAI shipped a model that improves reasoning across coding and math tasks.]]></description>
        </item>
      </channel>
    </rss>
    """.strip()

    with make_session() as db:
        bootstrap_default_data(db)
        source = db.scalar(select(NewsSource).where(NewsSource.source_key == "openai_blog"))
        assert source is not None

        monkeypatch.setattr(
            "app.services.news_service._fetch_remote_text",
            lambda _url: sample_rss,
        )

        result = sync_news_source(
            db=db,
            source_id=source.id,
            fetch_mode=NewsFetchMode.MANUAL,
            triggered_by=1,
            request_id="req-test",
        )

        assert result["total_count"] == 2
        assert result["new_count"] == 1
        assert result["duplicate_count"] == 1
        assert result["filtered_count"] == 1
        assert result["rejected_count"] == 0

        news_item = db.scalar(select(News).where(News.source_id == source.id))
        assert news_item is not None
        assert news_item.status == NewsStatus.FILTERED.value
        assert news_item.summary
        assert news_item.script
        assert news_item.tags

        generated = generate_news_content(
            db=db,
            news_id=news_item.id,
            payload=NewsGenerateRequest(style="broadcast"),
            triggered_by=1,
            request_id="req-generate",
        )

        assert generated["news"]["status"] == NewsStatus.SCRIPT_READY.value
        refreshed = db.get(News, news_item.id)
        assert refreshed is not None
        assert refreshed.status == NewsStatus.SCRIPT_READY.value
        assert "【风格】broadcast" in (refreshed.script or "")
        assert refreshed.translated_title
