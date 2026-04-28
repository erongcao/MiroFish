"""
Enhanced Three-Layer Simulator with Game Theory Diplomacy
增强版三层模拟器 - 集成博弈论外交系统
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.three_layer_simulator import (
    ThreeLayerSimulator, CountryState, DiplomaticState, MilitaryPosture, WarIntensity,
    Strategy, DiplomaticEvent, MilitaryEvent, WarEvent, UNResolution, UNResolutionType,
    FactionType, PoliticalFaction, GameTheoryEngine, DomesticPoliticsSystem,
    InternationalPressureSystem
)

from app.services.game_theory_diplomacy import (
    GameTheoryDiplomacy, DiplomaticAction, ConflictLevel, AgentDiplomaticState
)

class EnhancedThreeLayerSimulator(ThreeLayerSimulator):
    """
    增强版三层模拟器
    在原有基础上集成新的博弈论外交系统
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # 初始化新的博弈论外交系统
        self.diplomacy = GameTheoryDiplomacy()
        
        # 转换国家为外交Agent
        agent_configs = []
        for country_id, country in self.countries.items():
            agent_configs.append({
                "agent_id": country_id,
                "stance": self._get_stance_from_relations(country),
                "sentiment_bias": self._get_sentiment_from_relations(country),
            })
        
        self.diplomacy.initialize_agents(agent_configs)
        
        # 同步初始关系
        for country_id, country in self.countries.items():
            for target_id, relation in country.relations.items():
                if target_id in self.diplomacy.agents:
                    self.diplomacy.agents[country_id].trust_memory[target_id] = relation
        
        print("[EnhancedThreeLayer] 增强版三层模拟器已初始化")
    
    def _get_stance_from_relations(self, country: CountryState) -> str:
        """根据平均关系确定立场"""
        avg_relation = sum(country.relations.values()) / len(country.relations) if country.relations else 0
        if avg_relation < -0.3:
            return "opposing"
        elif avg_relation > 0.3:
            return "supportive"
        return "neutral"
    
    def _get_sentiment_from_relations(self, country: CountryState) -> float:
        """根据平均关系确定情感倾向"""
        avg_relation = sum(country.relations.values()) / len(country.relations) if country.relations else 0
        return avg_relation
    
    def simulate_round(self, media_posts: dict = None) -> dict:
        """
        增强版模拟轮次
        集成新的博弈论外交系统
        """
        self.round += 1
        
        # 调用父类的基本模拟
        round_summary = super().simulate_round(media_posts)
        
        # 使用新的博弈论系统进行外交决策
        self._enhanced_diplomatic_decisions(round_summary)
        
        # 使用新的博弈论系统进行冲突升级判断
        self._enhanced_conflict_escalation(round_summary)
        
        # 更新全局紧张度（基于新的冲突级别）
        self._update_tension_from_conflict_levels()
        
        return round_summary
    
    def _enhanced_diplomatic_decisions(self, round_summary: dict):
        """增强版外交决策"""
        # 为每个国家对生成外交行动
        country_ids = list(self.countries.keys())
        
        for i, actor_id in enumerate(country_ids):
            for target_id in country_ids[i+1:]:
                # 获取当前策略
                actor = self.countries[actor_id]
                target = self.countries[target_id]
                
                # 使用新的博弈论系统选择策略
                action = self.diplomacy.get_agent_strategy(
                    actor_id, target_id,
                    [DiplomaticAction.COOPERATE, DiplomaticAction.DETER, 
                     DiplomaticAction.ESCALATE, DiplomaticAction.DEFECT]
                )
                
                target_action = self.diplomacy.get_agent_strategy(
                    target_id, actor_id,
                    [DiplomaticAction.COOPERATE, DiplomaticAction.DETER,
                     DiplomaticAction.ESCALATE, DiplomaticAction.DEFECT]
                )
                
                # 计算外交结果
                result = self.diplomacy.calculate_diplomatic_outcome(
                    actor_id, target_id, action, target_action
                )
                
                # 根据结果更新关系
                if result['success']:
                    # 成功合作 → 改善关系
                    actor.relations[target_id] = min(1.0, actor.relations.get(target_id, 0) + 0.1)
                    target.relations[actor_id] = min(1.0, target.relations.get(actor_id, 0) + 0.1)
                else:
                    # 失败 → 恶化关系
                    if action in [DiplomaticAction.DEFECT, DiplomaticAction.ESCALATE]:
                        actor.relations[target_id] = max(-1.0, actor.relations.get(target_id, 0) - 0.15)
                        target.relations[actor_id] = max(-1.0, target.relations.get(actor_id, 0) - 0.15)
                
                # 记录外交事件
                if action != DiplomaticAction.COOPERATE or not result['success']:
                    event_name = self._get_event_name_from_action(action)
                    event = DiplomaticEvent(
                        name=event_name,
                        actor=actor_id,
                        target=target_id,
                        event_type=action.value.upper(),
                        description=f"{actor_id}对{target_id}采取{action.value}行动",
                        pressure=0.0,
                        actor_strategy=action.value,
                        target_strategy=target_action.value
                    )
                    self.diplomatic_events.append(event)
                    
                    round_summary["diplomatic_events"].append({
                        "name": event_name,
                        "actor": actor_id,
                        "target": target_id,
                        "type": action.value.upper(),
                        "success": result['success'],
                        "conflict_level": result['conflict_level']
                    })
    
    def _enhanced_conflict_escalation(self, round_summary: dict):
        """增强版冲突升级判断"""
        # 检查所有国家对的冲突级别
        for key, level in self.diplomacy.conflict_levels.items():
            if level in [ConflictLevel.PROXY_WAR, ConflictLevel.LIMITED_WAR, ConflictLevel.TOTAL_WAR]:
                # 冲突升级 → 生成战争事件
                parts = key.split("|")
                if len(parts) == 2:
                    actor_id, target_id = parts
                    
                    # 检查是否已存在战争事件
                    existing = any(
                        w.parties == [actor_id, target_id] or w.parties == [target_id, actor_id]
                        for w in self.war_events
                    )
                    
                    if not existing:
                        intensity = self._conflict_level_to_war_intensity(level)
                        
                        war = WarEvent(
                            name=f"{actor_id}-{target_id}冲突",
                            parties=[actor_id, target_id],
                            intensity=intensity,
                            territory_change={},
                            casualties={actor_id: 0, target_id: 0},
                            description=f"{actor_id}与{target_id}发生{level.value}冲突",
                            cause="博弈论外交失败"
                        )
                        
                        self.war_events.append(war)
                        round_summary["war_events"].append({
                            "name": war.name,
                            "parties": war.parties,
                            "intensity": war.intensity.value,
                            "description": war.description
                        })
                        
                        # 更新国家战争状态
                        if actor_id in self.countries:
                            self.countries[actor_id].war_intensity = intensity
                        if target_id in self.countries:
                            self.countries[target_id].war_intensity = intensity
    
    def _update_tension_from_conflict_levels(self):
        """根据冲突级别更新全局紧张度"""
        tension = 0.0
        
        for key, level in self.diplomacy.conflict_levels.items():
            level_tension = {
                ConflictLevel.PEACE: 0,
                ConflictLevel.TENSION: 10,
                ConflictLevel.CRISIS: 25,
                ConflictLevel.SANCTIONS: 40,
                ConflictLevel.PROXY_WAR: 60,
                ConflictLevel.LIMITED_WAR: 80,
                ConflictLevel.TOTAL_WAR: 100
            }.get(level, 0)
            
            tension = max(tension, level_tension)
        
        # 平滑过渡
        self.global_tension = self.global_tension * 0.7 + tension * 0.3
    
    def _get_event_name_from_action(self, action: DiplomaticAction) -> str:
        """将博弈论行动映射到事件名称"""
        mapping = {
            DiplomaticAction.COOPERATE: "合作倡议",
            DiplomaticAction.DEFECT: "背叛行动",
            DiplomaticAction.DETER: "威慑声明",
            DiplomaticAction.ESCALATE: "升级行动",
            DiplomaticAction.NEGOTIATE: "谈判提议",
            DiplomaticAction.SANCTION: "制裁措施",
            DiplomaticAction.APPEASE: "绥靖政策",
            DiplomaticAction.IGNORE: "无视"
        }
        return mapping.get(action, "未知行动")
    
    def _conflict_level_to_war_intensity(self, level: ConflictLevel) -> WarIntensity:
        """将冲突级别映射到战争强度"""
        mapping = {
            ConflictLevel.PROXY_WAR: WarIntensity.SKIRMISH,
            ConflictLevel.LIMITED_WAR: WarIntensity.LOCAL_WAR,
            ConflictLevel.TOTAL_WAR: WarIntensity.FULL_SCALE
        }
        return mapping.get(level, WarIntensity.SKIRMISH)
    
    def get_enhanced_context(self, agent_id: str) -> dict:
        """获取增强版上下文（供Agent使用）"""
        context = self.get_current_context(agent_id, "")
        
        # 添加博弈论外交上下文
        if agent_id in self.diplomacy.agents:
            diplomatic_state = self.diplomacy.agents[agent_id]
            
            context["diplomatic_state"] = {
                "reputation": diplomatic_state.reputation,
                "credibility": diplomatic_state.credibility,
                "resources": diplomatic_state.resources,
                "war_exhaustion": diplomatic_state.war_exhaustion,
            }
            
            # 添加关系详情
            context["relationships_detail"] = {}
            for other_id, other_state in self.diplomacy.agents.items():
                if other_id != agent_id:
                    key = f"{min(agent_id, other_id)}|{max(agent_id, other_id)}"
                    conflict_level = self.diplomacy.conflict_levels.get(key, ConflictLevel.PEACE)
                    
                    context["relationships_detail"][other_id] = {
                        "trust": diplomatic_state.get_trust(other_id),
                        "conflict_level": conflict_level.value,
                        "their_reputation": other_state.reputation,
                    }
        
        return context

# 使用示例
if __name__ == "__main__":
    config = {
        "simulation_id": "test_enhanced",
        "initial_tension": 40.0
    }
    
    simulator = EnhancedThreeLayerSimulator(config)
    
    # 模拟10轮
    for i in range(10):
        result = simulator.simulate_round()
        print(f"\n=== Round {i+1} ===")
        print(f"Global Tension: {simulator.global_tension:.1f}")
        print(f"Diplomatic Events: {len(result['diplomatic_events'])}")
        print(f"War Events: {len(result['war_events'])}")
        
        # 打印冲突级别
        for key, level in simulator.diplomacy.conflict_levels.items():
            if level != ConflictLevel.PEACE:
                print(f"  {key}: {level.value}")
    
    print("\n=== Final Summary ===")
    print(f"Total War Events: {len(simulator.war_events)}")
    print(f"Total Diplomatic Events: {len(simulator.diplomatic_events)}")
    print(f"Final Tension: {simulator.global_tension:.1f}")
