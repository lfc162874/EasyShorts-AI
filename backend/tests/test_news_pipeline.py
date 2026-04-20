import json

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.constants import NewsFetchMode, NewsSourceType, NewsStatus
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

        monkeypatch.setattr("app.services.collector_service._fetch_remote_text", lambda _url, **_: sample_rss)

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
        assert news_item.category == "模型发布"
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


def test_sync_web_news_source_collects_article_pages(monkeypatch):
    index_html = """
    <html>
      <head>
        <title>AI News Hub</title>
        <meta name="description" content="Latest AI news hub" />
      </head>
      <body>
        <main>
          <a href="https://example.com/posts/openai-model">OpenAI ships a new model</a>
          <a href="https://example.com/posts/agent-tools">Agent tooling update</a>
          <a href="/about">About</a>
        </main>
      </body>
    </html>
    """.strip()

    article_pages = {
        "https://example.com/posts/openai-model": """
        <html>
          <head>
            <title>OpenAI ships a new model</title>
            <meta property="og:title" content="OpenAI ships a new model" />
            <meta property="og:description" content="The model improves reasoning and tool use." />
            <meta property="article:published_time" content="2026-04-15T08:00:00+00:00" />
            <meta property="article:author" content="Editor" />
          </head>
          <body>
            <article>
              <p>OpenAI released a model that improves reasoning and tool use.</p>
              <p>It is relevant for agent workflows.</p>
            </article>
          </body>
        </html>
        """.strip(),
        "https://example.com/posts/agent-tools": """
        <html>
          <head>
            <title>Agent tooling update</title>
            <meta property="og:title" content="Agent tooling update" />
            <meta property="og:description" content="A new toolchain improves agent orchestration." />
            <meta property="article:published_time" content="2026-04-15T09:00:00+00:00" />
          </head>
          <body>
            <article>
              <p>The new toolchain improves agent orchestration and observability.</p>
            </article>
          </body>
        </html>
        """.strip(),
    }

    def fake_fetch(url: str, **_: object) -> str:
        if url == "https://example.com/news":
            return index_html
        if url in article_pages:
            return article_pages[url]
        raise AssertionError(f"unexpected url: {url}")

    with make_session() as db:
        source = NewsSource(
            source_key="example_web",
            name="Example Web",
            source_type=NewsSourceType.WEB.value,
            url="https://example.com/news",
            category="模型发布",
            language="en",
            fetch_interval_minutes=60,
            is_enabled=True,
            extra={"weight": 60},
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        monkeypatch.setattr("app.services.collector_service._fetch_remote_text", fake_fetch)

        result = sync_news_source(
            db=db,
            source_id=source.id,
            fetch_mode=NewsFetchMode.MANUAL,
            triggered_by=1,
            request_id="req-web",
        )

        assert result["total_count"] == 2
        assert result["new_count"] == 2
        assert result["duplicate_count"] == 0
        assert result["filtered_count"] == 2
        assert result["rejected_count"] == 0

        items = db.scalars(select(News).where(News.source_id == source.id).order_by(News.id.asc())).all()
        assert len(items) == 2
        assert items[0].title == "OpenAI ships a new model"
        assert items[0].status == NewsStatus.FILTERED.value
        assert items[0].category == "模型发布"
        assert items[0].summary
        assert items[0].translated_title
        assert items[0].translated_title != items[0].title
        assert items[1].title == "Agent tooling update"
        assert items[1].status == NewsStatus.FILTERED.value
        assert items[1].summary
        assert items[1].translated_title


def test_sync_zhihu_web_source_uses_explicit_article_urls(monkeypatch):
    zhihu_articles = {
        "https://zhuanlan.zhihu.com/p/706129671": {
            "title": "知乎直答：用提问发现世界",
            "excerpt": "知乎发布了新的 AI 产品，围绕提问与检索体验展开。",
            "content": (
                "<article><p>知乎直答围绕提问发现知识，聚合问答、检索和知识发现能力，"
                "帮助用户更快定位 AI、产品和技术讨论中的关键信息。</p>"
                "<p>这次更新强调用更自然的提问方式连接内容与答案，降低信息检索成本，"
                "对需要持续关注 AI 热点的人来说更容易建立稳定的追踪路径。</p></article>"
            ),
            "created": "2026-04-15T08:00:00+00:00",
            "author": {"name": "知乎官方"},
        },
        "https://zhuanlan.zhihu.com/p/2011841127288938794": {
            "title": "阿里巴巴将大模型品牌统一为千问",
            "excerpt": "阿里在模型命名和产品方向上做了统一。",
            "content": (
                "<article><p>阿里巴巴将大模型品牌统一为千问，进一步聚焦 AI 能力、"
                "智能体协作和多模态应用，强调从基础模型到产品体验的一体化推进。</p>"
                "<p>这一动作也让外界更容易把通义、千问和相关产品线联系到一起，"
                "有助于理解国内大模型赛道的产品叙事和生态布局。</p></article>"
            ),
            "created": "2026-04-15T09:00:00+00:00",
            "author": {"name": "AI 观察者"},
        },
    }

    def fake_fetch(url: str, **_: object) -> str:
        if url == "https://www.zhihu.com/":
            raise AssertionError("source page should not be fetched when explicit article urls are present")
        if url.startswith("https://www.zhihu.com/api/v4/articles/"):
            article_id = url.rsplit("/", 1)[-1]
            article_url = f"https://zhuanlan.zhihu.com/p/{article_id}"
            payload = zhihu_articles.get(article_url)
            if payload is not None:
                return json.dumps(payload, ensure_ascii=False)
        payload = zhihu_articles.get(url)
        if payload is not None:
            return json.dumps(payload, ensure_ascii=False)
        raise AssertionError(f"unexpected url: {url}")

    with make_session() as db:
        source = NewsSource(
            source_key="zhihu_ai_hot_test",
            name="知乎",
            source_type=NewsSourceType.WEB.value,
            url="https://www.zhihu.com/",
            category="中文社区",
            language="zh",
            fetch_interval_minutes=180,
            is_enabled=True,
            extra={
                "mode": "list",
                "max_items": 5,
                "article_urls": list(zhihu_articles.keys()),
            },
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        monkeypatch.setattr("app.services.collector_service._fetch_remote_text", fake_fetch)

        result = sync_news_source(
            db=db,
            source_id=source.id,
            fetch_mode=NewsFetchMode.MANUAL,
            triggered_by=1,
            request_id="req-zhihu",
        )

        assert result["total_count"] == 2
        assert result["new_count"] == 2
        assert result["duplicate_count"] == 0
        assert result["filtered_count"] == 2

        items = db.scalars(select(News).where(News.source_id == source.id).order_by(News.id.asc())).all()
        assert len(items) == 2
        assert items[0].title == "知乎直答：用提问发现世界"
        assert items[0].summary
        assert items[0].translated_title
        assert items[1].title == "阿里巴巴将大模型品牌统一为千问"
        assert items[1].summary
        assert items[1].translated_title


def test_sync_zhihu_source_returns_clear_auth_error_when_risk_payload_detected(monkeypatch):
    def fake_fetch(url: str, **_: object) -> str:
        if url.startswith("https://www.zhihu.com/api/v4/articles/"):
            return json.dumps(
                {
                    "error": {
                        "message": "请求参数异常，请升级客户端后重试。",
                        "code": 10003,
                    }
                },
                ensure_ascii=False,
            )
        raise AssertionError(f"unexpected url: {url}")

    with make_session() as db:
        source = NewsSource(
            source_key="zhihu_ai_hot_risk",
            name="知乎",
            source_type=NewsSourceType.WEB.value,
            url="https://www.zhihu.com/",
            category="中文社区",
            language="zh",
            fetch_interval_minutes=180,
            is_enabled=True,
            extra={
                "mode": "list",
                "max_items": 1,
                "article_urls": ["https://zhuanlan.zhihu.com/p/706129671"],
            },
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        monkeypatch.setattr("app.services.collector_service._fetch_remote_text", fake_fetch)

        result = sync_news_source(
            db=db,
            source_id=source.id,
            fetch_mode=NewsFetchMode.MANUAL,
            triggered_by=1,
            request_id="req-zhihu-risk",
        )

        assert result["total_count"] == 0
        assert result["new_count"] == 0
        assert result["filtered_count"] == 0
        assert "cookie" in ((result["fetch_record"]["error_message"] or "").lower())


def test_sync_manual_news_source_uses_structured_items():
    with make_session() as db:
        source = NewsSource(
            source_key="manual_source",
            name="Manual Source",
            source_type=NewsSourceType.MANUAL.value,
            url="https://example.com/manual",
            category="行业动态",
            language="en",
            fetch_interval_minutes=60,
            is_enabled=True,
            extra={
                "items": [
                    {
                        "title": "Manual AI policy update",
                        "link": "https://example.com/manual/policy-update",
                        "content": "登录社区云，欢迎回来。\nA manual item describing a policy update for AI governance.\n相关阅读：更多内容请访问原文。",
                        "published_at": "2026-04-15T10:00:00+00:00",
                        "author": "Ops",
                    },
                    {
                        "title": "Manual model release",
                        "link": "https://example.com/manual/model-release",
                        "content": "A manual item describing a new model release.",
                        "published_at": "2026-04-15T11:00:00+00:00",
                    },
                ]
            },
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        result = sync_news_source(
            db=db,
            source_id=source.id,
            fetch_mode=NewsFetchMode.MANUAL,
            triggered_by=1,
            request_id="req-manual",
        )

        assert result["total_count"] == 2
        assert result["new_count"] == 2
        assert result["duplicate_count"] == 0
        assert result["filtered_count"] == 2

        items = db.scalars(select(News).where(News.source_id == source.id).order_by(News.id.asc())).all()
        assert len(items) == 2
        assert items[0].title == "Manual AI policy update"
        assert items[0].status == NewsStatus.FILTERED.value
        assert "登录社区云" not in (items[0].content or "")
        assert "相关阅读" not in (items[0].content or "")
        assert items[1].title == "Manual model release"
        assert items[1].status == NewsStatus.FILTERED.value


def test_sync_news_source_merges_same_article_across_sources():
    shared_content = "OpenAI launched a new agent for coding tasks and reasoning workflows."

    with make_session() as db:
        source_a = NewsSource(
            source_key="manual_source_a",
            name="Manual Source A",
            source_type=NewsSourceType.MANUAL.value,
            url="https://example.com/manual/a",
            category="行业动态",
            language="en",
            fetch_interval_minutes=60,
            is_enabled=True,
            extra={
                "items": [
                    {
                        "title": "OpenAI launches a new agent",
                        "link": "https://example.com/manual/a/1",
                        "content": shared_content,
                        "published_at": "2026-04-15T12:00:00+00:00",
                    }
                ]
            },
        )
        source_b = NewsSource(
            source_key="manual_source_b",
            name="Manual Source B",
            source_type=NewsSourceType.MANUAL.value,
            url="https://example.com/manual/b",
            category="行业动态",
            language="en",
            fetch_interval_minutes=60,
            is_enabled=True,
            extra={
                "items": [
                    {
                        "title": "OpenAI launches a new agent",
                        "link": "https://example.com/manual/b/1",
                        "content": shared_content,
                        "published_at": "2026-04-15T12:05:00+00:00",
                    }
                ]
            },
        )
        db.add_all([source_a, source_b])
        db.commit()
        db.refresh(source_a)
        db.refresh(source_b)

        first_result = sync_news_source(
            db=db,
            source_id=source_a.id,
            fetch_mode=NewsFetchMode.MANUAL,
            triggered_by=1,
            request_id="req-merge-a",
        )
        second_result = sync_news_source(
            db=db,
            source_id=source_b.id,
            fetch_mode=NewsFetchMode.MANUAL,
            triggered_by=1,
            request_id="req-merge-b",
        )

        assert first_result["new_count"] == 1
        assert second_result["new_count"] == 0
        assert second_result["duplicate_count"] == 1
        assert second_result["filtered_count"] == 1

        items = db.scalars(select(News).order_by(News.id.asc())).all()
        assert len(items) == 1
        merged = items[0]
        assert merged.raw_metadata is not None
        merged_sources = merged.raw_metadata.get("merged_sources") if isinstance(merged.raw_metadata, dict) else None
        assert isinstance(merged_sources, list)
        assert len(merged_sources) == 2
