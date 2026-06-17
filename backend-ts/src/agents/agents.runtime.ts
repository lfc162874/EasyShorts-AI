/**
 * AgentScope 运行时封装
 * 封装 DashScopeChatModel + Agent，提供结构化输出调用能力
 *
 * 设计原则：
 * - AI-first rule-fallback：优先调用 LLM，失败时降级为规则逻辑
 * - 每个方法都是独立的，可被各 Agent Service 调用
 * - 通过 ConfigService 读取配置，支持运行时切换模型
 */

import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { DashScopeChatModel } from '@agentscope-ai/agentscope/model';
import { Agent } from '@agentscope-ai/agentscope/agent';
import { UserMsg } from '@agentscope-ai/agentscope/message';
import { z } from 'zod';

import type { AgentScopeRuntime } from './agents.types';

@Injectable()
export class AgentScopeRuntimeService {
  private readonly logger = new Logger(AgentScopeRuntimeService.name);
  private _model: DashScopeChatModel | null = null;
  private _apiKey: string | null = null;
  private _modelName: string | null = null;

  constructor(private readonly configService: ConfigService) {}

  /** 获取当前配置的 API Key */
  get apiKey(): string | null {
    if (!this._apiKey) {
      this._apiKey = this.configService.get<string>('agent.dashscopeApiKey') || process.env.DASHSCOPE_API_KEY || null;
    }
    return this._apiKey;
  }

  /** 获取当前配置的模型名称 */
  get modelName(): string {
    if (!this._modelName) {
      this._modelName = this.configService.get<string>('agent.defaultModelName', 'qwen3.5-plus');
    }
    return this._modelName;
  }

  /** 检查 AgentScope 运行时是否可用（API Key 已配置） */
  isAvailable(): boolean {
    return !!this.apiKey;
  }

  /** 获取运行时信息（供 Agent 执行上下文使用） */
  getRuntimeInfo(): AgentScopeRuntime | null {
    if (!this.isAvailable()) return null;
    return {
      modelName: this.modelName,
      apiKey: this.apiKey!,
    };
  }

  /**
   * 获取或创建 DashScope 模型实例（懒初始化）
   * 使用单例模式避免重复创建连接
   */
  getModel(): DashScopeChatModel | null {
    if (!this.isAvailable()) return null;

    if (!this._model) {
      try {
        this._model = new DashScopeChatModel({
          modelName: this.modelName,
          apiKey: this.apiKey!,
          stream: false,
          maxRetries: 2,
        });
        this.logger.debug(`AgentScope DashScope 模型已初始化: ${this.modelName}`);
      } catch (error) {
        this.logger.error(`AgentScope 模型初始化失败: ${error instanceof Error ? error.message : error}`);
        return null;
      }
    }
    return this._model;
  }

  /**
   * 调用 Agent 进行结构化输出（核心方法）
   *
   * @param options - 调用选项
   * @returns 解析后的结构化数据，失败返回 null（调用方应降级到规则逻辑）
   */
  async callStructured<T>(options: {
    agentName: string;
    systemPrompt: string;
    userPrompt: string;
    schema: z.ZodObject<Record<string, z.ZodTypeAny>>;
  }): Promise<T | null> {
    const model = this.getModel();
    if (!model) {
      this.logger.debug(`[${options.agentName}] AgentScope 不可用，跳过 AI 调用`);
      return null;
    }

    let agent: Agent;
    try {
      agent = new Agent({
        name: options.agentName,
        sysPrompt: options.systemPrompt,
        model,
        maxIters: 1,
      });
    } catch (error) {
      this.logger.error(`[${options.agentName}] Agent 创建失败: ${error instanceof Error ? error.message : error}`);
      return null;
    }

    try {
      const msg = await agent.reply({
        msgs: UserMsg({ name: 'user', content: options.userPrompt }),
        structuredModel: options.schema,
      });

      // 从回复消息中提取文本内容并解析 JSON
      const textContent = typeof msg === 'string' ? msg : JSON.stringify(msg);
      const cleaned = textContent.replace(/```json\n?|\n?```/g, '').trim();
      const parsed = JSON.parse(cleaned);

      this.logger.debug(`[${options.agentName}] AI 调用成功`);
      return parsed as T;
    } catch (error) {
      this.logger.warn(
        `[${options.agentName}] AI 调用失败，将降级到规则逻辑: ${error instanceof Error ? error.message : error}`,
      );
      return null;
    }
  }

  /**
   * 简单的文本补全调用（非结构化）
   * 用于不需要严格 JSON 输出的场景
   */
  async callText(options: {
    agentName: string;
    systemPrompt: string;
    userPrompt: string;
  }): Promise<string | null> {
    const model = this.getModel();
    if (!model) return null;

    let agent: Agent;
    try {
      agent = new Agent({
        name: options.agentName,
        sysPrompt: options.systemPrompt,
        model,
        maxIters: 1,
      });
    } catch {
      return null;
    }

    try {
      const msg = await agent.reply({
        msgs: UserMsg({ name: 'user', content: options.userPrompt }),
      });
      const textContent = typeof msg === 'string' ? msg : JSON.stringify(msg);
      return typeof textContent === 'string' ? textContent.trim() : JSON.stringify(textContent);
    } catch (error) {
      this.logger.warn(`[${options.agentName}] 文本调用失败: ${error instanceof Error ? error.message : error}`);
      return null;
    }
  }
}
