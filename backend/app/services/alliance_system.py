"""
Alliance System - 联盟机制
多 Agent 联合行动、联盟形成与维护
"""

import random
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

class AllianceType(Enum):
    DEFENSIVE = "defensive"      # 防御同盟 - 受攻击时互助
    OFFENSIVE = "offensive"      # 进攻同盟 - 共同攻击
    ECONOMIC = "economic"        # 经济同盟 - 贸易/制裁
    INTELLIGENCE = "intelligence" # 情报共享
    MULTI = "multi"              # 多边综合同盟

class AllianceStatus(Enum):
    PROPOSED = "proposed"        # 提议中
    ACTIVE = "active"            # 生效中
    STRAINED = "strained"        # 关系紧张
    DISSOLVED = "dissolved"      # 已解散

@dataclass
class Alliance:
    alliance_id: str
    name: str
    alliance_type: AllianceType
    members: Set[str] = field(default_factory=set)
    leader: Optional[str] = None
    formed_round: int = 0
    status: AllianceStatus = AllianceStatus.PROPOSED
    
    # 同盟参数
    mutual_defense: bool = False      # 是否共同防御
    collective_action: bool = False   # 是否集体行动
    trade_bonus: float = 0.0          # 贸易加成
    intel_sharing: bool = False       # 情报共享
    
    # 动态状态
    cohesion: float = 1.0             # 凝聚力 (0-1)
    trust_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    shared_enemies: Set[str] = field(default_factory=set)
    history: List[Dict] = field(default_factory=list)
    
    def add_member(self, agent_id: str, trust_level: float = 0.5):
        """添加成员"""
        if agent_id not in self.members:
            self.members.add(agent_id)
            self.trust_matrix[agent_id] = {}
            for other in self.members:
                if other != agent_id:
                    self.trust_matrix[agent_id][other] = trust_level
                    self.trust_matrix[other][agent_id] = trust_level
    
    def remove_member(self, agent_id: str):
        """移除成员"""
        if agent_id in self.members:
            self.members.remove(agent_id)
            if agent_id in self.trust_matrix:
                del self.trust_matrix[agent_id]
            for other in self.trust_matrix:
                if agent_id in self.trust_matrix[other]:
                    del self.trust_matrix[other][agent_id]
    
    def update_cohesion(self):
        """更新同盟凝聚力"""
        if len(self.members) < 2:
            self.cohesion = 0.0
            return
        
        total_trust = 0.0
        count = 0
        for a in self.members:
            for b in self.members:
                if a != b and b in self.trust_matrix.get(a, {}):
                    total_trust += self.trust_matrix[a][b]
                    count += 1
        
        self.cohesion = total_trust / count if count > 0 else 0.0
        
        # 凝聚力过低则同盟紧张
        if self.cohesion < 0.3:
            self.status = AllianceStatus.STRAINED
        elif self.cohesion < 0.1:
            self.status = AllianceStatus.DISSOLVED
    
    def get_collective_power(self, agent_powers: Dict[str, float]) -> float:
        """计算同盟集体实力"""
        return sum(agent_powers.get(m, 0.0) for m in self.members)
    
    def to_dict(self) -> Dict:
        return {
            "alliance_id": self.alliance_id,
            "name": self.name,
            "type": self.alliance_type.value,
            "members": list(self.members),
            "leader": self.leader,
            "formed_round": self.formed_round,
            "status": self.status.value,
            "cohesion": self.cohesion,
            "mutual_defense": self.mutual_defense,
            "collective_action": self.collective_action,
        }


class AllianceSystem:
    """联盟系统"""
    
    def __init__(self):
        self.alliances: Dict[str, Alliance] = {}
        self.agent_alliances: Dict[str, Set[str]] = defaultdict(set)
        self.alliance_counter = 0
        
        # 配置参数
        self.min_trust_for_alliance = 0.05      # 结盟最低信任度 (从0.15降至0.05促进同盟形成)
        self.max_alliances_per_agent = 3       # 每个 agent 最多同盟数
        self.cohesion_decay = 0.02             # 每轮凝聚力衰减
        self.betrayal_penalty = -0.5           # 背叛惩罚
    
    def propose_alliance(self, proposer: str, targets: List[str], 
                        alliance_type: AllianceType,
                        agent_trust_levels: Dict[str, Dict[str, float]],
                        round_num: int) -> Optional[Alliance]:
        """提议建立同盟"""
        
        # 检查是否已有过多同盟
        if len(self.agent_alliances.get(proposer, set())) >= self.max_alliances_per_agent:
            return None
        
        # 检查信任度
        valid_targets = []
        for target in targets:
            if target == proposer:
                continue
            trust = agent_trust_levels.get(proposer, {}).get(target, 0.0)
            if trust >= self.min_trust_for_alliance:
                valid_targets.append(target)
        
        if not valid_targets:
            return None
        
        # 创建同盟
        self.alliance_counter += 1
        alliance_id = f"alliance_{self.alliance_counter}"
        
        type_names = {
            AllianceType.DEFENSIVE: "防御同盟",
            AllianceType.OFFENSIVE: "进攻同盟", 
            AllianceType.ECONOMIC: "经济同盟",
            AllianceType.INTELLIGENCE: "情报同盟",
            AllianceType.MULTI: "综合同盟"
        }
        
        alliance = Alliance(
            alliance_id=alliance_id,
            name=f"{type_names.get(alliance_type, '同盟')}-{self.alliance_counter}",
            alliance_type=alliance_type,
            leader=proposer,
            formed_round=round_num,
            status=AllianceStatus.ACTIVE,
        )
        
        # 设置同盟特性
        if alliance_type == AllianceType.DEFENSIVE:
            alliance.mutual_defense = True
            alliance.collective_action = False
        elif alliance_type == AllianceType.OFFENSIVE:
            alliance.mutual_defense = True
            alliance.collective_action = True
        elif alliance_type == AllianceType.ECONOMIC:
            alliance.trade_bonus = 0.2
            alliance.collective_action = True
        elif alliance_type == AllianceType.INTELLIGENCE:
            alliance.intel_sharing = True
        elif alliance_type == AllianceType.MULTI:
            alliance.mutual_defense = True
            alliance.collective_action = True
            alliance.trade_bonus = 0.1
            alliance.intel_sharing = True
        
        # 添加成员
        alliance.add_member(proposer, 1.0)
        for target in valid_targets:
            trust = agent_trust_levels.get(proposer, {}).get(target, 0.5)
            alliance.add_member(target, trust)
            self.agent_alliances[target].add(alliance_id)
        
        self.agent_alliances[proposer].add(alliance_id)
        self.alliances[alliance_id] = alliance
        
        return alliance
    
    def dissolve_alliance(self, alliance_id: str, reason: str = ""):
        """解散同盟"""
        if alliance_id not in self.alliances:
            return
        
        alliance = self.alliances[alliance_id]
        alliance.status = AllianceStatus.DISSOLVED
        
        for member in alliance.members:
            if alliance_id in self.agent_alliances.get(member, set()):
                self.agent_alliances[member].remove(alliance_id)
        
        alliance.history.append({
            "event": "dissolved",
            "reason": reason,
            "round": alliance.formed_round,
        })
    
    def check_collective_defense(self, attacked_agent: str, 
                                  attacker: str) -> List[str]:
        """检查哪些同盟成员应参与集体防御"""
        defenders = []
        
        for alliance_id in self.agent_alliances.get(attacked_agent, set()):
            alliance = self.alliances.get(alliance_id)
            if not alliance or alliance.status != AllianceStatus.ACTIVE:
                continue
            
            if alliance.mutual_defense and attacker not in alliance.members:
                # 集体防御触发
                for member in alliance.members:
                    if member != attacked_agent:
                        defenders.append(member)
        
        return defenders
    
    def get_alliance_actions(self, alliance_id: str, 
                            action_type: str) -> Dict[str, any]:
        """获取同盟集体行动"""
        alliance = self.alliances.get(alliance_id)
        if not alliance or alliance.status != AllianceStatus.ACTIVE:
            return {}
        
        if not alliance.collective_action:
            return {"status": "no_collective_action"}
        
        if action_type == "sanction":
            # 集体制裁
            return {
                "status": "collective_sanction",
                "members": list(alliance.members),
                "sanction_power": len(alliance.members) * alliance.cohesion,
            }
        
        elif action_type == "attack":
            # 集体攻击
            return {
                "status": "collective_attack",
                "members": list(alliance.members),
                "attack_power": len(alliance.members) * alliance.cohesion * 1.5,
            }
        
        return {"status": "unknown_action"}
    
    def update_alliances(self, agent_trust_levels: Dict[str, Dict[str, float]],
                        round_num: int):
        """每轮更新同盟状态"""
        for alliance in list(self.alliances.values()):
            if alliance.status == AllianceStatus.DISSOLVED:
                continue
            
            # 更新信任矩阵
            for a in alliance.members:
                for b in alliance.members:
                    if a != b:
                        trust = agent_trust_levels.get(a, {}).get(b, 0.0)
                        if a in alliance.trust_matrix and b in alliance.trust_matrix[a]:
                            alliance.trust_matrix[a][b] = trust
            
            # 更新凝聚力
            alliance.update_cohesion()
            
            # 凝聚力衰减
            alliance.cohesion = max(0.0, alliance.cohesion - self.cohesion_decay)
            
            # 检查是否解散
            if alliance.cohesion < 0.1 or len(alliance.members) < 2:
                self.dissolve_alliance(alliance.alliance_id, "cohesion_too_low")
    
    def get_agent_alliance_context(self, agent_id: str) -> Dict:
        """获取 agent 的同盟上下文"""
        context = {
            "member_of": [],
            "can_propose_to": [],
            "collective_defenders": [],
        }
        
        for alliance_id in self.agent_alliances.get(agent_id, set()):
            alliance = self.alliances.get(alliance_id)
            if alliance and alliance.status == AllianceStatus.ACTIVE:
                context["member_of"].append(alliance.to_dict())
                
                if alliance.mutual_defense:
                    allies = [m for m in alliance.members if m != agent_id]
                    context["collective_defenders"].extend(allies)
        
        return context
    
    def get_summary(self) -> Dict:
        """获取联盟系统摘要"""
        active = sum(1 for a in self.alliances.values() 
                     if a.status == AllianceStatus.ACTIVE)
        dissolved = sum(1 for a in self.alliances.values() 
                        if a.status == AllianceStatus.DISSOLVED)
        
        return {
            "total_alliances": len(self.alliances),
            "active": active,
            "dissolved": dissolved,
            "alliances": [a.to_dict() for a in self.alliances.values() 
                         if a.status == AllianceStatus.ACTIVE],
        }


# 使用示例
if __name__ == "__main__":
    system = AllianceSystem()
    
    # 模拟信任度
    trust_levels = {
        "usa": {"uk": 0.8, "france": 0.7, "germany": 0.6, "china": -0.5},
        "uk": {"usa": 0.8, "france": 0.6, "germany": 0.5},
        "france": {"usa": 0.7, "uk": 0.6, "germany": 0.7},
        "germany": {"usa": 0.6, "uk": 0.5, "france": 0.7},
        "china": {"usa": -0.5, "russia": 0.4},
        "russia": {"china": 0.4, "usa": -0.6},
    }
    
    # USA 提议防御同盟
    alliance = system.propose_alliance(
        "usa", ["uk", "france", "germany"],
        AllianceType.DEFENSIVE,
        trust_levels,
        round_num=1
    )
    
    if alliance:
        print(f"同盟建立: {alliance.name}")
        print(f"成员: {alliance.members}")
        print(f"凝聚力: {alliance.cohesion:.2f}")
        
        # 检查集体防御
        defenders = system.check_collective_defense("uk", "russia")
        print(f"若 UK 被 Russia 攻击，集体防御者: {defenders}")
    
    print(f"\n系统摘要: {system.get_summary()}")
