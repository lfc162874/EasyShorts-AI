from __future__ import annotations

import hashlib
import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request as URLRequest
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import NewsFetchMode, NewsSourceType, NewsStatus, TaskStatus
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.logging import get_logger
from app.db.models.business import News, NewsFetchRecord, NewsSource
from app.db.models.system import SystemConfig
from app.schemas.news import (
    NewsDetailItem,
    NewsFetchRecordItem,
    NewsGenerateRequest,
    NewsItem,
    NewsListQuery,
    NewsSourceCreate,
    NewsSourceItem,
    NewsSourceUpdate,
)

logger = get_logger(__name__)


@dataclass(slots=True)
class ParsedNewsEntry:
    title: str
    link: str
    content: str
    published_at: datetime | None
    summary: str | None
    author: str | None
    guid: str | None
    raw: dict[str, str]


def _now() -> datetime:
    return datetime.now(UTC)


def _normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    return _normalize_whitespace(text)


def _contains_chinese(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _first_child_text(element: ET.Element, names: set[str]) -> str | None:
    for child in list(element):
        if _local_name(child.tag) not in names:
            continue
        text = "".join(child.itertext()) if list(child) else child.text or ""
        text = _normalize_whitespace(text)
        if text:
            return text
    return None


def _first_child_attr(element: ET.Element, names: set[str], attr: str) -> str | None:
    for child in list(element):
        if _local_name(child.tag) not in names:
            continue
        value = child.attrib.get(attr)
        if value:
            return _normalize_whitespace(value)
    return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    try:
        parsed = parsedate_to_datetime(candidate)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (TypeError, ValueError):
        pass

    try:
        normalized = candidate.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


def _fetch_remote_text(url: str) -> str:
    request = URLRequest(url, headers={"User-Agent": "EasyShortsAI/1.0"})
    with urlopen(request, timeout=20) as response:  # nosec - controlled project input
        raw = response.read()
        encoding = response.headers.get_content_charset() or "utf-8"
    return raw.decode(encoding, errors="ignore")


def _parse_feed_entries(source: NewsSource, raw_text: str) -> list[ParsedNewsEntry]:
    root = ET.fromstring(raw_text)
    tag = _local_name(root.tag).lower()
    if tag in {"rss", "rdf"}:
        items = root.findall(".//item")
    elif tag == "feed":
        items = root.findall(".//{*}entry")
    else:
        items = root.findall(".//item") or root.findall(".//{*}entry")

    entries: list[ParsedNewsEntry] = []
    for item in items:
        title = _first_child_text(item, {"title"}) or source.name
        link = _first_child_text(item, {"link"})
        if not link and _local_name(item.tag).lower() == "entry":
            link = _first_child_attr(item, {"link"}, "href")
        link = link or source.url

        content = _first_child_text(item, {"encoded", "content", "description", "summary"}) or ""
        summary = _first_child_text(item, {"summary", "description"})
        published_text = _first_child_text(item, {"pubdate", "published", "updated", "date"})
        author = _first_child_text(item, {"author", "creator", "name"})
        guid = _first_child_text(item, {"guid", "id"})
        if not content:
            content = summary or title

        raw = {
            "title": title,
            "link": link,
            "content": content,
            "summary": summary or "",
            "published": published_text or "",
            "author": author or "",
            "guid": guid or "",
        }
        entries.append(
            ParsedNewsEntry(
                title=_normalize_whitespace(title),
                link=_normalize_whitespace(link),
                content=_strip_html(content),
                published_at=_parse_datetime(published_text),
                summary=_strip_html(summary),
                author=_normalize_whitespace(author),
                guid=_normalize_whitespace(guid),
                raw=raw,
            )
        )
    return entries


def _is_sensitive(entry: ParsedNewsEntry, block_keywords: Iterable[str]) -> str | None:
    haystack = f"{entry.title}\n{entry.content}".lower()
    matched = [keyword for keyword in block_keywords if keyword and keyword.lower() in haystack]
    if matched:
        return "命中敏感词：" + "、".join(matched)
    return None


def _infer_category(source: NewsSource, entry: ParsedNewsEntry) -> str:
    if source.category:
        return source.category
    text = f"{entry.title} {entry.content}".lower()
    if any(keyword in text for keyword in ("openai", "anthropic", "gpt", "llm", "模型", "推理", "大模型")):
        return "模型发布"
    if any(keyword in text for keyword in ("paper", "arxiv", "论文", "研究")):
        return "研究论文"
    if any(keyword in text for keyword in ("open source", "opensource", "github", "hugging face", "huggingface", "开源")):
        return "开源生态"
    if any(keyword in text for keyword in ("policy", "监管", "法案", "政策")):
        return "政策监管"
    return "行业动态"


def _infer_language(source: NewsSource, entry: ParsedNewsEntry) -> str:
    if source.language:
        return source.language
    combined = f"{entry.title} {entry.content}"
    return "zh" if _contains_chinese(combined) else "en"


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


def _load_keyword_list(db: Session, category: str, config_key: str, default: list[str]) -> list[str]:
    raw = _load_config_value(db, category, config_key)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


def _load_prompt_bundle(db: Session) -> dict[str, str]:
    return {
        "summary_prompt": _load_config_value(
            db,
            "prompt",
            "news_summary_prompt",
            "请根据下面新闻内容生成中文摘要，突出核心结论和关键信息。",
        )
        or "",
        "title_prompt": _load_config_value(
            db,
            "prompt",
            "news_title_prompt",
            "请为下面这条新闻生成一个适合短视频封面的中文标题。",
        )
        or "",
        "script_prompt": _load_config_value(
            db,
            "prompt",
            "news_script_prompt",
            "请根据下面新闻内容生成适合短视频口播的中文脚本。",
        )
        or "",
        "tags_prompt": _load_config_value(
            db,
            "prompt",
            "news_tags_prompt",
            "请为下面新闻生成 3 到 5 个适合短视频传播的话题标签。",
        )
        or "",
    }


def _load_hot_threshold(db: Session) -> int:
    raw = _load_config_value(db, "parameter", "news_hot_threshold", "35") or "35"
    try:
        return int(raw)
    except ValueError:
        return 35


def _load_hot_keywords(db: Session) -> list[str]:
    return _load_keyword_list(
        db,
        "parameter",
        "news_hot_keywords",
        ["openai", "google", "anthropic", "meta", "deepseek", "huggingface", "arxiv"],
    )


def _load_block_keywords(db: Session) -> list[str]:
    return _load_keyword_list(
        db,
        "parameter",
        "news_block_keywords",
        ["赌博", "色情", "诈骗", "暴力", "违法"],
    )


def _score_hotness(db: Session, source: NewsSource, entry: ParsedNewsEntry) -> int:
    hot_keywords = _load_hot_keywords(db)
    text = f"{entry.title} {entry.content}".lower()
    score = 30
    if source.extra and isinstance(source.extra, dict):
        weight = source.extra.get("weight")
        if isinstance(weight, int):
            score += weight
    if source.category:
        score += 8
    if entry.summary:
        score += 3
    score += min(len(entry.content) // 400, 12)
    score += sum(8 for keyword in hot_keywords if keyword.lower() in text)
    return min(score, 100)


def _build_summary(entry: ParsedNewsEntry, style: str) -> str:
    source_text = entry.summary or entry.content
    if not source_text:
        return ""
    sentences = [
        sentence.strip()
        for sentence in re.split(r"[。！？!?\.]\s*", source_text)
        if sentence.strip()
    ]
    selected = sentences[:2] if sentences else [source_text[:180]]
    lead = "；".join(selected)
    style_hint = f"（{style}）" if style else ""
    return _normalize_whitespace(f"{lead}{style_hint}")


def _build_translation(text: str, label: str) -> str:
    if not text:
        return ""
    if _contains_chinese(text):
        return text
    return f"{label}：{_normalize_whitespace(text)}"


def _extract_keywords(text: str) -> list[str]:
    raw_terms = re.findall(r"[A-Za-z][A-Za-z0-9+._-]{2,}|[\u4e00-\u9fff]{2,6}", text)
    blacklist = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "news",
        "today",
        "latest",
        "about",
        "内容",
        "新闻",
        "今天",
        "最新",
    }
    keywords: list[str] = []
    for term in raw_terms:
        normalized = term.strip().strip(".,:;!?()[]{}<>\"'`")
        if not normalized:
            continue
        if normalized.lower() in blacklist or normalized in keywords:
            continue
        keywords.append(normalized)
    return keywords[:6]


def _build_tags(
    db: Session,
    source: NewsSource | None,
    entry: ParsedNewsEntry,
    category: str,
    style: str,
) -> list[str]:
    prompt_tags = _load_config_value(db, "prompt", "news_tags_prompt", "") or ""
    tags: list[str] = []
    for candidate in (category, source.name if source else None, style):
        if candidate and candidate not in tags:
            tags.append(candidate)

    for keyword in _extract_keywords(f"{entry.title} {entry.content} {prompt_tags}"):
        if keyword not in tags:
            tags.append(keyword)
        if len(tags) >= 5:
            break
    return tags[:5]


def _build_script(
    *,
    entry: ParsedNewsEntry,
    category: str,
    summary: str,
    translated_title: str,
    style: str,
    tags: list[str],
) -> str:
    style_label = style or "professional"
    lead_title = translated_title or entry.title
    tag_text = "、".join(tags[:3]) if tags else category
    return "\n".join(
        [
            f"【风格】{style_label}",
            f"【标题】{lead_title}",
            f"【标签】{tag_text}",
            "【口播】",
            f"大家好，今天带来一条{category}方向的 AI 新闻。",
            f"{summary}",
            "如果你想持续跟进 AI 领域动态，记得持续关注我们。",
        ]
    )


def _compute_dedup_hash(entry: ParsedNewsEntry) -> str:
    payload = "|".join(
        [
            _normalize_whitespace(entry.title).lower(),
            _normalize_whitespace(entry.link).lower(),
            _normalize_whitespace(entry.content[:600]).lower(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def serialize_news_source(source: NewsSource) -> dict:
    return {
        "id": source.id,
        "source_key": source.source_key,
        "name": source.name,
        "source_type": source.source_type,
        "url": source.url,
        "category": source.category,
        "language": source.language,
        "fetch_interval_minutes": source.fetch_interval_minutes,
        "is_enabled": source.is_enabled,
        "last_fetched_at": source.last_fetched_at,
        "last_success_at": source.last_success_at,
        "last_error_message": source.last_error_message,
        "extra": source.extra,
        "created_at": source.created_at,
        "updated_at": source.updated_at,
    }


def serialize_news_fetch_record(record: NewsFetchRecord, source_name: str | None = None) -> dict:
    return {
        "id": record.id,
        "source_id": record.source_id,
        "source_name": source_name,
        "task_job_id": record.task_job_id,
        "request_id": record.request_id,
        "fetch_mode": record.fetch_mode,
        "status": record.status,
        "total_count": record.total_count,
        "new_count": record.new_count,
        "duplicate_count": record.duplicate_count,
        "filtered_count": record.filtered_count,
        "error_count": record.error_count,
        "error_message": record.error_message,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "extra": record.extra,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def serialize_news(news: News, *, brief: bool = False) -> dict:
    content = news.content or ""
    translated_content = news.translated_content or ""
    script = news.script or ""
    raw_metadata = news.raw_metadata
    if brief:
        content = content[:240]
        translated_content = translated_content[:240] if translated_content else None
        script = script[:240] if script else None
        raw_metadata = None
    return {
        "id": news.id,
        "title": news.title,
        "content": content,
        "source": news.source,
        "source_id": news.source_id,
        "source_url": news.source_url,
        "url": news.url,
        "publish_time": news.publish_time,
        "status": news.status,
        "dedup_hash": news.dedup_hash,
        "category": news.category,
        "hot_score": news.hot_score,
        "language": news.language,
        "summary": news.summary,
        "translated_title": news.translated_title,
        "translated_content": translated_content,
        "script": script,
        "tags": news.tags,
        "filter_reason": news.filter_reason,
        "raw_metadata": raw_metadata,
        "created_at": news.created_at,
        "updated_at": news.updated_at,
    }


def serialize_news_detail(
    news: News,
    *,
    source_detail: dict | None = None,
    fetch_records: list[dict] | None = None,
) -> dict:
    payload = serialize_news(news, brief=False)
    payload["source_detail"] = source_detail
    payload["fetch_records"] = fetch_records or []
    return payload


def list_news_sources(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    source_type: NewsSourceType | None = None,
    is_enabled: bool | None = None,
) -> tuple[list[NewsSource], int]:
    filters = []
    if keyword:
        like = f"%{keyword.strip()}%"
        filters.append(
            or_(
                NewsSource.source_key.ilike(like),
                NewsSource.name.ilike(like),
                NewsSource.url.ilike(like),
                NewsSource.category.ilike(like),
            )
        )
    if source_type is not None:
        filters.append(NewsSource.source_type == source_type.value)
    if is_enabled is not None:
        filters.append(NewsSource.is_enabled.is_(is_enabled))

    total = db.scalar(select(func.count()).select_from(NewsSource).where(*filters)) or 0
    items = db.scalars(
        select(NewsSource)
        .where(*filters)
        .order_by(NewsSource.is_enabled.desc(), NewsSource.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def get_news_source(db: Session, source_id: int) -> NewsSource:
    source = db.get(NewsSource, source_id)
    if source is None:
        raise NotFoundException(message="新闻源不存在")
    return source


def create_news_source(db: Session, payload: NewsSourceCreate) -> NewsSource:
    source_key = payload.source_key.strip().lower()
    existing = db.scalar(
        select(NewsSource).where(
            or_(
                NewsSource.source_key == source_key,
                NewsSource.url == payload.url.strip(),
            )
        )
    )
    if existing:
        raise ConflictException(message="新闻源标识或地址已存在")
    source = NewsSource(
        source_key=source_key,
        name=payload.name.strip(),
        source_type=payload.source_type.value,
        url=payload.url.strip(),
        category=payload.category,
        language=(payload.language or "en").strip(),
        fetch_interval_minutes=payload.fetch_interval_minutes,
        is_enabled=payload.is_enabled,
        extra=payload.extra,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def update_news_source(db: Session, source_id: int, payload: NewsSourceUpdate) -> NewsSource:
    source = get_news_source(db, source_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "source_type" in update_data and update_data["source_type"] is not None:
        update_data["source_type"] = update_data["source_type"].value
    if "url" in update_data and update_data["url"] is not None:
        update_url = update_data["url"].strip()
        conflict = db.scalar(
            select(NewsSource).where(
                NewsSource.id != source.id,
                NewsSource.url == update_url,
            )
        )
        if conflict:
            raise ConflictException(message="新闻源地址已存在")
        update_data["url"] = update_url

    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].strip()
    if "category" in update_data and update_data["category"] is not None:
        update_data["category"] = update_data["category"].strip()
    if "language" in update_data and update_data["language"] is not None:
        update_data["language"] = update_data["language"].strip()

    for field, value in update_data.items():
        setattr(source, field, value)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _build_query_filters(
    *,
    keyword: str | None,
    status: NewsStatus | None,
    source_id: int | None,
    category: str | None,
) -> list:
    filters = []
    if keyword:
        like = f"%{keyword.strip()}%"
        filters.append(
            or_(
                News.title.ilike(like),
                News.source.ilike(like),
                News.category.ilike(like),
                News.summary.ilike(like),
                News.script.ilike(like),
            )
        )
    if status is not None:
        filters.append(News.status == status.value)
    if source_id is not None:
        filters.append(News.source_id == source_id)
    if category:
        filters.append(News.category == category.strip())
    return filters


def list_news(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    status: NewsStatus | None = None,
    source_id: int | None = None,
    category: str | None = None,
) -> tuple[list[News], int]:
    filters = _build_query_filters(
        keyword=keyword,
        status=status,
        source_id=source_id,
        category=category,
    )
    total = db.scalar(select(func.count()).select_from(News).where(*filters)) or 0
    items = db.scalars(
        select(News)
        .where(*filters)
        .order_by(News.publish_time.desc(), News.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return list(items), total


def get_news(db: Session, news_id: int) -> News:
    news = db.get(News, news_id)
    if news is None:
        raise NotFoundException(message="新闻不存在")
    return news


def list_news_fetch_records(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    source_id: int | None = None,
    status: str | None = None,
) -> tuple[list[tuple[NewsFetchRecord, str | None]], int]:
    filters = []
    if source_id is not None:
        filters.append(NewsFetchRecord.source_id == source_id)
    if status:
        filters.append(NewsFetchRecord.status == status)

    total = db.scalar(select(func.count()).select_from(NewsFetchRecord).where(*filters)) or 0
    records = db.scalars(
        select(NewsFetchRecord)
        .where(*filters)
        .order_by(NewsFetchRecord.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    source_names = {
        source.id: source.name
        for source in db.scalars(
            select(NewsSource).where(NewsSource.id.in_([record.source_id for record in records]))
        ).all()
    }
    return [(record, source_names.get(record.source_id)) for record in records], total


def get_news_detail(db: Session, news_id: int) -> dict:
    news = get_news(db, news_id)
    source_detail = None
    fetch_records: list[dict] = []
    if news.source_id is not None:
        source = db.get(NewsSource, news.source_id)
        if source is not None:
            source_detail = serialize_news_source(source)
            records, _ = list_news_fetch_records(db, page=1, page_size=5, source_id=source.id)
            fetch_records = [serialize_news_fetch_record(record, source_name=source_name) for record, source_name in records]
    return serialize_news_detail(
        news,
        source_detail=source_detail,
        fetch_records=fetch_records,
    )


def _record_fetch_error(record: NewsFetchRecord, error_message: str) -> None:
    record.status = TaskStatus.FAILED.value
    record.error_message = error_message
    record.finished_at = _now()


def sync_news_source(
    *,
    db: Session,
    source_id: int,
    fetch_mode: NewsFetchMode = NewsFetchMode.MANUAL,
    task_job_id: int | None = None,
    request_id: str | None = None,
    triggered_by: int | None = None,
) -> dict:
    source = get_news_source(db, source_id)
    if source.source_type not in {NewsSourceType.RSS.value, NewsSourceType.ATOM.value}:
        raise ValidationException(message="当前仅支持 RSS 或 Atom 新闻源")

    now = _now()
    source.last_fetched_at = now
    source.last_error_message = None
    db.add(source)

    record = NewsFetchRecord(
        source_id=source.id,
        task_job_id=task_job_id,
        request_id=request_id,
        fetch_mode=fetch_mode.value,
        status=TaskStatus.RUNNING.value,
        started_at=now,
        extra={
            "triggered_by": triggered_by,
            "source_key": source.source_key,
            "source_url": source.url,
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    existing_rows = db.execute(
        select(News.url, News.dedup_hash).where(
            or_(
                News.source_id == source.id,
                News.source == source.name,
            )
        )
    ).all()
    existing_urls = {row[0] for row in existing_rows if row[0]}
    existing_hashes = {row[1] for row in existing_rows if row[1]}

    try:
        raw_text = _fetch_remote_text(source.url)
        entries = _parse_feed_entries(source, raw_text)
    except (ET.ParseError, URLError, TimeoutError, OSError, ValueError) as exc:
        logger.exception("failed to fetch news source %s", source.id)
        source.last_error_message = str(exc)
        record.error_count = 1
        _record_fetch_error(record, str(exc))
        db.add_all([source, record])
        db.commit()
        return {
            "source": serialize_news_source(source),
            "fetch_record": serialize_news_fetch_record(record, source_name=source.name),
            "items": [],
            "total_count": 0,
            "new_count": 0,
            "duplicate_count": 0,
            "filtered_count": 0,
        }

    block_keywords = _load_block_keywords(db)
    hot_threshold = _load_hot_threshold(db)
    prompt_bundle = _load_prompt_bundle(db)

    created_items: list[News] = []
    duplicate_count = 0
    filtered_count = 0
    rejected_count = 0

    for entry in entries:
        dedup_hash = _compute_dedup_hash(entry)
        if entry.link in existing_urls or dedup_hash in existing_hashes:
            duplicate_count += 1
            continue

        category = _infer_category(source, entry)
        language = _infer_language(source, entry)
        hot_score = _score_hotness(db, source, entry)
        rejection_reason = _is_sensitive(entry, block_keywords)
        if rejection_reason is None and hot_score < hot_threshold:
            rejection_reason = f"热度不足，当前评分 {hot_score}，阈值 {hot_threshold}"

        news = News(
            title=entry.title,
            content=entry.content,
            source=source.name,
            source_id=source.id,
            source_url=source.url,
            url=entry.link,
            publish_time=entry.published_at,
            status=NewsStatus.NEW.value,
            dedup_hash=dedup_hash,
            category=category,
            hot_score=hot_score,
            language=language,
            raw_metadata={
                **entry.raw,
                "author": entry.author,
                "guid": entry.guid,
                "source_key": source.source_key,
                "source_type": source.source_type,
                "source_name": source.name,
                "fetch_mode": fetch_mode.value,
                "prompt_bundle": prompt_bundle,
            },
        )
        db.add(news)
        db.flush()

        news.status = NewsStatus.DEDUPED.value
        if rejection_reason:
            news.status = NewsStatus.REJECTED.value
            news.filter_reason = rejection_reason
            rejected_count += 1
        else:
            news.status = NewsStatus.FILTERED.value
            summary = _build_summary(entry, "专业快讯")
            news.summary = summary
            news.translated_title = _build_translation(entry.title, "中文标题")
            news.translated_content = _build_translation(entry.content, "中文内容")
            news.tags = _build_tags(db, source, entry, category, "professional")
            news.script = _build_script(
                entry=entry,
                category=category,
                summary=summary,
                translated_title=news.translated_title or "",
                style="professional",
                tags=news.tags or [],
            )
            filtered_count += 1
        db.add(news)
        created_items.append(news)
        existing_urls.add(entry.link)
        existing_hashes.add(dedup_hash)

    record.status = TaskStatus.SUCCESS.value
    record.total_count = len(entries)
    record.new_count = len(created_items)
    record.duplicate_count = duplicate_count
    record.filtered_count = filtered_count
    record.error_count = 0
    record.finished_at = _now()
    record.extra = {
        **(record.extra or {}),
        "rejected_count": rejected_count,
        "accepted_count": filtered_count,
        "generated_by": "rule-based-pipeline",
    }
    source.last_success_at = _now()
    source.last_error_message = None
    db.add_all([source, record])
    db.commit()

    return {
        "source": serialize_news_source(source),
        "fetch_record": serialize_news_fetch_record(record, source_name=source.name),
        "items": [serialize_news(news, brief=True) for news in created_items],
        "total_count": len(entries),
        "new_count": len(created_items),
        "duplicate_count": duplicate_count,
        "filtered_count": filtered_count,
        "rejected_count": rejected_count,
    }


def _generate_news_fields(
    *,
    db: Session,
    news: News,
    style: str,
) -> dict[str, object]:
    prompt_bundle = _load_prompt_bundle(db)
    summary = _build_summary(
        ParsedNewsEntry(
            title=news.title,
            link=news.url,
            content=news.content or news.title,
            published_at=news.publish_time,
            summary=news.summary,
            author=None,
            guid=None,
            raw=news.raw_metadata or {},
        ),
        style,
    )
    translated_title = _build_translation(news.title, "中文标题")
    translated_content = _build_translation(news.content or news.title, "中文内容")
    category = news.category or "行业动态"
    source = db.get(NewsSource, news.source_id) if news.source_id else None
    entry = ParsedNewsEntry(
        title=news.title,
        link=news.url,
        content=news.content or news.title,
        published_at=news.publish_time,
        summary=news.summary,
        author=None,
        guid=None,
        raw=news.raw_metadata or {},
    )
    tags = _build_tags(db, source, entry, category, style)
    script = _build_script(
        entry=entry,
        category=category,
        summary=summary or news.summary or "",
        translated_title=translated_title or news.translated_title or news.title,
        style=style,
        tags=tags,
    )
    return {
        "summary": summary or news.summary or "",
        "translated_title": translated_title or news.translated_title or news.title,
        "translated_content": translated_content or news.translated_content or news.content or news.title,
        "script": script,
        "tags": tags,
        "prompt_bundle": prompt_bundle,
    }


def generate_news_content(
    *,
    db: Session,
    news_id: int,
    payload: NewsGenerateRequest,
    task_job_id: int | None = None,
    request_id: str | None = None,
    triggered_by: int | None = None,
) -> dict:
    news = get_news(db, news_id)
    if news.status == NewsStatus.REJECTED.value and not payload.regenerate:
        raise ValidationException(message="已拒绝的新闻不能直接生成内容")

    generated = _generate_news_fields(db=db, news=news, style=payload.style)
    news.summary = generated["summary"]  # type: ignore[assignment]
    news.translated_title = generated["translated_title"]  # type: ignore[assignment]
    news.translated_content = generated["translated_content"]  # type: ignore[assignment]
    news.script = generated["script"]  # type: ignore[assignment]
    news.tags = list(generated["tags"])  # type: ignore[assignment]
    news.status = NewsStatus.SCRIPT_READY.value
    news.raw_metadata = {
        **(news.raw_metadata or {}),
        "generation": {
            "style": payload.style,
            "regenerate": payload.regenerate,
            "request_id": request_id,
            "task_job_id": task_job_id,
            "triggered_by": triggered_by,
            "generated_at": _now().isoformat(),
            "prompt_bundle": generated["prompt_bundle"],
            "pipeline": "rule-based-fallback",
        },
    }
    db.add(news)
    db.commit()
    db.refresh(news)
    return {
        "news": get_news_detail(db, news.id),
        "style": payload.style,
        "regenerate": payload.regenerate,
    }


def list_due_news_sources(db: Session, *, now: datetime | None = None) -> list[NewsSource]:
    current_time = now or _now()
    sources = db.scalars(
        select(NewsSource).where(
            NewsSource.is_enabled.is_(True),
            NewsSource.source_type.in_([NewsSourceType.RSS.value, NewsSourceType.ATOM.value]),
        )
    ).all()
    due_sources: list[NewsSource] = []
    for source in sources:
        if source.last_fetched_at is None:
            due_sources.append(source)
            continue
        interval = timedelta(minutes=max(source.fetch_interval_minutes, 5))
        if current_time - source.last_fetched_at >= interval:
            due_sources.append(source)
    return due_sources
