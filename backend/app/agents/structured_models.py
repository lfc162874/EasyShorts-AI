from __future__ import annotations

from pydantic import BaseModel, Field


class HotspotStructuredOutput(BaseModel):
    is_hot: bool = Field(description="是否判定为值得继续处理的热点")
    score: int = Field(description="热度分值，0 到 100")
    priority: str = Field(description="优先级，通常为 HIGH、MEDIUM 或 LOW")
    trend: str = Field(description="趋势判断，通常为 RISING、WATCH 或 STABLE")
    reason: str = Field(description="判定原因")
    keywords: list[str] = Field(default_factory=list, description="关键词列表")


class ClassificationStructuredOutput(BaseModel):
    category: str = Field(description="内容分类")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    keywords: list[str] = Field(default_factory=list, description="关键词列表")
    topic_hint: str = Field(description="主题提示")
    hot_score: int = Field(description="用于分类参考的热度分值")


class SummaryStructuredOutput(BaseModel):
    title: str = Field(description="优化后的标题")
    summary: str = Field(description="简明摘要")
    highlights: list[str] = Field(default_factory=list, description="要点列表")
    source_summary: str = Field(default="", description="原始摘要")


class ContentProcessingStructuredOutput(BaseModel):
    title: str = Field(description="优化后的标题")
    summary: str = Field(description="简明摘要")
    highlights: list[str] = Field(default_factory=list, description="要点列表")
    translated_title: str = Field(description="中文标题或中文改写")
    translated_content: str = Field(description="中文内容摘要式改写")
    tags: list[str] = Field(default_factory=list, description="标签列表")
    script: str = Field(description="口播脚本")


class EnrichmentStructuredOutput(BaseModel):
    background: str = Field(description="背景说明")
    impact: str = Field(description="影响分析")
    technical_analysis: str = Field(description="技术分析")
    application_scenarios: list[str] = Field(default_factory=list, description="应用场景")


class PushPlanStructuredOutput(BaseModel):
    push_now: bool = Field(description="是否立即推送")
    priority: str = Field(description="推送优先级")
    push_type: str = Field(description="推送类型")
    channels: list[str] = Field(default_factory=list, description="推送渠道")
    planned_at: str = Field(description="计划执行时间，ISO8601")
    reason: str = Field(description="推送决策原因")
    title: str = Field(description="推送标题")


class DigestStructuredOutput(BaseModel):
    title: str = Field(description="简报标题")
    summary: str = Field(description="简报摘要")
    highlights: list[str] = Field(default_factory=list, description="简报要点")
    topic_count: int = Field(description="覆盖热点数量")
