from __future__ import annotations

import hashlib
import html
import re
from datetime import UTC, datetime, timedelta
from typing import Iterable

HOT_KEYWORDS = (
    "openai",
    "anthropic",
    "deepseek",
    "qwen",
    "modelscope",
    "huggingface",
    "agent",
    "llm",
    "gpt",
    "model",
    "paper",
    "research",
    "open source",
    "opensource",
    "开源",
    "融资",
    "发布",
    "更新",
    "推理",
    "政策",
    "监管",
)

CATEGORY_RULES: list[tuple[str, Iterable[str]]] = [
    ("AI Agent", ("agent", "tool use", "tool calling", "智能体", "workflow", "automation")),
    ("大模型", ("llm", "model", "reasoning", "benchmark", "大模型", "模型", "参数", "推理")),
    ("开源生态", ("open source", "opensource", "开源", "github", "huggingface", "modelscope")),
    ("AI产品发布", ("launch", "release", "update", "ship", "发布", "更新", "上线", "功能")),
    ("学术研究", ("paper", "arxiv", "research", "论文", "研究", "实验")),
    ("融资动态", ("funding", "investment", "round", "融资", "投资", "天使轮", "A轮", "B轮")),
    ("政策监管", ("policy", "regulation", "law", "政策", "监管", "法案", "合规")),
]

BLACKLIST_WORDS = {
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
    "content",
    "contented",
    "内容",
    "新闻",
    "今天",
    "最新",
    "一个",
    "我们",
    "他们",
}


def normalize_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def contains_chinese(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def normalize_signature(value: str | None) -> str:
    if not value:
        return ""
    text = normalize_whitespace(value).lower()
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return text


def extract_keywords(text: str) -> list[str]:
    raw_terms = re.findall(r"[A-Za-z][A-Za-z0-9+._-]{2,}|[\u4e00-\u9fff]{2,6}", text)
    keywords: list[str] = []
    for term in raw_terms:
        normalized = term.strip().strip(".,:;!?()[]{}<>\"'`")
        if not normalized:
            continue
        if normalized.lower() in BLACKLIST_WORDS or normalized in keywords:
            continue
        keywords.append(normalized)
    return keywords[:8]


def split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"[。！？!?\.]\s*", text) if sentence.strip()]


def summarize_text(text: str, *, limit: int = 220) -> str:
    if not text:
        return ""
    sentences = split_sentences(text)
    selected = sentences[:2] if sentences else [text[:180]]
    summary = "；".join(selected)
    if not contains_chinese(summary):
        summary = summary.strip()
    return normalize_whitespace(summary)[:limit]


def infer_category(title: str, content: str, fallback: str | None = None) -> str:
    text = f"{title} {content}".lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return fallback or "行业动态"


def infer_priority(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 60:
        return "MEDIUM"
    return "LOW"


def infer_trend(score: int, *, title: str, content: str) -> str:
    text = f"{title} {content}".lower()
    if score >= 80 or any(keyword in text for keyword in ("breaking", "紧急", "首发", "发布")):
        return "RISING"
    if score >= 60:
        return "WATCH"
    return "STABLE"


def merge_channels(*channel_groups: Iterable[str | None]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in channel_groups:
        for channel in group:
            normalized = normalize_whitespace(str(channel or "")).lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            merged.append(normalized)
    return merged


def recommend_channels(priority: str) -> list[str]:
    if priority == "HIGH":
        return ["webhook", "email", "feishu", "wechat_work"]
    if priority == "MEDIUM":
        return ["webhook", "email", "feishu"]
    return ["webhook", "email"]


def compute_topic_key(title: str, category: str | None) -> str:
    payload = "|".join([normalize_signature(title), normalize_signature(category or "")])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_highlights(text: str, keywords: list[str]) -> list[str]:
    sentences = split_sentences(text)
    highlights: list[str] = []
    for sentence in sentences[:3]:
        if sentence not in highlights:
            highlights.append(sentence[:160])
    if keywords:
        keyword_text = "、".join(keywords[:3])
        highlights.append(f"核心关键词：{keyword_text}")
    return highlights[:4]


def build_background(category: str, title: str, keywords: list[str]) -> str:
    if category == "AI Agent":
        return f"这条 {category} 动态围绕 {title} 展开，和智能体编排、工具调用以及自动化流程相关。"
    if category == "大模型":
        return f"这条 {category} 动态涉及 {title}，通常会影响模型能力、推理成本和产品迭代节奏。"
    if category == "开源生态":
        return f"这条 {category} 动态涉及 {title}，对社区传播、生态协作和二次开发都比较敏感。"
    if keywords:
        return f"这条 {category} 动态围绕 {title} 展开，关键词包括 {', '.join(keywords[:3])}。"
    return f"这条 {category} 动态围绕 {title} 展开。"


def build_impact(category: str, score: int, keywords: list[str]) -> str:
    focus = "、".join(keywords[:3]) if keywords else "AI 生态"
    if score >= 80:
        return f"这类高热度内容会直接影响 {focus} 方向的关注度和后续传播节奏。"
    if category in {"AI Agent", "大模型"}:
        return f"该内容可能影响 {focus} 的产品落地、方法迭代与讨论热度。"
    return f"该内容会为 {focus} 提供补充信息，适合纳入持续观察。"


def build_technical_analysis(category: str, keywords: list[str]) -> str:
    if category == "AI Agent":
        return "重点关注编排方式、工具调用、上下文管理和任务拆分是否有变化。"
    if category == "大模型":
        return "重点关注模型规模、推理能力、上下文长度和成本变化。"
    if category == "开源生态":
        return "重点关注开源协议、仓库活跃度、复现门槛和社区参与度。"
    if keywords:
        return f"从技术角度看，需关注 {', '.join(keywords[:3])} 的变化。"
    return "从技术角度看，可继续追踪相关实现细节和落地方式。"


def build_application_scenarios(category: str, keywords: list[str]) -> list[str]:
    scenarios = [
        f"用于跟进 {category} 的最新行业动态。",
        "用于生成简报、日报或周报摘要。",
    ]
    if keywords:
        scenarios.append(f"用于围绕 {', '.join(keywords[:2])} 建立持续监控。")
    return scenarios[:3]


def build_model_label(model_name: str) -> str:
    labels = {
        "qwen3.5-plus": "通义千问 3.5 Plus",
        "qwen-max": "通义千问 Max",
        "deepseek-v3": "DeepSeek V3",
        "deepseek-r1": "DeepSeek R1",
    }
    return labels.get(model_name, model_name)


def build_planned_at(push_now: bool) -> datetime:
    now = datetime.now(UTC)
    if push_now:
        return now
    return now + timedelta(hours=6)
