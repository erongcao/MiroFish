"""
Nuclear Deterrence - 核威慑机制
特殊威慑逻辑、相互确保毁灭、核门槛
"""

import random
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

class NuclearStatus(Enum):
    NONE = "none"                # 无核武器
    EMERGING = "emerging"        # 新兴核国家
    ESTABLISHED = "established" #  established核国家
    SUPERPOWER = "superpower"    # 超级核大国

class DeterrencePosture(Enum):
    MINIMUM = "minimum"          # 最低威慑
    LIMITED = "limited"          # 有限威慑
    FULL = "full"                # 全面威慑
    FIRST_STRIKE = "first_strike" # 先发制人

@dataclass
class NuclearArsenal:
    warheads: int = 0
    delivery_systems: int = 0
    second_strike_capability: bool = False
    missile_defense: float = 0.0    # 导弹防御效率
    
    def calculate_deterrence_power(self) -> float:
        """计算威慑力量"""
        if self.warheads == 0:
            return 0.0
        
        base = np.log1p(self.warheads) * 10
        second_strike_bonus = 20 if self.second_strike_capability else 0
        delivery_bonus = np.log1p(self.delivery_systems) * 5
        
        return base + second_strike_bonus + delivery_bonus
    
    def calculate_assured_destruction(self, target_arsenal: 'NuclearArsenal') -> float:
        """计算确保相互毁灭概率"""
        if self.warheads == 0 or target_arsenal.warheads == 0:
            return 0.0
        
        # 生存能力
        survivability = 0.3 if self.second_strike_capability else 0.05
        
        # 突破防御概率
        penetration = max(0.1, 1.0 - target_arsenal.missile_defense)
        
        # 毁灭能力
        destructive_power = min(1.0, self.warheads / 100)
        
        mad_prob = survivability * penetration * destructive_power
        return min(0.99, mad_prob)


class NuclearDeterrence:
    """核威慑系统"""
    
    def __init__(self):
        self.arsenals: Dict[str, NuclearArsenal] = {}
        self.statuses: Dict[str, NuclearStatus] = {}
        self.postures: Dict[str, DeterrencePosture] = {}
        
        # 配置
        self.nuclear_threshold = "limited_war"  # 核门槛
        self.no_first_use: Set[str] = set()     # 承诺不首先使用
        self.escalation_control = 0.8           # 升级控制系数
    
    def register_nuclear_power(self, agent_id: str, 
                               warheads: int, 
                               delivery_systems: int,
                               second_strike: bool = False,
                               missile_defense: float = 0.0,
                               no_first_use: bool = False):
        """注册核国家"""
        self.arsenals[agent_id] = NuclearArsenal(
            warheads=warheads,
            delivery_systems=delivery_systems,
            second_strike_capability=second_strike,
            missile_defense=missile_defense,
        )
        
        # 确定核地位
        if warheads > 5000:
            self.statuses[agent_id] = NuclearStatus.SUPERPOWER
            self.postures[agent_id] = DeterrencePosture.FULL
        elif warheads > 500:
            self.statuses[agent_id] = NuclearStatus.ESTABLISHED
            self.postures[agent_id] = DeterrencePosture.FULL
        elif warheads > 50:
            self.statuses[agent_id] = NuclearStatus.EMERGING
            self.postures[agent_id] = DeterrencePosture.LIMITED
        else:
            self.statuses[agent_id] = NuclearStatus.NONE
            self.postures[agent_id] = DeterrencePosture.MINIMUM
        
        if no_first_use:
            self.no_first_use.add(agent_id)
    
    def check_nuclear_escalation(self, attacker: str, defender: str,
                                  conflict_level: str) -> Dict:
        """检查是否触发核升级"""
        
        # 检查双方是否有核武器
        attacker_arsenal = self.arsenals.get(attacker)
        defender_arsenal = self.arsenals.get(defender)
        
        if not attacker_arsenal and not defender_arsenal:
            return {"nuclear_escalation": False, "reason": "no_nuclear_powers"}
        
        # 检查冲突级别是否达到核门槛
        level_order = ["peace", "tension", "crisis", "sanctions", 
                      "proxy_war", "limited_war", "total_war"]
        threshold_idx = level_order.index(self.nuclear_threshold)
        current_idx = level_order.index(conflict_level) if conflict_level in level_order else 0
        
        if current_idx < threshold_idx:
            return {"nuclear_escalation": False, "reason": "below_threshold"}
        
        result = {
            "nuclear_escalation": True,
            "attacker_has_nukes": attacker_arsenal is not None,
            "defender_has_nukes": defender_arsenal is not None,
        }
        
        # 计算威慑效果
        if defender_arsenal and defender_arsenal.warheads > 0:
            mad_prob = defender_arsenal.calculate_assured_destruction(
                attacker_arsenal or NuclearArsenal()
            )
            
            # 威慑是否有效
            deterrence_effective = mad_prob > 0.5
            
            # 攻击者是否承诺不首先使用
            attacker_no_first = attacker in self.no_first_use
            
            result.update({
                "mad_probability": mad_prob,
                "deterrence_effective": deterrence_effective,
                "attacker_no_first_use": attacker_no_first,
                "defender_second_strike": defender_arsenal.second_strike_capability,
            })
            
            if deterrence_effective and not attacker_no_first:
                result["decision"] = "deterred"
                result["reason"] = "mutual_assured_destruction"
            elif attacker_no_first:
                result["decision"] = "no_first_use_constraint"
            else:
                result["decision"] = "risk_accepted"
        
        return result
    
    def simulate_nuclear_exchange(self, attacker: str, defender: str) -> Dict:
        """模拟核交换"""
        attacker_arsenal = self.arsenals.get(attacker)
        defender_arsenal = self.arsenals.get(defender)
        
        if not attacker_arsenal:
            return {"error": "attacker_has_no_nukes"}
        
        # 第一波打击
        first_strike = min(attacker_arsenal.warheads * 0.3, 100)
        
        # 防御方反击
        if defender_arsenal and defender_arsenal.second_strike_capability:
            penetration = max(0.1, 1.0 - attacker_arsenal.missile_defense)
            second_strike = min(defender_arsenal.warheads * 0.2 * penetration, 50)
        else:
            second_strike = 0
        
        # 伤亡估算（简化）
        casualties_attacker = second_strike * 0.5  # 百万人
        casualties_defender = first_strike * 0.5
        
        return {
            "first_strike_warheads": first_strike,
            "second_strike_warheads": second_strike,
            "estimated_casualties_attacker": casualties_attacker,
            "estimated_casualties_defender": casualties_defender,
            "total_warheads_used": first_strike + second_strike,
            "outcome": "catastrophic" if (casualties_attacker + casualties_defender) > 10 else "severe",
        }
    
    def get_nuclear_context(self, agent_id: str) -> Dict:
        """获取核威慑上下文"""
        arsenal = self.arsenals.get(agent_id)
        status = self.statuses.get(agent_id, NuclearStatus.NONE)
        posture = self.postures.get(agent_id, DeterrencePosture.MINIMUM)
        
        if not arsenal:
            return {"has_nukes": False}
        
        return {
            "has_nukes": True,
            "status": status.value,
            "posture": posture.value,
            "warheads": arsenal.warheads,
            "delivery_systems": arsenal.delivery_systems,
            "second_strike": arsenal.second_strike_capability,
            "deterrence_power": arsenal.calculate_deterrence_power(),
            "no_first_use": agent_id in self.no_first_use,
        }
    
    def get_standoff_summary(self, agent_a: str, agent_b: str) -> Dict:
        """获取核对峙摘要"""
        a_arsenal = self.arsenals.get(agent_a)
        b_arsenal = self.arsenals.get(agent_b)
        
        if not a_arsenal and not b_arsenal:
            return {"nuclear_standoff": False}
        
        mad_prob = 0.0
        if a_arsenal and b_arsenal:
            mad_prob = a_arsenal.calculate_assured_destruction(b_arsenal)
        
        return {
            "nuclear_standoff": True,
            "agent_a_nukes": a_arsenal.warheads if a_arsenal else 0,
            "agent_b_nukes": b_arsenal.warheads if b_arsenal else 0,
            "mad_probability": mad_prob,
            "deterrence_stable": mad_prob > 0.5,
        }


# 使用示例
if __name__ == "__main__":
    nd = NuclearDeterrence()
    
    # 注册核大国
    nd.register_nuclear_power("usa", 5800, 800, 
                             second_strike=True, missile_defense=0.3)
    nd.register_nuclear_power("russia", 6500, 600, 
                             second_strike=True, missile_defense=0.2)
    nd.register_nuclear_power("china", 350, 200, 
                             second_strike=True, no_first_use=True)
    
    # 检查 USA vs Russia 全面战争是否触发核升级
    result = nd.check_nuclear_escalation("usa", "russia", "total_war")
    print("USA vs Russia 核升级分析:")
    print(f"  触发核升级: {result['nuclear_escalation']}")
    print(f"  威慑有效: {result.get('deterrence_effective', False)}")
    print(f"  MAD概率: {result.get('mad_probability', 0):.2%}")
    print(f"  决策: {result.get('decision', 'N/A')}")
    
    # 核对峙摘要
    standoff = nd.get_standoff_summary("usa", "russia")
    print(f"\n核对峙: {standoff}")
