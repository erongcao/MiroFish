"""
Domestic Politics - 国内政治压力系统
民意、选举、政治约束对 Agent 外交决策的影响
"""

import random
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

class PoliticalSystem(Enum):
    DEMOCRACY = "democracy"      # 民主制
    AUTOCRACY = "autocracy"      # 威权制
    HYBRID = "hybrid"            # 混合制

class IssueType(Enum):
    WAR = "war"                  # 战争支持度
    ECONOMY = "economy"          # 经济
    DIPLOMACY = "diplomacy"      # 外交
    TRADE = "trade"              # 贸易
    HUMAN_RIGHTS = "human_rights" # 人权

@dataclass
class PublicOpinion:
    """民意状态"""
    issue: IssueType
    support: float = 0.5           # 支持度 (-1 反对, 1 支持)
    intensity: float = 0.5         # 强度 (0-1)
    volatility: float = 0.1        # 波动性
    
    def update(self, event_impact: float, media_framing: float = 0.0):
        """更新民意"""
        # 事件影响
        self.support += event_impact * self.intensity
        
        # 媒体框架影响
        self.support += media_framing * 0.1
        
        # 随机波动
        self.support += random.uniform(-self.volatility, self.volatility)
        
        # 边界
        self.support = max(-1.0, min(1.0, self.support))
        
        # 强度随时间衰减
        self.intensity = max(0.1, self.intensity * 0.95)

@dataclass
class DomesticPoliticalState:
    """Agent 国内政治状态"""
    agent_id: str
    political_system: PoliticalSystem = PoliticalSystem.DEMOCRACY
    
    # 民意
    public_opinions: Dict[IssueType, PublicOpinion] = field(default_factory=dict)
    
    # 政治资本
    political_capital: float = 1.0   # 政治资本 (0-1)
    approval_rating: float = 0.5     # 支持率
    
    # 约束
    term_limited: bool = False       # 是否任期限制
    term_remaining: int = 4          # 剩余任期轮数
    
    # 精英支持
    elite_support: float = 0.5       # 精英阶层支持
    military_support: float = 0.5    # 军方支持
    business_support: float = 0.5    # 商界支持
    
    # 历史
    promises_made: List[Dict] = field(default_factory=list)
    promises_kept: float = 0.5       # 承诺兑现率
    
    def __post_init__(self):
        """初始化默认民意"""
        if not self.public_opinions:
            for issue in IssueType:
                self.public_opinions[issue] = PublicOpinion(
                    issue=issue,
                    support=random.uniform(-0.2, 0.2),
                    intensity=random.uniform(0.3, 0.7),
                )
    
    def get_effective_constraint(self, action_type: str) -> float:
        """计算行动的有效约束 (-1 强烈反对, 1 强烈支持)"""
        
        # 民意约束
        if action_type in ["war", "attack", "escalate"]:
            opinion = self.public_opinions.get(IssueType.WAR)
            public_constraint = opinion.support if opinion else 0.0
        elif action_type in ["trade", "cooperate", "appease"]:
            opinion = self.public_opinions.get(IssueType.TRADE)
            public_constraint = opinion.support if opinion else 0.0
        else:
            opinion = self.public_opinions.get(IssueType.DIPLOMACY)
            public_constraint = opinion.support if opinion else 0.0
        
        # 政治体制调节
        if self.political_system == PoliticalSystem.DEMOCRACY:
            # 民主制：民意权重高
            public_weight = 0.5
            elite_weight = 0.2
            military_weight = 0.2
            business_weight = 0.1
        elif self.political_system == PoliticalSystem.AUTOCRACY:
            # 威权制：精英/军方权重高
            public_weight = 0.1
            elite_weight = 0.4
            military_weight = 0.3
            business_weight = 0.2
        else:
            # 混合制
            public_weight = 0.3
            elite_weight = 0.3
            military_weight = 0.2
            business_weight = 0.2
        
        # 综合约束
        constraint = (
            public_constraint * public_weight +
            self.elite_support * elite_weight +
            self.military_support * military_weight +
            self.business_support * business_weight
        )
        
        # 政治资本调节（资本低时更保守）
        if self.political_capital < 0.3:
            constraint *= 0.5  # 更保守
        
        # 任期限制（临近任期结束更激进或更保守）
        if self.term_limited and self.term_remaining <= 2:
            # 即将卸任：更自由（无需担心连任）
            constraint *= 1.2
        
        return max(-1.0, min(1.0, constraint))
    
    def apply_action_consequences(self, action_type: str, 
                                  success: bool, cost: float):
        """应用行动后果到国内政治"""
        
        # 消耗政治资本
        self.political_capital = max(0.0, self.political_capital - cost * 0.1)
        
        # 更新支持率
        if success:
            self.approval_rating = min(1.0, self.approval_rating + 0.05)
            self.promises_kept = min(1.0, self.promises_kept + 0.02)
        else:
            self.approval_rating = max(0.0, self.approval_rating - 0.08)
        
        # 更新特定民意
        if action_type in ["war", "attack"]:
            opinion = self.public_opinions.get(IssueType.WAR)
            if opinion:
                if success:
                    opinion.update(0.1)  # 胜利提升支持
                else:
                    opinion.update(-0.2)  # 失败降低支持
        
        elif action_type in ["cooperate", "trade", "appease"]:
            opinion = self.public_opinions.get(IssueType.TRADE)
            if opinion:
                if success:
                    opinion.update(0.05)
                else:
                    opinion.update(-0.1)
        
        # 经济影响
        if cost > 5.0:
            opinion = self.public_opinions.get(IssueType.ECONOMY)
            if opinion:
                opinion.update(-0.05 * cost / 10)
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "political_system": self.political_system.value,
            "approval_rating": self.approval_rating,
            "political_capital": self.political_capital,
            "elite_support": self.elite_support,
            "military_support": self.military_support,
            "business_support": self.business_support,
            "term_remaining": self.term_remaining,
            "public_opinions": {
                k.value: {"support": v.support, "intensity": v.intensity}
                for k, v in self.public_opinions.items()
            },
        }


class DomesticPolitics:
    """国内政治系统"""
    
    def __init__(self):
        self.political_states: Dict[str, DomesticPoliticalState] = {}
        
        # 配置
        self.election_cycle = 8          # 选举周期轮数
        self.media_influence = 0.3       # 媒体影响力
    
    def initialize_agent(self, agent_id: str, 
                        political_system: PoliticalSystem = PoliticalSystem.DEMOCRACY,
                        initial_approval: float = 0.5):
        """初始化 Agent 政治状态"""
        self.political_states[agent_id] = DomesticPoliticalState(
            agent_id=agent_id,
            political_system=political_system,
            approval_rating=initial_approval,
        )
    
    def get_political_constraint(self, agent_id: str, action_type: str) -> float:
        """获取政治约束"""
        state = self.political_states.get(agent_id)
        if not state:
            return 0.0
        
        return state.get_effective_constraint(action_type)
    
    def apply_action(self, agent_id: str, action_type: str, 
                    success: bool, cost: float = 0.0):
        """应用行动并更新政治状态"""
        state = self.political_states.get(agent_id)
        if not state:
            return
        
        state.apply_action_consequences(action_type, success, cost)
    
    def simulate_media_event(self, agent_id: str, issue: IssueType,
                            framing: float, intensity: float = 0.5):
        """模拟媒体事件影响"""
        state = self.political_states.get(agent_id)
        if not state:
            return
        
        opinion = state.public_opinions.get(issue)
        if opinion:
            opinion.intensity = max(opinion.intensity, intensity)
            opinion.update(0.0, framing * self.media_influence)
    
    def check_political_survival(self, agent_id: str) -> bool:
        """检查政治生存"""
        state = self.political_states.get(agent_id)
        if not state:
            return True
        
        # 支持率过低可能下台
        if state.approval_rating < 0.15:
            return False
        
        # 政治资本耗尽
        if state.political_capital < 0.05:
            return False
        
        # 精英/军方联合反对
        if state.elite_support < 0.2 and state.military_support < 0.2:
            return False
        
        return True
    
    def get_context_for_decision(self, agent_id: str) -> Dict:
        """获取决策上下文"""
        state = self.political_states.get(agent_id)
        if not state:
            return {}
        
        return {
            "approval_rating": state.approval_rating,
            "political_capital": state.political_capital,
            "effective_constraints": {
                "war": state.get_effective_constraint("war"),
                "trade": state.get_effective_constraint("trade"),
                "diplomacy": state.get_effective_constraint("diplomacy"),
            },
            "survival_risk": not self.check_political_survival(agent_id),
            "public_opinions": {
                k.value: {"support": v.support, "intensity": v.intensity}
                for k, v in state.public_opinions.items()
            },
        }
    
    def advance_round(self):
        """进入下一轮"""
        for state in self.political_states.values():
            # 恢复政治资本
            state.political_capital = min(1.0, state.political_capital + 0.05)
            
            # 减少任期
            if state.term_remaining > 0:
                state.term_remaining -= 1
            
            # 民意自然衰减
            for opinion in state.public_opinions.values():
                # 回归均值
                opinion.support += (0.0 - opinion.support) * 0.02
    
    def get_summary(self) -> Dict:
        """获取国内政治摘要"""
        return {
            "total_agents": len(self.political_states),
            "avg_approval": np.mean([s.approval_rating for s in self.political_states.values()]),
            "at_risk": sum(1 for s in self.political_states.values() 
                          if not self.check_political_survival(s.agent_id)),
            "agents": {aid: s.to_dict() for aid, s in self.political_states.items()},
        }


# 使用示例
if __name__ == "__main__":
    politics = DomesticPolitics()
    
    # 初始化不同体制
    politics.initialize_agent("usa", PoliticalSystem.DEMOCRACY, 0.55)
    politics.initialize_agent("china", PoliticalSystem.AUTOCRACY, 0.70)
    politics.initialize_agent("russia", PoliticalSystem.HYBRID, 0.45)
    
    # 检查战争约束
    for agent in ["usa", "china", "russia"]:
        constraint = politics.get_political_constraint(agent, "war")
        print(f"{agent} 战争约束: {constraint:.2f}")
    
    # 模拟战争行动
    politics.apply_action("usa", "war", success=False, cost=8.0)
    
    # 查看 USA 政治状态
    context = politics.get_context_for_decision("usa")
    print(f"\nUSA 决策上下文:")
    print(f"  支持率: {context['approval_rating']:.2f}")
    print(f"  政治资本: {context['political_capital']:.2f}")
    print(f"  生存风险: {context['survival_risk']}")
