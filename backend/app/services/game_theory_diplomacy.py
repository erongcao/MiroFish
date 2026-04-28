"""
Game Theory Diplomacy Engine - 博弈论外交引擎
基于真实博弈论机制的外交系统
"""

import random
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class DiplomaticAction(Enum):
    COOPERATE = "cooperate"      # 合作
    DEFECT = "defect"            # 背叛
    DETER = "deter"              # 威慑
    ESCALATE = "escalate"        # 升级
    NEGOTIATE = "negotiate"      # 谈判
    SANCTION = "sanction"        # 制裁
    APPEASE = "appease"          # 绥靖
    IGNORE = "ignore"            # 无视

class ConflictLevel(Enum):
    PEACE = "peace"              # 和平
    TENSION = "tension"          # 紧张
    CRISIS = "crisis"            # 危机
    SANCTIONS = "sanctions"      # 制裁
    PROXY_WAR = "proxy_war"      # 代理人战争
    LIMITED_WAR = "limited_war"  # 有限战争
    TOTAL_WAR = "total_war"      # 全面战争

@dataclass
class PayoffMatrix:
    """收益矩阵 - 囚徒困境扩展"""
    # (己方收益, 对方收益)
    cooperate_cooperate: Tuple[float, float] = (3.0, 3.0)    # 双赢
    cooperate_defect: Tuple[float, float] = (0.0, 5.0)      # 被背叛
    defect_cooperate: Tuple[float, float] = (5.0, 0.0)      # 背叛成功
    defect_defect: Tuple[float, float] = (1.0, 1.0)         # 双输
    
    def get_payoff(self, my_action: DiplomaticAction, 
                   their_action: DiplomaticAction) -> Tuple[float, float]:
        if my_action == DiplomaticAction.COOPERATE:
            if their_action == DiplomaticAction.COOPERATE:
                return self.cooperate_cooperate
            else:
                return self.cooperate_defect
        else:  # DEFECT or ESCALATE
            if their_action == DiplomaticAction.COOPERATE:
                return self.defect_cooperate
            else:
                return self.defect_defect

@dataclass
class DiplomaticHistory:
    """外交历史记录 - 用于声誉计算"""
    round: int
    action: DiplomaticAction
    target: str
    success: bool
    payoff: float
    betrayal: bool = False  # 是否背叛了对方

@dataclass
class AgentDiplomaticState:
    """Agent 外交状态"""
    agent_id: str
    reputation: float = 0.0           # 声誉 (-1 到 1)
    credibility: float = 1.0          # 可信度 (0 到 1)
    aggression: float = 0.5         # 攻击性 (0 到 1)
    cooperation_bias: float = 0.3     # 合作倾向
    trust_memory: Dict[str, float] = field(default_factory=dict)  # 对其他 agent 的信任
    history: List[DiplomaticHistory] = field(default_factory=list)
    resources: float = 100.0          # 资源/国力
    war_exhaustion: float = 0.0       # 战争疲劳
    
    def update_reputation(self, action: DiplomaticAction, success: bool):
        """更新声誉"""
        if action == DiplomaticAction.COOPERATE and success:
            self.reputation = min(1.0, self.reputation + 0.1)
        elif action == DiplomaticAction.DEFECT:
            self.reputation = max(-1.0, self.reputation - 0.15)
        elif action == DiplomaticAction.ESCALATE:
            self.reputation = max(-1.0, self.reputation - 0.2)
    
    def get_trust(self, other_id: str) -> float:
        """获取对特定 agent 的信任度"""
        return self.trust_memory.get(other_id, 0.0)
    
    def update_trust(self, other_id: str, delta: float):
        """更新对特定 agent 的信任度"""
        current = self.trust_memory.get(other_id, 0.0)
        self.trust_memory[other_id] = max(-1.0, min(1.0, current + delta))

class GameTheoryDiplomacy:
    """博弈论外交系统"""
    
    def __init__(self):
        self.agents: Dict[str, AgentDiplomaticState] = {}
        self.conflict_levels: Dict[str, ConflictLevel] = {}  # (a|b) -> level
        self.payoff_matrix = PayoffMatrix()
        self.round = 0
        
        # 外交行动成本
        self.action_costs = {
            DiplomaticAction.COOPERATE: 2.0,      # 合作需要投入
            DiplomaticAction.DEFECT: 1.0,         # 背叛成本低
            DiplomaticAction.DETER: 5.0,          # 威慑需要军力展示
            DiplomaticAction.ESCALATE: 8.0,       # 升级代价高
            DiplomaticAction.NEGOTIATE: 3.0,      # 谈判需要时间
            DiplomaticAction.SANCTION: 4.0,       # 制裁有经济成本
            DiplomaticAction.APPEASE: 3.0,        # 绥靖有政治成本
            DiplomaticAction.IGNORE: 0.0,         # 无视无成本
        }
        
        # 冲突升级阈值
        self.escalation_thresholds = {
            ConflictLevel.PEACE: -0.3,           # 信任度低于此则紧张
            ConflictLevel.TENSION: -0.6,         # 信任度低于此则危机
            ConflictLevel.CRISIS: -0.8,        # 信任度低于此则制裁
            ConflictLevel.SANCTIONS: -0.9,     # 信任度低于此则代理人战争
        }
    
    def initialize_agents(self, agent_configs: List[Dict]):
        """初始化 agent 外交状态"""
        for config in agent_configs:
            agent_id = str(config.get("agent_id", ""))
            # 根据角色设定初始属性
            stance = config.get("stance", "neutral")
            sentiment = config.get("sentiment_bias", 0.0)
            
            aggression = 0.5
            cooperation = 0.3
            
            if stance == "opposing":
                aggression = 0.7
                cooperation = 0.1
            elif stance == "supportive":
                aggression = 0.3
                cooperation = 0.6
            elif stance == "neutral":
                aggression = 0.4 + sentiment * 0.3
                cooperation = 0.4 - sentiment * 0.2
            
            self.agents[agent_id] = AgentDiplomaticState(
                agent_id=agent_id,
                aggression=aggression,
                cooperation_bias=cooperation,
                reputation=0.0,
                credibility=1.0,
                resources=100.0 + random.uniform(-10, 10)
            )
        
        # 初始化冲突级别
        agent_ids = list(self.agents.keys())
        for i, a in enumerate(agent_ids):
            for b in agent_ids[i+1:]:
                key = f"{min(a, b)}|{max(a, b)}"
                self.conflict_levels[key] = ConflictLevel.PEACE
    
    def calculate_diplomatic_outcome(self, agent_a: str, agent_b: str,
                                   action_a: DiplomaticAction, 
                                   action_b: DiplomaticAction) -> Dict:
        """计算外交结果 - 核心博弈论逻辑"""
        
        state_a = self.agents[agent_a]
        state_b = self.agents[agent_b]
        
        # 1. 计算收益
        payoff_a, payoff_b = self.payoff_matrix.get_payoff(action_a, action_b)
        
        # 2. 加入声誉影响
        reputation_factor_a = 1.0 + state_a.reputation * 0.2
        reputation_factor_b = 1.0 + state_b.reputation * 0.2
        
        payoff_a *= reputation_factor_a
        payoff_b *= reputation_factor_b
        
        # 3. 加入资源成本
        cost_a = self.action_costs.get(action_a, 0.0)
        cost_b = self.action_costs.get(action_b, 0.0)
        
        # 资源不足时成本增加
        if state_a.resources < cost_a * 2:
            cost_a *= 1.5
        if state_b.resources < cost_b * 2:
            cost_b *= 1.5
        
        net_payoff_a = payoff_a - cost_a
        net_payoff_b = payoff_b - cost_b
        
        # 4. 判断结果
        success = self._determine_success(action_a, action_b, state_a, state_b)
        
        # 5. 更新信任
        trust_delta = self._calculate_trust_delta(action_a, action_b, success)
        state_a.update_trust(agent_b, trust_delta)
        state_b.update_trust(agent_a, trust_delta)
        
        # 6. 更新声誉
        state_a.update_reputation(action_a, success)
        state_b.update_reputation(action_b, success)
        
        # 7. 更新冲突级别
        self._update_conflict_level(agent_a, agent_b, action_a, action_b, success)
        
        # 8. 记录历史
        history_a = DiplomaticHistory(
            round=self.round,
            action=action_a,
            target=agent_b,
            success=success,
            payoff=net_payoff_a,
            betrayal=(action_a == DiplomaticAction.DEFECT and action_b == DiplomaticAction.COOPERATE)
        )
        history_b = DiplomaticHistory(
            round=self.round,
            action=action_b,
            target=agent_a,
            success=success,
            payoff=net_payoff_b,
            betrayal=(action_b == DiplomaticAction.DEFECT and action_a == DiplomaticAction.COOPERATE)
        )
        state_a.history.append(history_a)
        state_b.history.append(history_b)
        
        # 9. 消耗资源
        state_a.resources -= cost_a
        state_b.resources -= cost_b
        
        # 10. 战争疲劳
        if action_a == DiplomaticAction.ESCALATE or action_b == DiplomaticAction.ESCALATE:
            state_a.war_exhaustion += 0.1
            state_b.war_exhaustion += 0.1
        
        return {
            "success": success,
            "payoff_a": net_payoff_a,
            "payoff_b": net_payoff_b,
            "trust_delta": trust_delta,
            "conflict_level": self.conflict_levels[f"{min(agent_a, agent_b)}|{max(agent_a, agent_b)}"].value,
            "betrayal_by_a": history_a.betrayal,
            "betrayal_by_b": history_b.betrayal,
        }
    
    def _determine_success(self, action_a: DiplomaticAction, action_b: DiplomaticAction,
                          state_a: AgentDiplomaticState, 
                          state_b: AgentDiplomaticState) -> bool:
        """判断外交是否成功"""
        # 双方都合作 → 成功
        if action_a == DiplomaticAction.COOPERATE and action_b == DiplomaticAction.COOPERATE:
            return True
        
        # 一方合作一方背叛 → 背叛方"成功"，但关系恶化
        if action_a == DiplomaticAction.COOPERATE and action_b in [DiplomaticAction.DEFECT, DiplomaticAction.ESCALATE]:
            return False  # 合作方被利用
        if action_b == DiplomaticAction.COOPERATE and action_a in [DiplomaticAction.DEFECT, DiplomaticAction.ESCALATE]:
            return False
        
        # 双方都强硬 → 看实力和可信度
        if action_a in [DiplomaticAction.DETER, DiplomaticAction.ESCALATE] and \
           action_b in [DiplomaticAction.DETER, DiplomaticAction.ESCALATE]:
            # 可信度 + 资源决定
            power_a = state_a.credibility * state_a.resources
            power_b = state_b.credibility * state_b.resources
            # 实力相近 → 僵局/双输
            if abs(power_a - power_b) < 20:
                return False  # 僵局
            else:
                return power_a > power_b  # 强者"成功"
        
        # 谈判 → 需要双方都有意愿
        if action_a == DiplomaticAction.NEGOTIATE or action_b == DiplomaticAction.NEGOTIATE:
            willingness = (state_a.cooperation_bias + state_b.cooperation_bias) / 2
            return random.random() < willingness
        
        # 绥靖 → 看对方是否接受
        if action_a == DiplomaticAction.APPEASE:
            return state_b.aggression < 0.7  # 对方不太激进则接受
        if action_b == DiplomaticAction.APPEASE:
            return state_a.aggression < 0.7
        
        return False
    
    def _calculate_trust_delta(self, action_a: DiplomaticAction, 
                              action_b: DiplomaticAction, success: bool) -> float:
        """计算信任度变化"""
        delta = 0.0
        
        if success:
            delta += 0.15  # 成功合作增加信任
        else:
            delta -= 0.1   # 失败减少信任
        
        # 背叛严重损害信任
        if action_a == DiplomaticAction.DEFECT and action_b == DiplomaticAction.COOPERATE:
            delta -= 0.3
        if action_b == DiplomaticAction.DEFECT and action_a == DiplomaticAction.COOPERATE:
            delta -= 0.3
        
        # 升级也损害信任
        if action_a == DiplomaticAction.ESCALATE or action_b == DiplomaticAction.ESCALATE:
            delta -= 0.2
        
        # 合作建立信任
        if action_a == DiplomaticAction.COOPERATE and action_b == DiplomaticAction.COOPERATE:
            delta += 0.2
        
        return delta
    
    def _update_conflict_level(self, agent_a: str, agent_b: str,
                              action_a: DiplomaticAction, action_b: DiplomaticAction,
                              success: bool):
        """更新冲突级别"""
        key = f"{min(agent_a, agent_b)}|{max(agent_a, agent_b)}"
        current = self.conflict_levels[key]
        
        trust = (self.agents[agent_a].get_trust(agent_b) + 
                self.agents[agent_b].get_trust(agent_a)) / 2
        
        # 根据信任度和行动升级/降级
        if success and action_a == DiplomaticAction.COOPERATE and action_b == DiplomaticAction.COOPERATE:
            # 成功合作 → 降级
            if current == ConflictLevel.TENSION:
                self.conflict_levels[key] = ConflictLevel.PEACE
            elif current == ConflictLevel.CRISIS:
                self.conflict_levels[key] = ConflictLevel.TENSION
            elif current == ConflictLevel.SANCTIONS:
                self.conflict_levels[key] = ConflictLevel.CRISIS
        
        elif not success and (action_a in [DiplomaticAction.DEFECT, DiplomaticAction.ESCALATE] or
                             action_b in [DiplomaticAction.DEFECT, DiplomaticAction.ESCALATE]):
            # 失败且有人背叛/升级 → 升级
            if current == ConflictLevel.PEACE:
                self.conflict_levels[key] = ConflictLevel.TENSION
            elif current == ConflictLevel.TENSION:
                self.conflict_levels[key] = ConflictLevel.CRISIS
            elif current == ConflictLevel.CRISIS:
                self.conflict_levels[key] = ConflictLevel.SANCTIONS
            elif current == ConflictLevel.SANCTIONS:
                self.conflict_levels[key] = ConflictLevel.PROXY_WAR
            elif current == ConflictLevel.PROXY_WAR:
                self.conflict_levels[key] = ConflictLevel.LIMITED_WAR
            elif current == ConflictLevel.LIMITED_WAR:
                self.conflict_levels[key] = ConflictLevel.TOTAL_WAR
    
    def get_agent_strategy(self, agent_id: str, opponent_id: str,
                          available_actions: List[DiplomaticAction]) -> DiplomaticAction:
        """为 agent 选择最优策略 - 基于博弈论"""
        state = self.agents[agent_id]
        opponent = self.agents[opponent_id]
        
        # 1. 获取历史模式
        opponent_history = [h for h in opponent.history if h.target == agent_id]
        opponent_pattern = self._analyze_pattern(opponent_history)
        
        # 2. 计算期望收益
        expected_payoffs = {}
        for action in available_actions:
            # 预测对方行动
            predicted_opponent_action = self._predict_opponent_action(
                opponent, agent_id, opponent_pattern
            )
            
            # 计算期望收益
            payoff, _ = self.payoff_matrix.get_payoff(action, predicted_opponent_action)
            
            # 加入成本
            cost = self.action_costs.get(action, 0.0)
            
            # 加入声誉影响
            reputation_impact = 0.0
            if action == DiplomaticAction.COOPERATE:
                reputation_impact = 0.1
            elif action == DiplomaticAction.DEFECT:
                reputation_impact = -0.15
            
            # 加入战争疲劳
            exhaustion_penalty = 0.0
            if action == DiplomaticAction.ESCALATE:
                exhaustion_penalty = -state.war_exhaustion * 2.0
            
            expected_payoffs[action] = (
                payoff - cost + reputation_impact + exhaustion_penalty
            )
        
        # 3. 选择最优策略（加入随机性避免确定性）
        max_payoff = max(expected_payoffs.values())
        best_actions = [a for a, p in expected_payoffs.items() if p >= max_payoff - 0.5]
        
        # 根据 agent 性格加入倾向
        if state.aggression > 0.6 and DiplomaticAction.ESCALATE in best_actions:
            return DiplomaticAction.ESCALATE
        elif state.cooperation_bias > 0.5 and DiplomaticAction.COOPERATE in best_actions:
            return DiplomaticAction.COOPERATE
        
        return random.choice(best_actions)
    
    def _analyze_pattern(self, history: List[DiplomaticHistory]) -> Dict:
        """分析对手历史行为模式"""
        if not history:
            return {"cooperation_rate": 0.3, "betrayal_rate": 0.2, "escalation_rate": 0.2}
        
        total = len(history)
        cooperate = sum(1 for h in history if h.action == DiplomaticAction.COOPERATE)
        betray = sum(1 for h in history if h.betrayal)
        escalate = sum(1 for h in history if h.action == DiplomaticAction.ESCALATE)
        
        return {
            "cooperation_rate": cooperate / total,
            "betrayal_rate": betray / total,
            "escalation_rate": escalate / total,
        }
    
    def _predict_opponent_action(self, opponent: AgentDiplomaticState,
                                my_id: str, pattern: Dict) -> DiplomaticAction:
        """预测对手行动"""
        # 基于历史模式预测
        rand = random.random()
        
        if rand < pattern["cooperation_rate"]:
            return DiplomaticAction.COOPERATE
        elif rand < pattern["cooperation_rate"] + pattern["escalation_rate"]:
            return DiplomaticAction.ESCALATE
        elif rand < pattern["cooperation_rate"] + pattern["escalation_rate"] + pattern["betrayal_rate"]:
            return DiplomaticAction.DEFECT
        else:
            return DiplomaticAction.DETER
    
    def get_conflict_summary(self) -> Dict:
        """获取冲突状态摘要"""
        summary = {
            "total_agents": len(self.agents),
            "peace_count": 0,
            "tension_count": 0,
            "crisis_count": 0,
            "sanctions_count": 0,
            "proxy_war_count": 0,
            "limited_war_count": 0,
            "total_war_count": 0,
            "relationships": {}
        }
        
        for key, level in self.conflict_levels.items():
            summary[f"{level.value}_count"] += 1
            summary["relationships"][key] = level.value
        
        return summary
    
    def advance_round(self):
        """进入下一轮"""
        self.round += 1
        
        # 恢复资源
        for agent in self.agents.values():
            agent.resources = min(200.0, agent.resources + 5.0)
            agent.war_exhaustion = max(0.0, agent.war_exhaustion - 0.05)
            
            # 可信度随时间恢复
            if agent.credibility < 1.0:
                agent.credibility = min(1.0, agent.credibility + 0.02)

# 使用示例
if __name__ == "__main__":
    # 创建博弈论外交系统
    diplomacy = GameTheoryDiplomacy()
    
    # 配置 agent
    agent_configs = [
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "china", "stance": "neutral", "sentiment_bias": 0.0},
        {"agent_id": "russia", "stance": "opposing", "sentiment_bias": 0.3},
        {"agent_id": "iran", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "eu", "stance": "neutral", "sentiment_bias": 0.0},
    ]
    
    diplomacy.initialize_agents(agent_configs)
    
    # 模拟几轮外交
    for round_num in range(10):
        print(f"\n=== Round {round_num} ===")
        
        # USA vs China
        action_usa = diplomacy.get_agent_strategy("usa", "china", 
            [DiplomaticAction.COOPERATE, DiplomaticAction.DETER, DiplomaticAction.ESCALATE])
        action_china = diplomacy.get_agent_strategy("china", "usa",
            [DiplomaticAction.COOPERATE, DiplomaticAction.DETER, DiplomaticAction.NEGOTIATE])
        
        result = diplomacy.calculate_diplomatic_outcome("usa", "china", action_usa, action_china)
        print(f"USA({action_usa.value}) vs China({action_china.value}): {result}")
        
        diplomacy.advance_round()
    
    print("\n=== Final Conflict Summary ===")
    print(diplomacy.get_conflict_summary())
