"""
Enhanced Diplomacy Integration - 增强外交集成
将博弈论外交系统接入 MiroFish
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any

# 导入博弈论外交系统
try:
    from game_theory_diplomacy import (
        GameTheoryDiplomacy, DiplomaticAction, ConflictLevel,
        AgentDiplomaticState
    )
    DIPLOMACY_AVAILABLE = True
except ImportError:
    DIPLOMACY_AVAILABLE = False
    print("[DiplomacyIntegration] 博弈论外交系统未找到")

class DiplomacyIntegration:
    """外交系统集成器"""
    
    def __init__(self, simulation_dir: str, config: Dict[str, Any]):
        self.simulation_dir = simulation_dir
        self.config = config
        self.enabled = DIPLOMACY_AVAILABLE
        
        if not self.enabled:
            return
        
        self.diplomacy = GameTheoryDiplomacy()
        self.initialized = False
        
        # 配置
        self.enable_game_theory = config.get("enable_game_theory_diplomacy", True)
        self.escalation_ladder = config.get("escalation_ladder", True)
        self.reputation_system = config.get("reputation_system", True)
        
        print("[DiplomacyIntegration] 博弈论外交集成器已初始化")
    
    def initialize(self, agent_configs: List[Dict]):
        """初始化外交系统"""
        if not self.enabled or not self.enable_game_theory:
            return
        
        # 转换配置
        diplomacy_configs = []
        for config in agent_configs:
            diplomacy_configs.append({
                "agent_id": str(config.get("agent_id", "")),
                "stance": config.get("stance", "neutral"),
                "sentiment_bias": config.get("sentiment_bias", 0.0),
            })
        
        self.diplomacy.initialize_agents(diplomacy_configs)
        self.initialized = True
        
        print(f"[DiplomacyIntegration] 已初始化 {len(diplomacy_configs)} 个 agent 的外交状态")
    
    def process_diplomatic_event(self, event: Dict, round_num: int) -> Dict:
        """处理外交事件 - 使用博弈论机制"""
        if not self.enabled or not self.initialized:
            return {"status": "disabled", "result": None}
        
        # 提取事件信息
        actor = event.get("actor", "")
        target = event.get("target", "")
        event_type = event.get("event_type", "")
        
        # 映射到博弈论行动
        action = self._map_event_to_action(event_type)
        
        # 获取目标方的预测行动
        target_action = self.diplomacy.get_agent_strategy(
            target, actor,
            [DiplomaticAction.COOPERATE, DiplomaticAction.DETER, 
             DiplomaticAction.ESCALATE, DiplomaticAction.DEFECT]
        )
        
        # 计算外交结果
        result = self.diplomacy.calculate_diplomatic_outcome(
            actor, target, action, target_action
        )
        
        # 根据冲突级别决定是否升级为战争
        conflict_level = result.get("conflict_level", "peace")
        war_triggered = self._should_trigger_war(conflict_level)
        
        return {
            "status": "processed",
            "result": result,
            "war_triggered": war_triggered,
            "conflict_level": conflict_level,
            "actor_action": action.value,
            "target_action": target_action.value,
        }
    
    def _map_event_to_action(self, event_type: str) -> DiplomaticAction:
        """将事件类型映射到博弈论行动"""
        mapping = {
            "STATEMENT": DiplomaticAction.DETER,
            "CONDITIONS": DiplomaticAction.NEGOTIATE,
            "BREAK": DiplomaticAction.DEFECT,
            "ULTIMATUM": DiplomaticAction.ESCALATE,
            "SANCTION": DiplomaticAction.SANCTION,
            "TRADE": DiplomaticAction.COOPERATE,
            "MEETING": DiplomaticAction.NEGOTIATE,
            "WITHDRAW": DiplomaticAction.APPEASE,
        }
        return mapping.get(event_type, DiplomaticAction.DETER)
    
    def _should_trigger_war(self, conflict_level: str) -> bool:
        """根据冲突级别判断是否触发战争"""
        if not self.escalation_ladder:
            # 旧模式：直接战争
            return conflict_level in ["proxy_war", "limited_war", "total_war"]
        
        # 新模式：升级阶梯
        war_levels = ["limited_war", "total_war"]
        return conflict_level in war_levels
    
    def get_diplomatic_context(self, agent_id: str) -> Dict:
        """获取 agent 的外交上下文"""
        if not self.enabled or not self.initialized:
            return {}
        
        state = self.diplomacy.agents.get(agent_id)
        if not state:
            return {}
        
        # 构建上下文供 LLM 使用
        relationships = {}
        for other_id, other_state in self.diplomacy.agents.items():
            if other_id != agent_id:
                trust = state.get_trust(other_id)
                key = f"{min(agent_id, other_id)}|{max(agent_id, other_id)}"
                conflict = self.diplomacy.conflict_levels.get(key, ConflictLevel.PEACE)
                
                relationships[other_id] = {
                    "trust": trust,
                    "conflict_level": conflict.value,
                    "their_reputation": other_state.reputation,
                }
        
        return {
            "my_reputation": state.reputation,
            "my_credibility": state.credibility,
            "my_resources": state.resources,
            "war_exhaustion": state.war_exhaustion,
            "relationships": relationships,
            "history": [
                {
                    "round": h.round,
                    "action": h.action.value,
                    "target": h.target,
                    "success": h.success,
                    "betrayal": h.betrayal,
                }
                for h in state.history[-5:]  # 最近5条
            ],
        }
    
    def advance_round(self):
        """进入下一轮"""
        if self.enabled and self.initialized:
            self.diplomacy.advance_round()
    
    def get_summary(self) -> Dict:
        """获取外交系统摘要"""
        if not self.enabled or not self.initialized:
            return {"status": "disabled"}
        
        return {
            "status": "active",
            "round": self.diplomacy.round,
            "conflict_summary": self.diplomacy.get_conflict_summary(),
            "agent_states": {
                agent_id: {
                    "reputation": state.reputation,
                    "resources": state.resources,
                    "war_exhaustion": state.war_exhaustion,
                }
                for agent_id, state in self.diplomacy.agents.items()
            },
        }

# 使用示例
if __name__ == "__main__":
    # 创建集成器
    integration = DiplomacyIntegration("/tmp/test", {
        "enable_game_theory_diplomacy": True,
        "escalation_ladder": True,
        "reputation_system": True,
    })
    
    # 配置 agent
    agent_configs = [
        {"agent_id": "usa", "stance": "opposing", "sentiment_bias": -0.3},
        {"agent_id": "china", "stance": "neutral", "sentiment_bias": 0.0},
        {"agent_id": "russia", "stance": "opposing", "sentiment_bias": 0.3},
    ]
    
    integration.initialize(agent_configs)
    
    # 模拟外交事件
    test_event = {
        "actor": "usa",
        "target": "china",
        "event_type": "ULTIMATUM",
    }
    
    result = integration.process_diplomatic_event(test_event, 1)
    print(f"外交结果: {result}")
    
    # 获取上下文
    context = integration.get_diplomatic_context("usa")
    print(f"USA 外交上下文: {context}")
