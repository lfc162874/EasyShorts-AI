from __future__ import annotations

import json
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request as URLRequest
from urllib.request import urlopen

from app.core.constants import NewsSourceType
from app.core.exceptions import ValidationException
from app.core.logging import get_logger
from app.db.models.business import NewsSource

logger = get_logger(__name__)


@dataclass(slots=True)
class CollectedNewsEntry:
    title: str
    link: str
    content: str
    published_at: datetime | None
    summary: str | None
    author: str | None
    guid: str | None
    raw: dict[str, object]


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


def _parse_datetime(value: str | int | float | None) -> datetime | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=UTC)
        except (OverflowError, OSError, ValueError):
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


def _request_headers(url: str, *, accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8") -> dict[str, str]:
    parsed = urlparse(url)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": accept,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
    }
    if parsed.netloc.endswith("zhihu.com"):
        headers.update(
            {
                "Referer": "https://www.zhihu.com/",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
    return headers


def _merge_request_headers(
    base_headers: dict[str, str],
    extra_headers: dict[str, object] | None,
) -> dict[str, str]:
    merged = dict(base_headers)
    if not isinstance(extra_headers, dict):
        return merged
    for key, value in extra_headers.items():
        header_name = str(key).strip()
        header_value = str(value).strip() if value is not None else ""
        if not header_name or not header_value:
            continue
        merged[header_name] = header_value
    return merged


def _resolve_source_headers(
    source: NewsSource | None,
    url: str,
    *,
    accept: str,
) -> dict[str, str]:
    headers = _request_headers(url, accept=accept)
    source_extra = source.extra if source and isinstance(source.extra, dict) else {}
    headers = _merge_request_headers(headers, source_extra.get("request_headers"))

    cookie_value = source_extra.get("cookie") or source_extra.get("cookies")
    if cookie_value:
        headers["Cookie"] = str(cookie_value).strip()
    return headers


def _fetch_remote_text(
    url: str,
    *,
    accept: str = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    source: NewsSource | None = None,
) -> str:
    request = URLRequest(url, headers=_resolve_source_headers(source, url, accept=accept))
    try:
        with urlopen(request, timeout=20) as response:  # nosec - controlled project input
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
        return raw.decode(encoding, errors="ignore")
    except HTTPError as exc:
        if exc.code in {403, 429} and "zhihu.com" in urlparse(url).netloc:
            logger.warning("Zhihu fetch blocked for %s: %s", url, exc)
        raise


def _extract_zhihu_article_id(article_url: str) -> str | None:
    parsed = urlparse(article_url)
    match = re.search(r"/p/(\d+)", parsed.path)
    if match:
        return match.group(1)
    return None


def _looks_like_zhihu_risk_payload(payload: dict[str, object]) -> bool:
    error_payload = payload.get("error")
    if not isinstance(error_payload, dict):
        return False
    code = str(error_payload.get("code") or "")
    message = str(error_payload.get("message") or "")
    return code in {"10003", "40362"} or "限制本次访问" in message or "升级客户端后重试" in message


def _extract_zhihu_article_entry(source: NewsSource, article_url: str, payload: dict[str, object]) -> CollectedNewsEntry:
    title = str(payload.get("title") or source.name)
    summary = str(
        payload.get("excerpt")
        or payload.get("excerpt_new")
        or payload.get("excerpt_text")
        or payload.get("summary")
        or ""
    )
    content_html = str(payload.get("content") or "")
    content = _strip_html(content_html) or summary or title
    created_value = payload.get("created") or payload.get("updated") or payload.get("published_time")
    author = ""
    author_payload = payload.get("author")
    if isinstance(author_payload, dict):
        author = str(author_payload.get("name") or author_payload.get("url_token") or "")
    elif author_payload is not None:
        author = str(author_payload)
    raw = {
        "title": title,
        "link": article_url,
        "content": content,
        "summary": summary,
        "published": created_value or "",
        "author": author,
        "guid": article_url,
        "api_url": f"https://www.zhihu.com/api/v4/articles/{_extract_zhihu_article_id(article_url)}",
        "api_payload": payload,
    }
    return CollectedNewsEntry(
        title=_normalize_whitespace(title),
        link=_normalize_whitespace(article_url),
        content=_strip_html(content),
        published_at=_parse_datetime(created_value if isinstance(created_value, (str, int, float)) else None),
        summary=_strip_html(summary),
        author=_normalize_whitespace(author),
        guid=_normalize_whitespace(article_url),
        raw=raw,
    )


def _extract_article_entry_by_url(source: NewsSource, article_url: str) -> CollectedNewsEntry:
    parsed = urlparse(article_url)
    if parsed.netloc.endswith("zhihu.com"):
        article_id = _extract_zhihu_article_id(article_url)
        if article_id:
            api_url = f"https://www.zhihu.com/api/v4/articles/{article_id}"
            try:
                raw_text = _fetch_remote_text(
                    api_url,
                    accept="application/json, text/plain, */*",
                    source=source,
                )
                payload = json.loads(raw_text)
                if isinstance(payload, dict):
                    if _looks_like_zhihu_risk_payload(payload):
                        raise ValidationException(
                            message=(
                                "知乎当前返回风控响应，匿名请求无法继续采集。"
                                "请在该来源 extra 中配置 cookie 或 request_headers 后重试。"
                            )
                        )
                    return _extract_zhihu_article_entry(source, article_url, payload)
            except ValidationException:
                raise
            except Exception as exc:  # pragma: no cover - fallback for Zhihu anti-bot changes
                logger.warning("Failed to fetch Zhihu article API for %s: %s", article_url, exc)
    raw_text = _fetch_remote_text(article_url, source=source)
    return _extract_article_entry(source, article_url, raw_text)


def _parse_feed_entries(source: NewsSource, raw_text: str) -> list[CollectedNewsEntry]:
    root = ET.fromstring(raw_text)
    tag = _local_name(root.tag).lower()
    if tag in {"rss", "rdf"}:
        items = root.findall(".//item")
    elif tag == "feed":
        items = root.findall(".//{*}entry")
    else:
        items = root.findall(".//item") or root.findall(".//{*}entry")

    entries: list[CollectedNewsEntry] = []
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
            CollectedNewsEntry(
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


class _ArticleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.links: list[tuple[str, str]] = []
        self.body_parts: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self._body_depth = 0
        self._current_anchor_href: str | None = None
        self._current_anchor_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value for key, value in attrs if value is not None}
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if normalized_tag == "title":
            self._in_title = True
        elif normalized_tag == "meta":
            key = attr_map.get("property") or attr_map.get("name")
            content = attr_map.get("content")
            if key and content:
                self.meta[key.lower()] = _normalize_whitespace(content)
        elif normalized_tag == "a":
            href = attr_map.get("href")
            if href:
                self._current_anchor_href = href.strip()
                self._current_anchor_text = []
        elif normalized_tag in {"article", "main", "section", "p", "li", "h1", "h2", "h3", "h4", "blockquote"}:
            self._body_depth += 1

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"}:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if normalized_tag == "title":
            self._in_title = False
        elif normalized_tag == "a" and self._current_anchor_href:
            text = _normalize_whitespace(" ".join(self._current_anchor_text))
            self.links.append((self._current_anchor_href, text))
            self._current_anchor_href = None
            self._current_anchor_text = []
        elif normalized_tag in {"article", "main", "section", "p", "li", "h1", "h2", "h3", "h4", "blockquote"}:
            if self._body_depth:
                self._body_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_title:
            self.title_parts.append(data)
        if self._current_anchor_href:
            self._current_anchor_text.append(data)
        if self._body_depth > 0:
            self.body_parts.append(data)


def _parse_html_page(raw_text: str) -> _ArticleHTMLParser:
    parser = _ArticleHTMLParser()
    parser.feed(raw_text)
    parser.close()
    return parser


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _looks_like_article_url(
    candidate_url: str,
    source_url: str,
    anchor_text: str,
    *,
    extra: dict[str, object] | None = None,
) -> bool:
    parsed_candidate = urlparse(candidate_url)
    parsed_source = urlparse(source_url)
    if parsed_candidate.scheme not in {"http", "https"}:
        return False
    if parsed_candidate.netloc and parsed_source.netloc and parsed_candidate.netloc != parsed_source.netloc:
        return False
    if candidate_url.rstrip("/") == source_url.rstrip("/"):
        return False

    include_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in _as_string_list((extra or {}).get("link_patterns"))]
    if include_patterns and not any(pattern.search(candidate_url) or pattern.search(anchor_text) for pattern in include_patterns):
        return False

    exclude_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in _as_string_list((extra or {}).get("exclude_link_patterns"))]
    if any(pattern.search(candidate_url) or pattern.search(anchor_text) for pattern in exclude_patterns):
        return False

    path = parsed_candidate.path.lower()
    article_markers = (
        "article",
        "articles",
        "blog",
        "news",
        "post",
        "posts",
        "story",
        "stories",
        "research",
        "paper",
        "release",
        "update",
    )
    if any(marker in path for marker in article_markers):
        return True
    if parsed_candidate.query and any(marker in parsed_candidate.query.lower() for marker in ("id=", "p=", "post=", "article=")):
        return True
    if anchor_text and len(anchor_text.split()) >= 3:
        return True
    return False


def _extract_article_entry(source: NewsSource, article_url: str, raw_text: str) -> CollectedNewsEntry:
    page = _parse_html_page(raw_text)
    meta = {key.lower(): value for key, value in page.meta.items()}
    title = (
        meta.get("og:title")
        or meta.get("twitter:title")
        or meta.get("title")
        or _normalize_whitespace("".join(page.title_parts))
        or source.name
    )
    summary = meta.get("description") or meta.get("og:description") or meta.get("twitter:description")
    published_text = (
        meta.get("article:published_time")
        or meta.get("article:modified_time")
        or meta.get("pubdate")
        or meta.get("date")
        or meta.get("datepublished")
    )
    author = meta.get("article:author") or meta.get("author") or meta.get("dc.creator") or meta.get("byl")
    body_text = _normalize_whitespace(" ".join(page.body_parts))
    content = body_text or summary or title
    raw = {
        "title": title,
        "link": article_url,
        "content": content,
        "summary": summary or "",
        "published": published_text or "",
        "author": author or "",
        "guid": article_url,
        "meta": meta,
        "links": page.links[:20],
    }
    return CollectedNewsEntry(
        title=_normalize_whitespace(title),
        link=_normalize_whitespace(article_url),
        content=_strip_html(content),
        published_at=_parse_datetime(published_text),
        summary=_strip_html(summary),
        author=_normalize_whitespace(author),
        guid=_normalize_whitespace(article_url),
        raw=raw,
    )


def _collect_rss_entries(source: NewsSource) -> list[CollectedNewsEntry]:
    raw_text = _fetch_remote_text(source.url, source=source)
    return _parse_feed_entries(source, raw_text)


def _collect_web_entries(source: NewsSource) -> list[CollectedNewsEntry]:
    source_extra = source.extra if isinstance(source.extra, dict) else {}
    explicit_urls = _as_string_list(source_extra.get("article_urls"))
    explicit_urls += _as_string_list(source_extra.get("urls"))
    explicit_urls = [urljoin(source.url, item) for item in explicit_urls]

    mode = str(source_extra.get("mode") or "list").lower()
    max_items_raw = source_extra.get("max_items")
    max_items = 10
    if isinstance(max_items_raw, int) and max_items_raw > 0:
        max_items = min(max_items_raw, 50)

    candidate_urls: list[str] = []
    if explicit_urls:
        candidate_urls.extend(explicit_urls)
    else:
        raw_text = _fetch_remote_text(source.url, source=source)
        source_page = _parse_html_page(raw_text)
        for href, anchor_text in source_page.links:
            candidate = urljoin(source.url, href)
            if _looks_like_article_url(candidate, source.url, anchor_text, extra=source_extra):
                candidate_urls.append(candidate)

    deduped_urls: list[str] = []
    seen: set[str] = set()
    for candidate in candidate_urls:
        normalized = candidate.strip()
        if not normalized or normalized in seen:
            continue
        deduped_urls.append(normalized)
        seen.add(normalized)

    if mode == "single" and not deduped_urls:
        deduped_urls = [source.url]
    elif not deduped_urls:
        deduped_urls = [source.url]

    entries: list[CollectedNewsEntry] = []
    for article_url in deduped_urls[:max_items]:
        entries.append(_extract_article_entry_by_url(source, article_url))
    return entries


def _collect_manual_entries(source: NewsSource) -> list[CollectedNewsEntry]:
    source_extra = source.extra if isinstance(source.extra, dict) else {}
    raw_items = source_extra.get("items") or source_extra.get("entries") or []
    if not isinstance(raw_items, list):
        return []

    entries: list[CollectedNewsEntry] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            continue
        title = _normalize_whitespace(str(item.get("title") or item.get("name") or source.name))
        link = _normalize_whitespace(str(item.get("link") or item.get("url") or f"{source.url}#manual-{index + 1}"))
        content = _strip_html(
            str(
                item.get("content")
                or item.get("description")
                or item.get("summary")
                or title
            )
        )
        summary = _strip_html(str(item.get("summary") or item.get("description") or ""))
        published_at = _parse_datetime(
            str(
                item.get("published_at")
                or item.get("published_time")
                or item.get("pubDate")
                or item.get("date")
                or ""
            )
        )
        author = _normalize_whitespace(str(item.get("author") or item.get("creator") or ""))
        guid = _normalize_whitespace(str(item.get("guid") or item.get("id") or link))
        raw = {
            **item,
            "source_key": source.source_key,
            "source_name": source.name,
            "source_type": source.source_type,
        }
        entries.append(
            CollectedNewsEntry(
                title=title or source.name,
                link=link or source.url,
                content=content or title or source.name,
                published_at=published_at,
                summary=summary or None,
                author=author or None,
                guid=guid or None,
                raw=raw,
            )
        )
    return entries


def collect_source_entries(source: NewsSource) -> list[CollectedNewsEntry]:
    source_type = (source.source_type or "").upper()
    if source_type in {NewsSourceType.RSS.value, NewsSourceType.ATOM.value}:
        return _collect_rss_entries(source)
    if source_type == NewsSourceType.WEB.value:
        return _collect_web_entries(source)
    if source_type == NewsSourceType.MANUAL.value:
        return _collect_manual_entries(source)
    raise ValidationException(message=f"当前不支持该来源类型：{source.source_type}")
