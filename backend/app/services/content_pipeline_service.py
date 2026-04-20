from __future__ import annotations

import difflib
import hashlib
import html
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.agents.agentscope_runtime import can_use_agentscope, run_structured_agent_sync
from app.agents.runtime import build_agent_runtime
from app.agents.structured_models import ContentProcessingStructuredOutput
from app.core.constants import NewsFetchMode, NewsSourceType, NewsStatus, TaskStatus
from app.core.exceptions import ValidationException
from app.core.logging import get_logger
from app.db.models.business import News, NewsSource
from app.db.models.system import SystemConfig
from app.services.collector_service import CollectedNewsEntry

logger = get_logger(__name__)

NOISE_PATTERNS = [
    r"登录社区云.*?加入社区",
    r"登录社区云.*?欢迎回来",
    r"邀请您加入社区",
    r"登录.*?CSDN账号登录",
    r"欢迎回来",
    r"关注我们",
    r"订阅我们",
    r"点击查看原文",
    r"阅读全文",
    r"相关阅读",
    r"更多内容",
    r"请访问原文",
    r"更多内容请访问原文",
    r"免责声明",
    r"广告",
    r"扫一扫",
    r"打开客户端",
    r"下载客户端",
    r"评论.*",
    r"分享.*",
]

NOISE_LINE_MARKERS = (
    "登录社区云",
    "欢迎回来",
    "请访问原文",
    "更多内容",
    "相关阅读",
    "点击查看原文",
    "阅读全文",
    "打开客户端",
    "下载客户端",
    "关注我们",
    "订阅我们",
    "免责声明",
    "评论",
    "分享",
)

TRANSLATION_MAP: list[tuple[str, str]] = [
    ("open source", "开源"),
    ("opensource", "开源"),
    ("modelscope", "ModelScope"),
    ("reasoning model", "推理模型"),
    ("reasoning", "推理"),
    ("tool use", "工具调用"),
    ("tooling", "工具链"),
    ("agent", "智能体"),
    ("agents", "智能体"),
    ("model", "模型"),
    ("released", "发布"),
    ("releases", "发布"),
    ("released a", "发布了"),
    ("launches", "发布"),
    ("launched", "发布"),
    ("ships", "发布"),
    ("shipped", "发布"),
    ("release", "发布"),
    ("launch", "发布"),
    ("ship", "发布"),
    ("update", "更新"),
    ("funding", "融资"),
    ("investment", "投资"),
    ("round", "轮融资"),
    ("policy", "政策"),
    ("regulation", "监管"),
    ("research", "研究"),
    ("paper", "论文"),
    ("benchmark", "基准"),
    ("training", "训练"),
    ("fine-tuning", "微调"),
    ("multimodal", "多模态"),
    ("community", "社区"),
    ("product", "产品"),
    ("feature", "功能"),
    ("generation", "生成"),
    ("inference", "推理"),
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic"),
    ("huggingface", "HuggingFace"),
    ("deepseek", "DeepSeek"),
]


@dataclass(slots=True)
class ContentAnalysis:
    cleaned_title: str
    cleaned_content: str
    category: str
    language: str
    hot_score: int
    summary: str
    translated_title: str
    translated_content: str
    tags: list[str]
    script: str
    filter_reason: str | None
    dedup_hash: str
    title_signature: str
    content_signature: str
    raw_metadata: dict[str, object]


@dataclass(slots=True)
class ContentProcessOutcome:
    news: News
    created: bool
    merged: bool
    duplicate: bool
    promoted_from_rejected: bool
    analysis: ContentAnalysis


def _now() -> datetime:
    return datetime.now(UTC)


def _build_content_processing_system_prompt(prompt_bundle: dict[str, str]) -> str:
    prompt_parts = [
        "你是 EasyShorts AI 的内容处理助手，负责把清洗后的 AI 新闻整理成更适合分析和推送的结构化内容。",
        "要求：只输出 JSON，不要输出解释、前言或 Markdown。",
        "要求：必须严格基于原文，不要编造原文中没有的事实。",
        "要求：标题要简洁准确，摘要要自然、信息密度高，标签要贴合内容。",
        "要求：翻译内容只需要自然中文改写，不需要逐字直译。",
        prompt_bundle.get("news_title_prompt", ""),
        prompt_bundle.get("news_summary_prompt", ""),
        prompt_bundle.get("news_script_prompt", ""),
        prompt_bundle.get("news_tags_prompt", ""),
    ]
    return "\n".join(part for part in prompt_parts if part).strip()


def _build_content_processing_user_prompt(
    *,
    title: str,
    source_name: str | None,
    source_type: str | None,
    category: str,
    language: str,
    hot_score: int,
    summary: str,
    content: str,
    style: str,
) -> str:
    return "\n".join(
        [
            "请根据下面这条 AI 新闻输出结构化处理结果，只输出 JSON。",
            "字段要求：title, summary, highlights, translated_title, translated_content, tags, script。",
            "其中 highlights 至少 3 条，tags 3 到 5 个，script 适合口播。",
            f"写作风格：{style or 'professional'}",
            f"标题：{title}",
            f"来源：{source_name or '未知'}",
            f"来源类型：{source_type or '未知'}",
            f"分类：{category}",
            f"语言：{language}",
            f"热度分值：{hot_score}",
            f"原始摘要：{summary or '无'}",
            "正文：",
            content or "",
        ]
    )


def _normalize_tag_candidates(values: object, limit: int = 5) -> list[str]:
    if not isinstance(values, list):
        return []
    tags: list[str] = []
    for value in values:
        tag = _normalize_whitespace(str(value))
        if not tag or tag in tags:
            continue
        tags.append(tag)
        if len(tags) >= limit:
            break
    return tags


def _merge_tag_lists(primary: list[str], secondary: list[str], limit: int = 5) -> list[str]:
    merged: list[str] = []
    for candidate in [*primary, *secondary]:
        tag = _normalize_whitespace(candidate)
        if not tag or tag in merged:
            continue
        merged.append(tag)
        if len(merged) >= limit:
            break
    return merged


def _refine_content_with_agent(
    db: Session,
    *,
    title: str,
    source_name: str | None,
    source_type: str | None,
    category: str,
    language: str,
    hot_score: int,
    summary: str,
    content: str,
    style: str,
) -> dict[str, object] | None:
    runtime = build_agent_runtime(db)
    if not can_use_agentscope(runtime):
        return None

    prompt_bundle = _load_prompt_bundle(db)
    system_prompt = _build_content_processing_system_prompt(prompt_bundle)
    if not system_prompt:
        return None

    user_prompt = _build_content_processing_user_prompt(
        title=title,
        source_name=source_name,
        source_type=source_type,
        category=category,
        language=language,
        hot_score=hot_score,
        summary=summary,
        content=content,
        style=style,
    )
    agent_result = run_structured_agent_sync(
        runtime=runtime,
        agent_name="ContentProcessingAgent",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        structured_model=ContentProcessingStructuredOutput,
    )
    if agent_result is None:
        return None

    return {
        "title": _normalize_whitespace(str(agent_result.get("title") or "")),
        "summary": _normalize_whitespace(str(agent_result.get("summary") or "")),
        "highlights": _normalize_tag_candidates(agent_result.get("highlights"), limit=5),
        "translated_title": _normalize_whitespace(str(agent_result.get("translated_title") or "")),
        "translated_content": _normalize_whitespace(str(agent_result.get("translated_content") or "")),
        "tags": _normalize_tag_candidates(agent_result.get("tags"), limit=5),
        "script": _normalize_whitespace(str(agent_result.get("script") or "")),
        "model_name": runtime.model_name,
        "prompt_version": runtime.prompt_version,
    }


def refine_content_with_agent(
    db: Session,
    *,
    title: str,
    source_name: str | None,
    source_type: str | None,
    category: str,
    language: str,
    hot_score: int,
    summary: str,
    content: str,
    style: str,
) -> dict[str, object] | None:
    return _refine_content_with_agent(
        db,
        title=title,
        source_name=source_name,
        source_type=source_type,
        category=category,
        language=language,
        hot_score=hot_score,
        summary=summary,
        content=content,
        style=style,
    )


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


def _clean_boilerplate(text: str) -> str:
    cleaned = text
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"\bwww\.\S+", " ", cleaned)
    lines: list[str] = []
    for raw_line in re.split(r"[\r\n]+", cleaned):
        line = _normalize_whitespace(raw_line)
        if not line:
            continue
        compact = re.sub(r"\s+", "", line).lower()
        if any(marker.lower() in compact for marker in NOISE_LINE_MARKERS):
            continue
        if re.fullmatch(r"[：:，,。！？!?]+", compact):
            continue
        lines.append(line)
    cleaned = " ".join(lines) if lines else _normalize_whitespace(cleaned)
    cleaned = re.sub(r"\s*[：:]\s*", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip()
    cleaned = re.sub(r"^[。！？!?，,：:\s]+", "", cleaned)
    cleaned = re.sub(r"[。！？!?，,：:\s]+$", "", cleaned)
    return cleaned.strip()


def _clean_content_text(text: str | None) -> str:
    if not text:
        return ""
    cleaned = _strip_html(text)
    cleaned = _clean_boilerplate(cleaned)
    cleaned = re.sub(r"\s*([。！？!?])\s*", r"\1", cleaned)
    cleaned = re.sub(r"\s*([,，;；])\s*", r"\1", cleaned)
    return _normalize_whitespace(cleaned)


def _normalize_signature(value: str | None) -> str:
    if not value:
        return ""
    text = _normalize_whitespace(value).lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text


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
        "一个",
        "我们",
        "他们",
    }
    keywords: list[str] = []
    for term in raw_terms:
        normalized = term.strip().strip(".,:;!?()[]{}<>\"'`")
        if not normalized:
            continue
        if normalized.lower() in blacklist or normalized in keywords:
            continue
        keywords.append(normalized)
    return keywords[:8]


def _infer_category(source: NewsSource | None, title: str, content: str) -> str:
    text = f"{title} {content}".lower()

    category_rules: list[tuple[str, Iterable[str]]] = [
        ("融资", ("funding", "investment", "series a", "series b", "seed round", "融资", "投资", "天使轮", "A轮", "B轮")),
        ("开源生态", ("open source", "open-source", "opensource", "开源", "gitub", "github", "hugging face", "huggingface", "modelscope")),
        ("模型发布", ("model", "weights", "checkpoint", "reasoning", "benchmark", "推理", "大模型", "模型", "参数", "开源权重")),
        ("产品更新", ("launch", "release", "update", "ship", "发布", "更新", "上线", "功能", "feature")),
        ("研究论文", ("paper", "arxiv", "research", "论文", "研究", "实验")),
        ("政策监管", ("policy", "regulation", "law", "监管", "政策", "法案", "合规")),
        ("社区动态", ("community", "blog", "forum", "community", "社区", "博客", "专栏")),
    ]
    for category, keywords in category_rules:
        if any(keyword in text for keyword in keywords):
            return category

    if source and source.category:
        return source.category
    return "行业动态"


def _infer_language(source: NewsSource | None, title: str, content: str) -> str:
    if source and source.language:
        return source.language
    combined = f"{title} {content}"
    return "zh" if _contains_chinese(combined) else "en"


def _score_hotness(db: Session, source: NewsSource | None, title: str, content: str) -> int:
    hot_keywords = _load_hot_keywords(db)
    text = f"{title} {content}".lower()
    score = 20
    if source and isinstance(source.extra, dict):
        weight = source.extra.get("weight")
        if isinstance(weight, int):
            score += weight
    if source and source.category:
        score += 4
    if len(content) > 250:
        score += 5
    if len(content) > 800:
        score += 5
    if len(content) > 1600:
        score += 5
    if title:
        score += min(len(title) // 8, 5)
    score += sum(8 for keyword in hot_keywords if keyword.lower() in text)
    signal_keywords = (
        "ai",
        "artificial intelligence",
        "model",
        "agent",
        "llm",
        "gpt",
        "openai",
        "anthropic",
        "deepseek",
        "huggingface",
        "modelscope",
        "policy",
        "governance",
        "research",
        "paper",
        "open source",
        "开源",
        "融资",
        "发布",
        "更新",
        "推理",
    )
    score += sum(4 for keyword in signal_keywords if keyword in text)
    if any(marker in text for marker in ("openai", "anthropic", "meta", "deepseek", "google", "huggingface", "modelscope")):
        score += 8
    if any(marker in text for marker in ("model", "agent", "llm", "ai", "人工智能", "大模型", "开源", "推理")):
        score += 6
    return min(score, 100)


def _is_sensitive(title: str, content: str, block_keywords: Iterable[str]) -> str | None:
    haystack = f"{title}\n{content}".lower()
    matched = [keyword for keyword in block_keywords if keyword and keyword.lower() in haystack]
    if matched:
        return "命中敏感词：" + "、".join(matched)
    return None


def _is_low_quality(title: str, content: str, hot_score: int, hot_threshold: int, source: NewsSource | None) -> str | None:
    if len(title) < 6:
        return "标题过短，疑似低质量内容"
    unique_tokens = _extract_keywords(f"{title} {content}")
    if len(unique_tokens) < 2 and len(content) < 220:
        return "有效信息过少，疑似低质量内容"
    normalized = f"{title} {content}".lower()
    relevance_keywords = (
        "ai",
        "model",
        "agent",
        "llm",
        "gpt",
        "openai",
        "anthropic",
        "deepseek",
        "huggingface",
        "modelscope",
        "人工智能",
        "大模型",
        "模型",
        "智能体",
        "开源",
        "推理",
        "论文",
        "研究",
        "融资",
        "产品",
        "发布",
        "更新",
    )
    relevance_hits = sum(1 for keyword in relevance_keywords if keyword in normalized)
    is_manual_source = source is not None and source.source_type == NewsSourceType.MANUAL.value
    if len(content) < 50:
        if not (is_manual_source and relevance_hits >= 1 and hot_score >= max(hot_threshold - 5, 0)):
            return "正文过短，疑似低质量内容"
    if len(content) < 80 and hot_score < hot_threshold + 5:
        if not (is_manual_source and relevance_hits >= 1 and hot_score >= max(hot_threshold - 5, 0)):
            return "正文过短，疑似低质量内容"
    if relevance_hits == 0 and hot_score < hot_threshold + 5:
        return "内容与 AI 热点关联度较低"
    if hot_score < hot_threshold:
        return f"热度不足，当前评分 {hot_score}，阈值 {hot_threshold}"
    return None


def _translate_phrase(text: str) -> str:
    translated = text
    for source_text, target_text in TRANSLATION_MAP:
        translated = re.sub(re.escape(source_text), target_text, translated, flags=re.IGNORECASE)
    translated = re.sub(r"\b(the|a|an|of|and|to|in|for|with|on|by|from|at|is|are|was|were)\b", " ", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\s+", " ", translated)
    return translated.strip(" .,:;")


def _build_translation(text: str) -> str:
    if not text:
        return ""
    if _contains_chinese(text):
        return text
    translated = _translate_phrase(text)
    if not translated:
        translated = text
    return translated


def _build_summary(title: str, content: str, style: str) -> str:
    source_text = content or title
    if not source_text:
        return ""
    sentences = [
        sentence.strip()
        for sentence in re.split(r"[。！？!?\.]\s*", source_text)
        if sentence.strip()
    ]
    selected = sentences[:2] if sentences else [source_text[:180]]
    lead = "；".join(selected)
    if not _contains_chinese(lead):
        lead = _translate_phrase(lead)
    return _normalize_whitespace(lead)[:220]


def _build_tags(
    db: Session,
    source: NewsSource | None,
    title: str,
    content: str,
    category: str,
    style: str,
) -> list[str]:
    prompt_tags = _load_config_value(db, "prompt", "news_tags_prompt", "") or ""
    tags: list[str] = []
    for candidate in (category, source.name if source else None, style):
        if candidate and candidate not in tags:
            tags.append(candidate)

    for keyword in _extract_keywords(f"{title} {content} {prompt_tags}"):
        if keyword not in tags:
            tags.append(keyword)
        if len(tags) >= 5:
            break
    return tags[:5]


def _build_script(
    *,
    title: str,
    category: str,
    summary: str,
    translated_title: str,
    style: str,
    tags: list[str],
) -> str:
    style_label = style or "professional"
    lead_title = translated_title or title
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


def _compute_dedup_hash(title: str, link: str, content: str, guid: str | None = None) -> str:
    payload = "|".join(
        [
            _normalize_signature(title),
            _normalize_signature(link),
            _normalize_signature(content[:600]),
            _normalize_signature(guid or ""),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _content_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    left_norm = _normalize_signature(left)
    right_norm = _normalize_signature(right)
    if not left_norm or not right_norm:
        return 0.0
    return difflib.SequenceMatcher(None, left_norm, right_norm).ratio()


def analyze_collected_entry(
    db: Session,
    source: NewsSource | None,
    entry: CollectedNewsEntry,
    *,
    style: str = "professional",
) -> ContentAnalysis:
    cleaned_title = _normalize_whitespace(entry.title or (source.name if source else ""))
    cleaned_content = _clean_content_text(entry.content or entry.summary or entry.title)
    cleaned_summary = _clean_content_text(entry.summary) if entry.summary else ""
    if cleaned_summary and len(cleaned_summary) > len(cleaned_content):
        cleaned_content = cleaned_summary
    category = _infer_category(source, cleaned_title, cleaned_content)
    language = _infer_language(source, cleaned_title, cleaned_content)
    hot_score = _score_hotness(db, source, cleaned_title, cleaned_content)
    block_keywords = _load_block_keywords(db)
    hot_threshold = _load_hot_threshold(db)
    filter_reason = _is_sensitive(cleaned_title, cleaned_content, block_keywords)
    if filter_reason is None:
        filter_reason = _is_low_quality(cleaned_title, cleaned_content, hot_score, hot_threshold, source)

    summary = _build_summary(cleaned_title, cleaned_content, style)
    translated_title = _build_translation(cleaned_title)
    translated_content = _build_translation(cleaned_content)
    tags = _build_tags(db, source, cleaned_title, cleaned_content, category, style)
    script = _build_script(
        title=cleaned_title,
        category=category,
        summary=summary or cleaned_content[:180],
        translated_title=translated_title or cleaned_title,
        style=style,
        tags=tags,
    )
    agent_metadata: dict[str, object] | None = None
    if filter_reason is None:
        agent_result = _refine_content_with_agent(
            db,
            title=cleaned_title,
            source_name=source.name if source else None,
            source_type=source.source_type if source else None,
            category=category,
            language=language,
            hot_score=hot_score,
            summary=summary,
            content=cleaned_content,
            style=style,
        )
        if agent_result is not None:
            refined_title = str(agent_result.get("title") or "").strip()
            if refined_title:
                cleaned_title = refined_title

            refined_summary = str(agent_result.get("summary") or "").strip()
            if refined_summary:
                summary = refined_summary

            refined_translated_title = str(agent_result.get("translated_title") or "").strip()
            if refined_translated_title:
                translated_title = refined_translated_title

            refined_translated_content = str(agent_result.get("translated_content") or "").strip()
            if refined_translated_content:
                translated_content = refined_translated_content

            agent_tags = _normalize_tag_candidates(agent_result.get("tags"), limit=5)
            if agent_tags:
                tags = _merge_tag_lists(tags, agent_tags, limit=5)

            refined_script = str(agent_result.get("script") or "").strip()
            if refined_script:
                script = refined_script

            agent_metadata = {
                "model_name": agent_result.get("model_name"),
                "prompt_version": agent_result.get("prompt_version"),
                "highlights": agent_result.get("highlights") or [],
            }

    dedup_hash = _compute_dedup_hash(cleaned_title, entry.link, cleaned_content, entry.guid)
    return ContentAnalysis(
        cleaned_title=cleaned_title,
        cleaned_content=cleaned_content,
        category=category,
        language=language,
        hot_score=hot_score,
        summary=summary,
        translated_title=translated_title,
        translated_content=translated_content,
        tags=tags,
        script=script,
        filter_reason=filter_reason,
        dedup_hash=dedup_hash,
        title_signature=_normalize_signature(cleaned_title),
        content_signature=_normalize_signature(cleaned_content[:1200]),
        raw_metadata={
            "cleaned_at": _now().isoformat(),
            "prompt_bundle": _load_prompt_bundle(db),
            "content_processing_agent": agent_metadata,
            "content_pipeline": "content-processing-agent-v1" if agent_metadata else "content-processing-rule-v1",
        },
    )


def _merge_raw_metadata(
    existing: dict[str, object] | None,
    incoming: dict[str, object],
    source: NewsSource,
    entry: CollectedNewsEntry,
    analysis: ContentAnalysis,
    *,
    fetch_mode: NewsFetchMode,
    request_id: str | None,
    task_job_id: int | None,
    triggered_by: int | None,
) -> dict[str, object]:
    metadata = dict(existing or {})
    merged_sources = list(metadata.get("merged_sources") or [])
    merged_sources.append(
        {
            "source_id": source.id,
            "source_key": source.source_key,
            "source_name": source.name,
            "source_type": source.source_type,
            "source_url": source.url,
            "url": entry.link,
            "guid": entry.guid,
            "fetch_mode": fetch_mode.value,
            "request_id": request_id,
            "task_job_id": task_job_id,
            "triggered_by": triggered_by,
            "merged_at": _now().isoformat(),
            "dedup_hash": analysis.dedup_hash,
        }
    )
    unique_sources: list[dict[str, object]] = []
    seen_keys: set[tuple[object, ...]] = set()
    for item in merged_sources:
        key = (item.get("source_key"), item.get("url"), item.get("guid"))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_sources.append(item)

    metadata.update(incoming)
    metadata["merged_sources"] = unique_sources
    metadata["last_merge_at"] = _now().isoformat()
    return metadata


def _get_existing_news_signature(news: News) -> tuple[str, str, str]:
    raw_metadata = news.raw_metadata if isinstance(news.raw_metadata, dict) else {}
    title_signature = raw_metadata.get("title_signature") or _normalize_signature(news.title)
    content_value = raw_metadata.get("cleaned_content") or news.content or ""
    content_signature = raw_metadata.get("content_signature") or _normalize_signature(str(content_value)[:1200])
    dedup_hash = news.dedup_hash or ""
    return str(title_signature), str(content_signature), dedup_hash


def _find_duplicate_news(
    db: Session,
    *,
    source: NewsSource,
    entry: CollectedNewsEntry,
    analysis: ContentAnalysis,
) -> News | None:
    candidates = db.scalars(select(News).order_by(News.id.desc())).all()
    for candidate in candidates:
        if candidate.url and entry.link and candidate.url.strip() == entry.link.strip():
            return candidate
        if candidate.dedup_hash and candidate.dedup_hash == analysis.dedup_hash:
            return candidate

        title_signature, content_signature, _ = _get_existing_news_signature(candidate)
        if title_signature and title_signature == analysis.title_signature:
            if content_signature and content_signature == analysis.content_signature:
                return candidate
            if _content_similarity(candidate.content or "", analysis.cleaned_content) >= 0.88:
                return candidate

        existing_raw = candidate.raw_metadata if isinstance(candidate.raw_metadata, dict) else {}
        existing_guid = str(existing_raw.get("guid") or "")
        if existing_guid and entry.guid and existing_guid == entry.guid:
            return candidate

    return None


def _apply_analysis_to_news(
    news: News,
    *,
    source: NewsSource,
    entry: CollectedNewsEntry,
    analysis: ContentAnalysis,
    fetch_mode: NewsFetchMode,
    request_id: str | None,
    task_job_id: int | None,
    triggered_by: int | None,
    force: bool,
    promote_rejected: bool = False,
) -> None:
    content_pipeline_name = "content-processing-rule-v1"
    if isinstance(analysis.raw_metadata, dict):
        content_pipeline_name = str(
            analysis.raw_metadata.get("content_pipeline") or content_pipeline_name,
        )
    raw_metadata = _merge_raw_metadata(
        news.raw_metadata if isinstance(news.raw_metadata, dict) else {},
        {
            **entry.raw,
            "raw_content": entry.content,
            "raw_summary": entry.summary,
            "raw_author": entry.author,
            "raw_guid": entry.guid,
            "source_key": source.source_key,
            "source_name": source.name,
            "source_type": source.source_type,
            "fetch_mode": fetch_mode.value,
            "content_pipeline": content_pipeline_name,
            "analysis": {
                "category": analysis.category,
                "language": analysis.language,
                "hot_score": analysis.hot_score,
                "dedup_hash": analysis.dedup_hash,
                "title_signature": analysis.title_signature,
                "content_signature": analysis.content_signature,
                "filter_reason": analysis.filter_reason,
                "force": force,
                "triggered_by": triggered_by,
                "task_job_id": task_job_id,
                "request_id": request_id,
            },
        },
        source,
        entry,
        analysis,
        fetch_mode=fetch_mode,
        request_id=request_id,
        task_job_id=task_job_id,
        triggered_by=triggered_by,
    )
    news.title = analysis.cleaned_title
    news.content = analysis.cleaned_content
    news.source = source.name
    news.source_id = source.id
    news.source_url = source.url
    news.url = entry.link
    news.publish_time = entry.published_at
    news.dedup_hash = analysis.dedup_hash
    news.category = analysis.category
    news.hot_score = max(news.hot_score or 0, analysis.hot_score)
    news.language = analysis.language
    news.raw_metadata = raw_metadata

    if analysis.filter_reason and not force and not promote_rejected:
        news.status = NewsStatus.REJECTED.value
        news.filter_reason = analysis.filter_reason
        news.summary = analysis.summary or news.summary
        news.translated_title = analysis.translated_title or news.translated_title
        news.translated_content = analysis.translated_content or news.translated_content
        news.tags = analysis.tags or news.tags
        news.script = analysis.script or news.script
        return

    news.status = NewsStatus.FILTERED.value
    news.filter_reason = None
    news.summary = analysis.summary
    news.translated_title = analysis.translated_title
    news.translated_content = analysis.translated_content
    news.tags = analysis.tags
    news.script = analysis.script


def process_collected_entry(
    db: Session,
    *,
    source: NewsSource,
    entry: CollectedNewsEntry,
    fetch_mode: NewsFetchMode,
    request_id: str | None = None,
    task_job_id: int | None = None,
    triggered_by: int | None = None,
    style: str = "professional",
    force: bool = False,
) -> ContentProcessOutcome:
    analysis = analyze_collected_entry(db, source, entry, style=style)
    duplicate_news = _find_duplicate_news(db, source=source, entry=entry, analysis=analysis)
    if duplicate_news is not None:
        duplicate_status_before = duplicate_news.status
        if duplicate_status_before in {NewsStatus.FILTERED.value, NewsStatus.SCRIPT_READY.value} and analysis.filter_reason:
            duplicate_news.raw_metadata = _merge_raw_metadata(
                duplicate_news.raw_metadata if isinstance(duplicate_news.raw_metadata, dict) else {},
                {
                    **entry.raw,
                    "raw_content": entry.content,
                    "raw_summary": entry.summary,
                    "raw_author": entry.author,
                    "raw_guid": entry.guid,
                    "source_key": source.source_key,
                    "source_name": source.name,
                    "source_type": source.source_type,
                    "fetch_mode": fetch_mode.value,
                    "content_pipeline": analysis.raw_metadata.get("content_pipeline")
                    if isinstance(analysis.raw_metadata, dict)
                    else "content-processing-rule-v1",
                    "analysis": {
                        "category": analysis.category,
                        "language": analysis.language,
                        "hot_score": analysis.hot_score,
                        "dedup_hash": analysis.dedup_hash,
                        "title_signature": analysis.title_signature,
                        "content_signature": analysis.content_signature,
                        "filter_reason": analysis.filter_reason,
                        "force": force,
                        "triggered_by": triggered_by,
                        "task_job_id": task_job_id,
                        "request_id": request_id,
                    },
                },
                source,
                entry,
                analysis,
                fetch_mode=fetch_mode,
                request_id=request_id,
                task_job_id=task_job_id,
                triggered_by=triggered_by,
            )
            duplicate_news.hot_score = max(duplicate_news.hot_score or 0, analysis.hot_score)
            db.add(duplicate_news)
            db.flush()
            return ContentProcessOutcome(
                news=duplicate_news,
                created=False,
                merged=True,
                duplicate=True,
                promoted_from_rejected=False,
                analysis=analysis,
            )

        _apply_analysis_to_news(
            duplicate_news,
            source=source,
            entry=entry,
            analysis=analysis,
            fetch_mode=fetch_mode,
            request_id=request_id,
            task_job_id=task_job_id,
            triggered_by=triggered_by,
            force=force,
            promote_rejected=duplicate_status_before == NewsStatus.REJECTED.value and not analysis.filter_reason,
        )
        db.add(duplicate_news)
        db.flush()
        return ContentProcessOutcome(
            news=duplicate_news,
            created=False,
            merged=True,
            duplicate=True,
            promoted_from_rejected=duplicate_status_before == NewsStatus.REJECTED.value
            and duplicate_news.status == NewsStatus.FILTERED.value,
            analysis=analysis,
        )

    news = News(
        title=analysis.cleaned_title,
        content=analysis.cleaned_content,
        source=source.name,
        source_id=source.id,
        source_url=source.url,
        url=entry.link,
        publish_time=entry.published_at,
        status=NewsStatus.NEW.value,
        dedup_hash=analysis.dedup_hash,
        category=analysis.category,
        hot_score=analysis.hot_score,
        language=analysis.language,
        raw_metadata={
            **entry.raw,
            "raw_content": entry.content,
            "raw_summary": entry.summary,
            "raw_author": entry.author,
            "raw_guid": entry.guid,
            "source_key": source.source_key,
            "source_name": source.name,
            "source_type": source.source_type,
            "fetch_mode": fetch_mode.value,
            "content_pipeline": analysis.raw_metadata.get("content_pipeline")
            if isinstance(analysis.raw_metadata, dict)
            else "content-processing-rule-v1",
            "analysis": {
                "category": analysis.category,
                "language": analysis.language,
                "hot_score": analysis.hot_score,
                "dedup_hash": analysis.dedup_hash,
                "title_signature": analysis.title_signature,
                "content_signature": analysis.content_signature,
                "filter_reason": analysis.filter_reason,
                "force": force,
                "triggered_by": triggered_by,
                "task_job_id": task_job_id,
                "request_id": request_id,
            },
            **analysis.raw_metadata,
        },
    )
    db.add(news)
    db.flush()
    _apply_analysis_to_news(
        news,
        source=source,
        entry=entry,
        analysis=analysis,
        fetch_mode=fetch_mode,
        request_id=request_id,
        task_job_id=task_job_id,
        triggered_by=triggered_by,
        force=force,
    )
    db.add(news)
    db.flush()
    return ContentProcessOutcome(
        news=news,
        created=True,
        merged=False,
        duplicate=False,
        promoted_from_rejected=False,
        analysis=analysis,
    )


def process_existing_news_item(
    db: Session,
    *,
    news: News,
    style: str = "professional",
    force: bool = False,
    request_id: str | None = None,
    task_job_id: int | None = None,
    triggered_by: int | None = None,
) -> News:
    if news.status == NewsStatus.REJECTED.value and not force:
        raise ValidationException(message="已拒绝的内容请使用 force=True 重新处理")

    source = db.get(NewsSource, news.source_id) if news.source_id else None
    if source is None:
        source = NewsSource(
            source_key=f"news-{news.id}",
            name=news.source,
            source_type=NewsSourceType.MANUAL.value,
            url=news.source_url or news.url,
            category=news.category,
            language=news.language or "en",
            fetch_interval_minutes=360,
            is_enabled=True,
            extra={},
        )
        db.add(source)
        db.flush()

    raw_metadata = news.raw_metadata if isinstance(news.raw_metadata, dict) else {}
    entry = CollectedNewsEntry(
        title=news.title,
        link=news.url,
        content=str(raw_metadata.get("raw_content") or news.content or news.title),
        published_at=news.publish_time,
        summary=str(raw_metadata.get("raw_summary") or news.summary or ""),
        author=str(raw_metadata.get("raw_author") or ""),
        guid=str(raw_metadata.get("raw_guid") or news.url),
        raw=raw_metadata,
    )
    analysis = analyze_collected_entry(db, source, entry, style=style)
    _apply_analysis_to_news(
        news,
        source=source,
        entry=entry,
        analysis=analysis,
        fetch_mode=NewsFetchMode.MANUAL,
        request_id=request_id,
        task_job_id=task_job_id,
        triggered_by=triggered_by,
        force=force,
        promote_rejected=False,
    )
    news.raw_metadata = {
        **(news.raw_metadata or {}),
        "manual_reprocess": {
            "request_id": request_id,
            "task_job_id": task_job_id,
            "triggered_by": triggered_by,
            "reprocessed_at": _now().isoformat(),
            "style": style,
            "force": force,
        },
    }
    db.add(news)
    db.flush()
    return news
