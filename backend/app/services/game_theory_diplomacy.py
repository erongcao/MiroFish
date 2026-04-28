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
        
        # 10. 战争疲劳 - 增加升级冲突的疲劳值
        if action_a == DiplomaticAction.ESCALATE or action_b == DiplomaticAction.ESCALATE:
            state_a.war_exhaustion += 0.25
            state_b.war_exhaustion += 0.25
        elif action_a == DiplomaticAction.DEFECT or action_b == DiplomaticAction.DEFECT:
            state_a.war_exhaustion += 0.1
            state_b.war_exhaustion += 0.1
        
        # 战争状态下持续增加疲劳
        key = f"{min(agent_a, agent_b)}|{max(agent_a, agent_b)}"
        if self.conflict_levels[key] in [ConflictLevel.PROXY_WAR, 
                                          ConflictLevel.LIMITED_WAR, 
                                          ConflictLevel.TOTAL_WAR]:
            state_a.war_exhaustion += 0.15
            state_b.war_exhaustion += 0.15
        
        return {
            "success": success,
            "payoff_a": net_payoff_a,
            "payoff_b": net_payoff_b,
            "cost_a": cost_a,
            "cost_b": cost_b,
            "trust_delta": trust_delta,
            "conflict_level": self.conflict_levels[key].value,
            "action_a": action_a,
            "action_b": action_b
        }
    
    def _determine_success(self, action_a: DiplomaticAction, 
                          action_b: DiplomaticAction,
                          state_a: AgentDiplomaticState,
                          state_b: AgentDiplomaticState) -> bool:
        """判断行动是否成功"""
        # 简单的成功判断逻辑
        if action_a == DiplomaticAction.COOPERATE and action_b == DiplomaticAction.COOPERATE:
            return True
        elif action_a == DiplomaticAction.ESCALATE and state_a.resources > state_b.resources:
            return True
        elif action_b == DiplomaticAction.ESCALATE and state_b.resources > state_a.resources:
            return False
        elif action_a == DiplomaticAction.DEFECT and action_b == DiplomaticAction.COOPERATE:
            return True
        elif action_b == DiplomaticAction.DEFECT and action_a == DiplomaticAction.COOPERATE:
            return False
        else:
            # 随机因素
            return random.random() > 0.5
    
    def _calculate_trust_delta(self, action_a: DiplomaticAction, 
                              action_b: DiplomaticAction,
                              success: bool) -> float:
        """计算信任度变化"""
        if action_a == DiplomaticAction.COOPERATE and action_b == DiplomaticAction.COOPERATE:
            return 0.2 if success else -0.1
        elif action_a == DiplomaticAction.DEFECT or action_b == DiplomaticAction.DEFECT:
            return -0.3
        elif action_a == DiplomaticAction.ESCALATE or action_b == DiplomaticAction.ESCALATE:
            return -0.4
        else:
            return 0.0
    
    def _update_conflict_level(self, agent_a: str, agent_b: str,
                                action_a: DiplomaticAction, action_b: DiplomaticAction,
                                success: bool):
        """更新冲突级别 - 考虑美国国内政治特点"""
        key = f"{min(agent_a, agent_b)}|{max(agent_a, agent_b)}"
        current = self.conflict_levels[key]
        
        trust = (self.agents[agent_a].get_trust(agent_b) + 
                self.agents[agent_b].get_trust(agent_a)) / 2
        
        # 获取国家信息（从agent_id推断）
        country_a = self._get_country(agent_a)
        country_b = self._get_country(agent_b)
        
        # 美国国内政治特殊处理：同国Agent冲突升级更慢
        if country_a == country_b == "usa":
            # 美国国内有强大的制度整合力
            # 冲突升级需要更多轮次
            escalation_resistance = 0.6  # 60%阻力
            
            # 只有当双方都选择escalate时才升级
            if not (action_a == DiplomaticAction.ESCALATE and action_b == DiplomaticAction.ESCALATE):
                # 单方escalate不会导致升级
                return
            
            # 随机决定是否升级（模拟国内政治阻力）
            if random.random() > escalation_resistance:
                return  # 政治阻力阻止升级
        
        # 标准冲突升级逻辑
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
    
    def _get_country(self, agent_id: str) -> str:
        """从agent_id推断国家"""
        if agent_id.startswith("us_") or agent_id in ["trump_president", "pompeo_state", "mnuchin_treasury", "esper_defense"]:
            return "usa"
        elif agent_id.startswith("cn_") or agent_id in ["xi_president", "yang_foreign", "wei_military"]:
            return "china"
        elif agent_id.startswith("ru_") or agent_id in ["putin_president", "shoigu_defense", "lavrov_foreign"]:
            return "russia"
        elif agent_id.startswith("eu_") or agent_id in ["macron_france", "merkel_germany"]:
            return "eu"
        elif agent_id.startswith("iran_"):
            return "iran"
        elif agent_id.startswith("israel_"):
            return "israel"
        elif agent_id.startswith("saudi_"):
            return "saudi"
        elif agent_id.startswith("india_"):
            return "india"
        elif agent_id.startswith("japan_"):
            return "japan"
        elif agent_id.startswith("uk_"):
            return "uk"
        elif agent_id.startswith("turkey_"):
            return "turkey"
        elif agent_id.startswith("nk_"):
            return "north_korea"
        elif agent_id.startswith("sk_"):
            return "south_korea"
        return "unknown"
    
    def get_agent_strategy(self, agent_id: str, opponent_id: str,
                          available_actions: List[DiplomaticAction]) -> DiplomaticAction:
        """为 agent 选择最优策略 - 基于博弈论"""
        state = self.agents[agent_id]
        opponent_state = self.agents[opponent_id]
        
        # 计算预期收益
        best_action = None
        best_expected_payoff = float('-inf')
        
        for action in available_actions:
            expected_payoff = 0.0
            
            # 预测对手行动
            opponent_action_probs = self._predict_opponent_actions(opponent_id, agent_id)
            
            for opponent_action, prob in opponent_action_probs.items():
                payoff, _ = self.payoff_matrix.get_payoff(action, opponent_action)
                cost = self.action_costs.get(action, 0.0)
                expected_payoff += prob * (payoff - cost)
            
            # 考虑声誉影响
            if action == DiplomaticAction.COOPERATE:
                expected_payoff += state.reputation * 0.5
            elif action == DiplomaticAction.ESCALATE:
                expected_payoff -= state.war_exhaustion * 2.0
            
            if expected_payoff > best_expected_payoff:
                best_expected_payoff = expected_payoff
                best_action = action
        
        return best_action if best_action else DiplomaticAction.COOPERATE
    
    def _predict_opponent_actions(self, opponent_id: str, my_id: str) -> Dict[DiplomaticAction, float]:
        """预测对手行动概率"""
        opponent_state = self.agents[opponent_id]
        
        # 基于历史行为预测
        if not opponent_state.history:
            # 没有历史，均匀分布
            return {
                DiplomaticAction.COOPERATE: 0.3,
                DiplomaticAction.DEFECT: 0.2,
                DiplomaticAction.ESCALATE: 0.2,
                DiplomaticAction.NEGOTIATE: 0.2,
                DiplomaticAction.SANCTION: 0.1
            }
        
        # 统计历史行动频率
        action_counts = defaultdict(int)
        for h in opponent_state.history:
            action_counts[h.action] += 1
        
        total = len(opponent_state.history)
        probs = {}
        for action in DiplomaticAction:
            probs[action] = action_counts.get(action, 0) / total
        
        # 加入一些随机性
        for action in probs:
            probs[action] = 0.7 * probs[action] + 0.3 * 0.2
        
        return probs
    
    def get_conflict_level(self, agent_a: str, agent_b: str) -> ConflictLevel:
        """获取两个 agent 之间的冲突级别"""
        key = f"{min(agent_a, agent_b)}|{max(agent_a, agent_b)}"
        return self.conflict_levels.get(key, ConflictLevel.PEACE)
    
    def get_alliance_value(self, agent_a: str, agent_b: str) -> float:
        """计算联盟价值 (-1 到 1)"""
        state_a = self.agents[agent_a]
        state_b = self.agents[agent_b]
        
        # 基于信任度和历史合作
        trust = (state_a.get_trust(agent_b) + state_b.get_trust(agent_a)) / 2
        
        # 合作历史
        cooperation_count = 0
        for h in state_a.history:
            if h.target == agent_b and h.action == DiplomaticAction.COOPERATE:
                cooperation_count += 1
        
        total_interactions = len([h for h in state_a.history if h.target == agent_b])
        if total_interactions > 0:
            cooperation_rate = cooperation_count / total_interactions
        else:
            cooperation_rate = 0.5
        
        return (trust * 0.6 + cooperation_rate * 0.4)
    
    def next_round(self):
        """进入下一轮"""
        self.round += 1
        
        # 战争疲劳恢复
        for agent in self.agents.values():
            agent.war_exhaustion = max(0.0, agent.war_exhaustion - 0.05)
            # 资源缓慢恢复
            agent.resources = min(200.0, agent.resources + 2.0)
    
    def get_agent_stats(self, agent_id: str) -> Dict:
        """获取 agent 统计信息"""
        state = self.agents.get(agent_id)
        if not state:
            return {}
        
        return {
            "reputation": state.reputation,
            "credibility": state.credibility,
            "aggression": state.aggression,
            "cooperation_bias": state.cooperation_bias,
            "resources": state.resources,
            "war_exhaustion": state.war_exhaustion,
            "history_count": len(state.history)
        }
    
    def get_global_state(self) -> Dict:
        """获取全局状态"""
        total_agents = len(self.agents)
        if total_agents == 0:
            return {}
        
        avg_resources = sum(a.resources for a in self.agents.values()) / total_agents
        avg_war_exhaustion = sum(a.war_exhaustion for a in self.agents.values()) / total_agents
        
        conflict_counts = defaultdict(int)
        for level in self.conflict_levels.values():
            conflict_counts[level.value] += 1
        
        return {
            "round": self.round,
            "total_agents": total_agents,
            "avg_resources": avg_resources,
            "avg_war_exhaustion": avg_war_exhaustion,
            "conflict_distribution": dict(conflict_counts),
            "total_conflicts": len(self.conflict_levels)
        }

# 测试代码
if __name__ == "__main__":
    engine = GameTheoryDiplomacy()
    
    # 创建测试 agents
    configs = [
        {"agent_id": "usa_military", "stance": "opposing"},
        {"agent_id": "usa_economic", "stance": "neutral"},
        {"agent_id": "china_military", "stance": "opposing"},
        {"agent_id": "china_economic", "stance": "supportive"},
    ]
    
    engine.initialize_agents(configs)
    
    # 模拟几轮博弈
    for round_num in range(3):
        print(f"\n=== Round {round_num + 1} ===")
        
        # USA vs China
        action_usa = engine.get_agent_strategy("usa_military", "china_military",
                                               [DiplomaticAction.COOPERATE, DiplomaticAction.ESCALATE])
        action_china = engine.get_agent_strategy("china_military", "usa_military",
                                                [DiplomaticAction.COOPERATE, DiplomaticAction.DETER])
        
        result = engine.calculate_diplomatic_outcome("usa_military", "china_military",
                                                      action_usa, action_china)
        
        print(f"USA: {action_usa.value}, China: {action_china.value}")
        print(f"Result: {result}")
        
        engine.next_round()
    
    print("\nFinal State:")
    print(engine.get_global_state())