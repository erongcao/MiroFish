"""
Third Party Mediation - 第三方调解系统
联合国/欧盟/中立国介入调解冲突
"""

import random
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

class MediatorType(Enum):
    UN = "un"                    # 联合国
    REGIONAL = "regional"        # 区域组织（欧盟、东盟等）
    NEUTRAL = "neutral"          # 中立国家
    GREAT_POWER = "great_power"  # 大国调解
    NGO = "ngo"                  # 非政府组织

class MediationOutcome(Enum):
    SUCCESS = "success"          # 成功调解
    PARTIAL = "partial"          # 部分成功
    FAILED = "failed"            # 失败
    REJECTED = "rejected"        # 被拒绝

@dataclass
class MediationAttempt:
    attempt_id: str
    mediator: str
    mediator_type: MediatorType
    parties: Set[str] = field(default_factory=set)
    conflict_level: str = "crisis"
    proposed_round: int = 0
    
    # 调解参数
    mediator_credibility: float = 0.5
    mediator_power: float = 0.5
    
    # 结果
    outcome: MediationOutcome = MediationOutcome.FAILED
    trust_restored: float = 0.0
    deescalation: int = 0          # 降级层级数
    
    def calculate_success_probability(self, 
                                     party_trust_levels: Dict[str, float]) -> float:
        """计算调解成功概率"""
        base_prob = 0.3
        
        # 调解者信誉加成
        credibility_bonus = self.mediator_credibility * 0.3
        
        # 实力加成（大国调解更有效）
        power_bonus = self.mediator_power * 0.2
        
        # 冲突级别惩罚（级别越高越难调解）
        level_penalty = {
            "peace": 0.0,
            "tension": 0.0,
            "crisis": -0.1,
            "sanctions": -0.2,
            "proxy_war": -0.3,
            "limited_war": -0.4,
            "total_war": -0.5,
        }.get(self.conflict_level, -0.2)
        
        # 双方意愿（取最低意愿）
        willingness = min(
            party_trust_levels.get(p, 0.0) for p in self.parties
        ) + 0.5
        
        prob = base_prob + credibility_bonus + power_bonus + level_penalty + willingness * 0.3
        return max(0.05, min(0.9, prob))
    
    def to_dict(self) -> Dict:
        return {
            "attempt_id": self.attempt_id,
            "mediator": self.mediator,
            "mediator_type": self.mediator_type.value,
            "parties": list(self.parties),
            "outcome": self.outcome.value,
            "trust_restored": self.trust_restored,
            "deescalation": self.deescalation,
        }


class ThirdPartyMediation:
    """第三方调解系统"""
    
    def __init__(self):
        self.mediators: Dict[str, Dict] = {}
        self.mediation_history: List[MediationAttempt] = []
        self.attempt_counter = 0
        
        # 配置
        self.mediation_cooldown = 5      # 调解冷却轮数
        self.min_conflict_level = "crisis"  # 最低冲突级别才调解
        self.last_mediation_round: Dict[str, int] = {}
    
    def register_mediator(self, agent_id: str, mediator_type: MediatorType,
                         credibility: float = 0.5, power: float = 0.5,
                         region: Optional[str] = None):
        """注册调解者"""
        self.mediators[agent_id] = {
            "agent_id": agent_id,
            "type": mediator_type,
            "credibility": credibility,
            "power": power,
            "region": region,
            "successful_mediations": 0,
            "failed_mediations": 0,
        }
    
    def attempt_mediation(self, mediator_id: str, 
                         parties: List[str],
                         conflict_level: str,
                         party_trust_levels: Dict[str, float],
                         round_num: int) -> Optional[MediationAttempt]:
        """尝试调解"""
        
        mediator = self.mediators.get(mediator_id)
        if not mediator:
            return None
        
        # 检查冷却
        last_round = self.last_mediation_round.get(mediator_id, 0)
        if round_num - last_round < self.mediation_cooldown:
            return None
        
        # 检查冲突级别
        level_order = ["peace", "tension", "crisis", "sanctions", 
                      "proxy_war", "limited_war", "total_war"]
        min_idx = level_order.index(self.min_conflict_level)
        current_idx = level_order.index(conflict_level) if conflict_level in level_order else 999
        
        if current_idx < min_idx:
            return None
        
        self.attempt_counter += 1
        attempt = MediationAttempt(
            attempt_id=f"med_{self.attempt_counter}",
            mediator=mediator_id,
            mediator_type=mediator["type"],
            parties=set(parties),
            conflict_level=conflict_level,
            proposed_round=round_num,
            mediator_credibility=mediator["credibility"],
            mediator_power=mediator["power"],
        )
        
        # 计算成功概率
        success_prob = attempt.calculate_success_probability(party_trust_levels)
        
        # 判定结果
        roll = random.random()
        if roll < success_prob * 0.3:
            attempt.outcome = MediationOutcome.SUCCESS
            attempt.trust_restored = random.uniform(0.3, 0.6)
            attempt.deescalation = random.randint(2, 3)
            mediator["successful_mediations"] += 1
        elif roll < success_prob * 0.7:
            attempt.outcome = MediationOutcome.PARTIAL
            attempt.trust_restored = random.uniform(0.1, 0.3)
            attempt.deescalation = random.randint(1, 2)
            mediator["successful_mediations"] += 1
        elif roll < success_prob * 1.2:
            attempt.outcome = MediationOutcome.FAILED
            mediator["failed_mediations"] += 1
        else:
            attempt.outcome = MediationOutcome.REJECTED
            mediator["failed_mediations"] += 1
        
        self.mediation_history.append(attempt)
        self.last_mediation_round[mediator_id] = round_num
        
        return attempt
    
    def find_best_mediator(self, parties: List[str], 
                          conflict_level: str,
                          round_num: int) -> Optional[str]:
        """寻找最佳调解者"""
        candidates = []
        
        for mediator_id, mediator in self.mediators.items():
            # 检查冷却
            last_round = self.last_mediation_round.get(mediator_id, 0)
            if round_num - last_round < self.mediation_cooldown:
                continue
            
            # 检查是否是冲突方
            if mediator_id in parties:
                continue
            
            # 计算适合度
            credibility = mediator["credibility"]
            power = mediator["power"]
            success_rate = (
                mediator["successful_mediations"] / 
                max(1, mediator["successful_mediations"] + mediator["failed_mediations"])
            )
            
            fitness = credibility * 0.3 + power * 0.3 + success_rate * 0.4
            candidates.append((mediator_id, fitness))
        
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def get_mediation_context(self, agent_id: str) -> Dict:
        """获取调解上下文"""
        mediator_info = self.mediators.get(agent_id, {})
        
        related_attempts = [
            a for a in self.mediation_history
            if agent_id in a.parties or agent_id == a.mediator
        ]
        
        return {
            "is_mediator": agent_id in self.mediators,
            "mediator_stats": mediator_info,
            "related_attempts": [a.to_dict() for a in related_attempts[-5:]],
        }
    
    def get_summary(self) -> Dict:
        """获取调解系统摘要"""
        outcomes = defaultdict(int)
        for attempt in self.mediation_history:
            outcomes[attempt.outcome.value] += 1
        
        return {
            "total_attempts": len(self.mediation_history),
            "outcomes": dict(outcomes),
            "mediators": len(self.mediators),
            "success_rate": (
                outcomes["success"] / len(self.mediation_history)
                if self.mediation_history else 0
            ),
        }


# 使用示例
if __name__ == "__main__":
    mediation = ThirdPartyMediation()
    
    # 注册调解者
    mediation.register_mediator("un", MediatorType.UN, 
                               credibility=0.8, power=0.6)
    mediation.register_mediator("eu", MediatorType.REGIONAL, 
                               credibility=0.7, power=0.5, region="europe")
    mediation.register_mediator("switzerland", MediatorType.NEUTRAL, 
                               credibility=0.9, power=0.2)
    
    # 模拟冲突双方信任度
    trust_levels = {
        "usa": -0.3, "china": -0.4,
    }
    
    # 联合国调解中美危机
    attempt = mediation.attempt_mediation(
        "un", ["usa", "china"], "crisis",
        trust_levels, round_num=1
    )
    
    if attempt:
        print(f"调解尝试: {attempt.attempt_id}")
        print(f"调解者: {attempt.mediator}")
        print(f"结果: {attempt.outcome.value}")
        print(f"信任恢复: {attempt.trust_restored:.2f}")
        print(f"降级: {attempt.deescalation} 级")
    
    print(f"\n调解摘要: {mediation.get_summary()}")
