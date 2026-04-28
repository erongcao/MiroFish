"""
Sanction Network - 经济制裁网络
多边制裁、制裁效果追踪、反制裁机制
"""

import random
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict

class SanctionType(Enum):
    TRADE = "trade"              # 贸易制裁
    FINANCIAL = "financial"      # 金融制裁
    TECHNOLOGY = "technology"    # 技术制裁
    TRAVEL = "travel"            # 旅行/签证制裁
    ARMS = "arms"                # 武器禁运
    COMPREHENSIVE = "comprehensive" # 全面制裁

class SanctionSeverity(Enum):
    LIGHT = 1.0        # 轻度 - 象征性
    MODERATE = 2.0     # 中度 - 实际影响
    SEVERE = 4.0       # 重度 - 重大经济影响
    TOTAL = 8.0        # 全面 - 经济封锁

@dataclass
class Sanction:
    sanction_id: str
    target: str                        # 被制裁方
    imposers: Set[str] = field(default_factory=set)  # 制裁实施方
    sanction_type: SanctionType = SanctionType.TRADE
    severity: SanctionSeverity = SanctionSeverity.MODERATE
    imposed_round: int = 0
    duration: int = 10                 # 预计持续轮数
    
    # 动态效果
    economic_impact: float = 0.0     # 经济影响 (-1 到 0)
    effectiveness: float = 1.0         # 有效性 (0-1)
    
    # 反制裁
    counter_sanctions: Set[str] = field(default_factory=set)
    
    def calculate_impact(self, target_economy: float, 
                        imposer_collective_power: float) -> float:
        """计算制裁实际经济影响"""
        base_impact = -self.severity.value * 0.05
        
        # 实施方实力加成
        power_ratio = min(1.0, imposer_collective_power / (target_economy + 1.0))
        
        # 多边形加成
        multilateral_bonus = 1.0 + (len(self.imposers) - 1) * 0.2
        
        impact = base_impact * power_ratio * multilateral_bonus * self.effectiveness
        return max(-0.5, impact)  # 最大影响 -50%
    
    def to_dict(self) -> Dict:
        return {
            "sanction_id": self.sanction_id,
            "target": self.target,
            "imposers": list(self.imposers),
            "type": self.sanction_type.value,
            "severity": self.severity.name,
            "economic_impact": self.economic_impact,
            "effectiveness": self.effectiveness,
            "duration": self.duration,
        }


class SanctionNetwork:
    """制裁网络系统"""
    
    def __init__(self):
        self.sanctions: Dict[str, Sanction] = {}
        self.agent_sanctions: Dict[str, Set[str]] = defaultdict(set)  # agent -> 对其的制裁
        self.imposed_sanctions: Dict[str, Set[str]] = defaultdict(set)  # agent -> 其实施的制裁
        self.sanction_counter = 0
        
        # 配置
        self.decay_rate = 0.05           # 制裁效果衰减率
        self.resistance_factor = 0.3     # 被制裁方抵抗力
        self.escalation_threshold = -0.3  # 升级制裁的阈值
    
    def impose_sanction(self, imposers: List[str], target: str,
                       sanction_type: SanctionType,
                       severity: SanctionSeverity,
                       agent_economies: Dict[str, float],
                       round_num: int) -> Optional[Sanction]:
        """实施制裁"""
        
        if not imposers or not target:
            return None
        
        self.sanction_counter += 1
        sanction_id = f"sanction_{self.sanction_counter}"
        
        sanction = Sanction(
            sanction_id=sanction_id,
            target=target,
            imposers=set(imposers),
            sanction_type=sanction_type,
            severity=severity,
            imposed_round=round_num,
        )
        
        # 计算集体实力
        collective_power = sum(agent_economies.get(i, 0.0) for i in imposers)
        target_economy = agent_economies.get(target, 100.0)
        
        # 计算实际影响
        sanction.economic_impact = sanction.calculate_impact(
            target_economy, collective_power
        )
        
        # 有效性随机因素
        sanction.effectiveness = random.uniform(0.6, 1.0)
        
        # 记录
        self.sanctions[sanction_id] = sanction
        self.agent_sanctions[target].add(sanction_id)
        for imposer in imposers:
            self.imposed_sanctions[imposer].add(sanction_id)
        
        return sanction
    
    def add_counter_sanction(self, original_sanction_id: str, 
                            counter_imposer: str,
                            agent_economies: Dict[str, float],
                            round_num: int) -> Optional[Sanction]:
        """添加反制裁"""
        original = self.sanctions.get(original_sanction_id)
        if not original:
            return None
        
        # 反制裁针对原制裁方之一
        target = random.choice(list(original.imposers))
        
        counter = self.impose_sanction(
            [counter_imposer], target,
            SanctionType.TRADE,
            SanctionSeverity.LIGHT,
            agent_economies,
            round_num
        )
        
        if counter:
            original.counter_sanctions.add(counter.sanction_id)
            counter.sanction_id = f"counter_{counter.sanction_id}"
        
        return counter
    
    def update_sanctions(self, agent_economies: Dict[str, float],
                        round_num: int):
        """每轮更新制裁效果"""
        for sanction in list(self.sanctions.values()):
            # 效果衰减
            sanction.effectiveness = max(0.0, 
                sanction.effectiveness - self.decay_rate)
            
            # 被制裁方适应
            resistance = self.resistance_factor * (1 + random.uniform(-0.2, 0.2))
            sanction.economic_impact = min(0.0, 
                sanction.economic_impact + resistance * 0.01)
            
            # 检查是否到期
            if round_num - sanction.imposed_round >= sanction.duration:
                sanction.effectiveness = 0.0
    
    def get_total_impact(self, agent_id: str) -> float:
        """获取 agent 承受的总制裁影响"""
        total_impact = 0.0
        
        for sanction_id in self.agent_sanctions.get(agent_id, set()):
            sanction = self.sanctions.get(sanction_id)
            if sanction and sanction.effectiveness > 0:
                total_impact += sanction.economic_impact * sanction.effectiveness
        
        return total_impact
    
    def get_sanction_context(self, agent_id: str) -> Dict:
        """获取制裁上下文"""
        imposed_on_me = []
        my_sanctions = []
        
        for sanction_id in self.agent_sanctions.get(agent_id, set()):
            sanction = self.sanctions.get(sanction_id)
            if sanction:
                imposed_on_me.append(sanction.to_dict())
        
        for sanction_id in self.imposed_sanctions.get(agent_id, set()):
            sanction = self.sanctions.get(sanction_id)
            if sanction:
                my_sanctions.append(sanction.to_dict())
        
        return {
            "under_sanctions": imposed_on_me,
            "imposed_sanctions": my_sanctions,
            "total_impact": self.get_total_impact(agent_id),
        }
    
    def get_multilateral_sanction_power(self, target: str) -> float:
        """计算对某目标的多边制裁实力"""
        total = 0.0
        
        for sanction_id in self.agent_sanctions.get(target, set()):
            sanction = self.sanctions.get(sanction_id)
            if sanction:
                total += len(sanction.imposers) * sanction.severity.value
        
        return total
    
    def should_escalate(self, agent_id: str) -> bool:
        """判断是否应该升级制裁"""
        impact = self.get_total_impact(agent_id)
        return impact < self.escalation_threshold
    
    def get_summary(self) -> Dict:
        """获取制裁网络摘要"""
        active_sanctions = [s for s in self.sanctions.values() 
                           if s.effectiveness > 0]
        
        return {
            "total_sanctions": len(self.sanctions),
            "active": len(active_sanctions),
            "by_type": {
                t.value: sum(1 for s in active_sanctions if s.sanction_type == t)
                for t in SanctionType
            },
            "most_sanctioned": sorted(
                self.agent_sanctions.keys(),
                key=lambda a: len(self.agent_sanctions[a]),
                reverse=True
            )[:5],
        }


# 使用示例
if __name__ == "__main__":
    network = SanctionNetwork()
    
    economies = {
        "usa": 200.0, "eu": 180.0, "china": 150.0,
        "russia": 80.0, "iran": 30.0, "nk": 10.0,
    }
    
    # 多边制裁 Russia
    sanction = network.impose_sanction(
        ["usa", "eu"], "russia",
        SanctionType.COMPREHENSIVE,
        SanctionSeverity.SEVERE,
        economies,
        round_num=1
    )
    
    if sanction:
        print(f"制裁实施: {sanction.sanction_id}")
        print(f"目标: {sanction.target}")
        print(f"实施方: {sanction.imposers}")
        print(f"经济影响: {sanction.economic_impact:.2%}")
        print(f"有效性: {sanction.effectiveness:.2f}")
        
        # Russia 反制裁
        counter = network.add_counter_sanction(
            sanction.sanction_id, "russia", economies, round_num=1
        )
        if counter:
            print(f"\n反制裁: {counter.sanction_id}")
            print(f"反制裁目标: {counter.target}")
    
    print(f"\n制裁摘要: {network.get_summary()}")
    print(f"Russia 总影响: {network.get_total_impact('russia'):.2%}")
