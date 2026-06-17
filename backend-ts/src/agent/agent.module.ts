import { Module } from '@nestjs/common';
import { PrismaModule } from '../prisma/prisma.module';
import { AgentService } from './agent.service';
import { AgentController } from './agent.controller';

// AgentScope 运行时 + 6 个 Agent + 编排器
import { AgentScopeRuntimeService } from '../agents/agents.runtime';
import { HotspotAgent } from '../agents/hotspot.agent';
import { ClassificationAgent } from '../agents/classification.agent';
import { SummaryAgent } from '../agents/summary.agent';
import { EnrichmentAgent } from '../agents/enrichment.agent';
import { PushPlannerAgent } from '../agents/push-planner.agent';
import { DigestAgent } from '../agents/digest.agent';
import { AgentOrchestrator } from '../agents/agents.orchestrator';

@Module({
  imports: [PrismaModule],
  controllers: [AgentController],
  providers: [
    // 核心服务
    AgentService,
    // AgentScope 运行时
    AgentScopeRuntimeService,
    // 6 个 Agent
    HotspotAgent,
    ClassificationAgent,
    SummaryAgent,
    EnrichmentAgent,
    PushPlannerAgent,
    DigestAgent,
    // 编排器
    AgentOrchestrator,
  ],
  exports: [
    AgentService,
    AgentScopeRuntimeService,
    AgentOrchestrator,
    HotspotAgent,
    ClassificationAgent,
    SummaryAgent,
    EnrichmentAgent,
    PushPlannerAgent,
    DigestAgent,
  ],
})
export class AgentModule {}
