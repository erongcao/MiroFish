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

# 导入扩展模块
try:
    from alliance_system import AllianceSystem, AllianceType
    ALLIANCE_AVAILABLE = True
except ImportError:
    ALLIANCE_AVAILABLE = False

try:
    from sanction_network import SanctionNetwork, SanctionType, SanctionSeverity
    SANCTION_AVAILABLE = True
except ImportError:
    SANCTION_AVAILABLE = False

try:
    from third_party_mediation import ThirdPartyMediation, MediatorType
    MEDIATION_AVAILABLE = True
except ImportError:
    MEDIATION_AVAILABLE = False

try:
    from nuclear_deterrence import NuclearDeterrence, NuclearStatus
    NUCLEAR_AVAILABLE = True
except ImportError:
    NUCLEAR_AVAILABLE = False

try:
    from domestic_politics import DomesticPolitics, PoliticalSystem
    DOMESTIC_AVAILABLE = True
except ImportError:
    DOMESTIC_AVAILABLE = False

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
        
        # 初始化扩展模块
        self.alliance_system = AllianceSystem() if ALLIANCE_AVAILABLE else None
        self.sanction_network = SanctionNetwork() if SANCTION_AVAILABLE else None
        self.mediation = ThirdPartyMediation() if MEDIATION_AVAILABLE else None
        self.nuclear = NuclearDeterrence() if NUCLEAR_AVAILABLE else None
        self.domestic = DomesticPolitics() if DOMESTIC_AVAILABLE else None
        
        print("[DiplomacyIntegration] 博弈论外交集成器已初始化")
        if self.alliance_system:
            print("[DiplomacyIntegration] 联盟系统已加载")
        if self.sanction_network:
            print("[DiplomacyIntegration] 制裁网络已加载")
        if self.mediation:
            print("[DiplomacyIntegration] 调解系统已加载")
        if self.nuclear:
            print("[DiplomacyIntegration] 核威慑系统已加载")
        if self.domestic:
            print("[DiplomacyIntegration] 国内政治系统已加载")
    
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
        
        # 初始化扩展模块
        if self.domestic:
            for config in agent_configs:
                agent_id = str(config.get("agent_id", ""))
                system_str = config.get("political_system", "democracy")
                system = getattr(PoliticalSystem, system_str.upper(), PoliticalSystem.DEMOCRACY)
                approval = config.get("initial_approval", 0.5)
                self.domestic.initialize_agent(agent_id, system, approval)
        
        if self.nuclear:
            for config in agent_configs:
                agent_id = str(config.get("agent_id", ""))
                warheads = config.get("nuclear_warheads", 0)
                if warheads > 0:
                    self.nuclear.register_nuclear_power(
                        agent_id,
                        warheads=warheads,
                        delivery_systems=config.get("nuclear_delivery", 0),
                        second_strike=config.get("nuclear_second_strike", False),
                        missile_defense=config.get("missile_defense", 0.0),
                        no_first_use=config.get("no_first_use", False),
                    )
        
        if self.mediation:
            for config in agent_configs:
                agent_id = str(config.get("agent_id", ""))
                mediator_type = config.get("mediator_type")
                if mediator_type:
                    mt = getattr(MediatorType, mediator_type.upper(), MediatorType.NEUTRAL)
                    self.mediation.register_mediator(
                        agent_id, mt,
                        credibility=config.get("mediator_credibility", 0.5),
                        power=config.get("mediator_power", 0.5),
                        region=config.get("region"),
                    )
        
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
        
        # 检查核威慑
        nuclear_result = None
        if war_triggered and self.nuclear:
            nuclear_result = self.nuclear.check_nuclear_escalation(
                actor, target, conflict_level
            )
            if nuclear_result.get("deterrence_effective"):
                war_triggered = False
        
        # 检查集体防御
        collective_defenders = []
        if war_triggered and self.alliance_system:
            collective_defenders = self.alliance_system.check_collective_defense(
                target, actor
            )
        
        # 检查国内政治约束
        domestic_constraint = None
        if self.domestic:
            constraint = self.domestic.get_political_constraint(actor, "war")
            if constraint < -0.3:
                war_triggered = False
            domestic_constraint = constraint
        
        return {
            "status": "processed",
            "result": result,
            "war_triggered": war_triggered,
            "conflict_level": conflict_level,
            "actor_action": action.value,
            "target_action": target_action.value,
            "nuclear_deterrence": nuclear_result,
            "collective_defenders": collective_defenders,
            "domestic_constraint": domestic_constraint,
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
            
            # 更新扩展模块
            if self.alliance_system:
                trust_levels = {
                    aid: {oid: state.get_trust(oid) 
                          for oid in self.diplomacy.agents if oid != aid}
                    for aid, state in self.diplomacy.agents.items()
                }
                self.alliance_system.update_alliances(
                    trust_levels, self.diplomacy.round
                )
            
            if self.sanction_network:
                economies = {
                    aid: state.resources 
                    for aid, state in self.diplomacy.agents.items()
                }
                self.sanction_network.update_sanctions(economies, self.diplomacy.round)
            
            if self.domestic:
                self.domestic.advance_round()
    
    def propose_alliance(self, proposer: str, targets: List[str],
                        alliance_type: str, round_num: int) -> Optional[Dict]:
        """提议建立同盟"""
        if not self.alliance_system:
            return None
        
        atype = getattr(AllianceType, alliance_type.upper(), AllianceType.DEFENSIVE)
        trust_levels = {
            aid: {oid: state.get_trust(oid) 
                  for oid in self.diplomacy.agents if oid != aid}
            for aid, state in self.diplomacy.agents.items()
        }
        
        alliance = self.alliance_system.propose_alliance(
            proposer, targets, atype, trust_levels, round_num
        )
        
        return alliance.to_dict() if alliance else None
    
    def impose_sanction(self, imposers: List[str], target: str,
                       sanction_type: str, severity: str,
                       round_num: int) -> Optional[Dict]:
        """实施制裁"""
        if not self.sanction_network:
            return None
        
        stype = getattr(SanctionType, sanction_type.upper(), SanctionType.TRADE)
        sev = getattr(SanctionSeverity, severity.upper(), SanctionSeverity.MODERATE)
        economies = {
            aid: state.resources 
            for aid, state in self.diplomacy.agents.items()
        }
        
        sanction = self.sanction_network.impose_sanction(
            imposers, target, stype, sev, economies, round_num
        )
        
        return sanction.to_dict() if sanction else None
    
    def attempt_mediation(self, mediator_id: str, parties: List[str],
                         round_num: int) -> Optional[Dict]:
        """尝试调解"""
        if not self.mediation:
            return None
        
        trust_levels = {
            aid: self.diplomacy.agents[aid].get_trust(pid) if aid in self.diplomacy.agents else 0.0
            for aid in parties for pid in parties if pid != aid
        }
        
        # 获取冲突级别
        key = f"{min(parties[0], parties[1])}|{max(parties[0], parties[1])}"
        conflict = self.diplomacy.conflict_levels.get(key, ConflictLevel.PEACE)
        
        attempt = self.mediation.attempt_mediation(
            mediator_id, parties, conflict.value, trust_levels, round_num
        )
        
        return attempt.to_dict() if attempt else None
    
    def get_enhanced_context(self, agent_id: str) -> Dict:
        """获取增强的外交上下文（包含所有扩展模块）"""
        base_context = self.get_diplomatic_context(agent_id)
        
        if self.alliance_system:
            base_context["alliances"] = self.alliance_system.get_agent_alliance_context(agent_id)
        
        if self.sanction_network:
            base_context["sanctions"] = self.sanction_network.get_sanction_context(agent_id)
        
        if self.mediation:
            base_context["mediation"] = self.mediation.get_mediation_context(agent_id)
        
        if self.nuclear:
            base_context["nuclear"] = self.nuclear.get_nuclear_context(agent_id)
        
        if self.domestic:
            base_context["domestic"] = self.domestic.get_context_for_decision(agent_id)
        
        return base_context
    
    def get_summary(self) -> Dict:
        """获取外交系统摘要"""
        if not self.enabled or not self.initialized:
            return {"status": "disabled"}
        
        summary = {
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
        
        if self.alliance_system:
            summary["alliances"] = self.alliance_system.get_summary()
        
        if self.sanction_network:
            summary["sanctions"] = self.sanction_network.get_summary()
        
        if self.mediation:
            summary["mediation"] = self.mediation.get_summary()
        
        if self.nuclear:
            summary["nuclear_powers"] = len([a for a in self.nuclear.arsenals.values() if a.warheads > 0])
        
        if self.domestic:
            summary["domestic"] = self.domestic.get_summary()
        
        return summary

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
